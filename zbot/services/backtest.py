# coding=utf-8
import warnings
import os
import re
import importlib
# from backtesting import Backtest as BacktestBase
import pandas as pd
from backtesting.lib import crossover, FractionalBacktest as BacktestBase
from zbot.services.model import get_candles_from_db
from zbot.utils.dateutils import timestamp_to_datetime, format_datetime
from zbot.common.config import read_config
from zbot.models.backtest import BacktestRecord
import json
import logging
from datetime import datetime
import os
from zbot.utils.dateutils import timedelta_to_localized_string

# 配置日志
logger = logging.getLogger(__name__)

# 策略目录路径
strategies_dir = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '../strategies')

# 查找策略目录下全部策略


def get_strategy_names():
    # 查找所有策略文件
    strategy_files = [f for f in os.listdir(
        strategies_dir) if f.endswith('.py')]

    return strategy_files


def get_strategy_class_names():
    """
    查找策略目录下的策略文件中的策略类名
    :return: 包含所有策略类名的列表
    """
    # 查找策略目录下的策略文件中的策略类名
    class_names = []
    strategy_names = get_strategy_names()
    for filename in strategy_names:
        # 读取文件内容查找类定义
        with open(os.path.join(strategies_dir, filename), 'r', encoding='utf-8') as f:
            content = f.read()

            # 使用正则表达式匹配类定义
            class_matches = re.findall(r'class\s+(\w+)\s*\(', content)

            # 查找匹配的类
            for name in class_matches:
                class_names.append({'name': name, 'filename': filename})
    return class_names


def load_strategy_class(strategy_name, strategy_path=None):
    """
    根据策略名称动态加载strategies目录中的策略类
    :param strategy_name: 策略类名
    :return: 策略类
    """
    # 策略目录路径
    strategies_dir = strategy_path or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '../strategies')

    # 遍历目录下的所有Python文件
    for filename in os.listdir(strategies_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            # 模块名称
            module_name = f'zbot.strategies.{filename[:-3]}'

            # 导入模块
            module = importlib.import_module(module_name)

            # 读取文件内容查找类定义
            with open(os.path.join(strategies_dir, filename), 'r', encoding='utf-8') as f:
                content = f.read()

                # 使用正则表达式匹配类定义
                class_matches = re.findall(r'class\s+(\w+)\s*\(', content)

                # 查找匹配的类
                for class_name in class_matches:
                    if class_name == strategy_name:
                        return getattr(module, class_name)

    # 如果未找到策略类
    raise ValueError(f"未找到策略类: {strategy_name}")


# 自定义Backtest类
class CustomBacktest(BacktestBase):
    def __init__(self, *args, **kwargs):
        with warnings.catch_warnings(record=True):
            warnings.filterwarnings(action='ignore', message='frac')
            super().__init__(*args, **kwargs, fractional_unit=1e-06)


class Backtest(object):
    def __init__(self, strategy: str, symbol: str, interval: str, start: str, end: str, cash: float,
                 commission: float, exchange: str = None):
        self.strategy = strategy
        self.symbol = symbol
        self.interval = interval
        self.start = start
        self.end = end
        self.cash = cash
        self.commission = commission
        self.exchange = exchange or read_config('exchange')['name']

        # 指标含义映射关系
        self.translations = {
            # 基础指标
            'Start': {'cn': '起始时间', 'en': 'Start'},
            'End': {'cn': '结束时间', 'en': 'End'},
            'Duration': {'cn': '策略运行时间', 'en': 'Duration', 'desc': '反映策略回测的时间跨度。时间越长，策略的长期稳定性越能被验证。'},
            'Exposure Time [%]': {'cn': '持仓时间百分比', 'en': 'Exposure Time [%]', 'desc': '表示策略在回测期间平均持仓时间占比。高比例说明策略倾向于中长期持有，低比例可能为高频或短线策略。'},
            'Equity Final [$]': {'cn': '最终权益', 'en': 'Equity Final [$]', 'desc': '策略最终资产价值。'},
            'Equity Peak [$]': {'cn': '权益峰值', 'en': 'Equity Peak [$]', 'desc': '策略历史最高资产值。​​意义​​：反映策略的收益潜力与风险（如峰值后是否大幅回撤）。'},
            'Commissions [$]': {'cn': '手续费', 'en': 'Commissions [$]', 'desc': '策略交易中的手续费成本。'},
            # 收益与风险指标
            'Return [%]': {'cn': '总收益率', 'en': 'Return [%]', 'desc': '策略总收益率。需结合时间跨度评估（如年化收益是否合理）。'},
            'Return (Ann.) [%]': {'cn': '年化收益率', 'en': 'Return (Ann.) [%]', 'desc': '扣除时间后的年均收益。理想值应高于市场基准（如美股长期年化约7-10%）。'},
            'Buy & Hold Return [%]': {'cn': '买入持有收益率', 'en': 'Buy & Hold Return [%]', 'desc': '在回测期间不进行交易，仅用初始资金购买资产并持有至结束时间的收益率。用于比较策略的相对表现。'},
            'Volatility (Ann.) [%]': {'cn': '年化波动率', 'en': 'Volatility (Ann.) [%]', 'desc': '衡量收益的波动程度。高波动（>30%）通常伴随高风险。'},
            'CAGR [%]': {'cn': '复合年化增长率', 'en': 'CAGR [%]', 'desc': '剔除波动后的平滑收益，更真实反映长期增长能力。'},
            'Sharpe Ratio': {'cn': '夏普比率', 'en': 'Sharpe Ratio', 'desc': '衡量单位风险下的超额收益。>1为优秀，0.5-1为合理，<0.5需谨慎。'},
            'Sortino Ratio': {'cn': '索提诺比率', 'en': 'Sortino Ratio', 'desc': '仅考虑下行风险后的收益比。>1表明策略在熊市中抗跌能力较强。'},
            'Calmar Ratio': {'cn': '卡尔马比率', 'en': 'Calmar Ratio', 'desc': '收益与最大回撤的比值。>1表示策略回撤后能快速恢复，<1需警惕风险。'},
            # 策略性能指标​​
            'Alpha [%]': {'cn': '阿尔法系数', 'en': 'Alpha [%]', 'desc': '策略相对于基准（如市场指数）的超额收益。高Alpha表明策略有效。'},
            'Beta': {'cn': '贝塔系数', 'en': 'Beta', 'desc': '衡量策略收益与市场收益的相关性。>1表明策略收益与市场收益正相关，<1表明负相关。'},
            'Max. Drawdown [%]': {'cn': '最大回撤', 'en': 'Max. Drawdown [%]', 'desc': '策略从峰值到谷底的跌幅。>30%为高风险，需评估恢复能力。'},
            'Avg. Drawdown [%]': {'cn': '平均回撤', 'en': 'Avg. Drawdown [%]', 'desc': '策略历史最大回撤的平均值，反映策略的波动频率。'},
            'Profit Factor': {'cn': '利润因子', 'en': 'Profit Factor', 'desc': '盈利交易总收益与亏损交易总损失的比值。>1.5为稳健策略。'},
            'Win Rate [%]': {'cn': '胜率', 'en': 'Win Rate [%]', 'desc': '盈利交易占比。高频策略通常>50%，长线策略可能<50%。'},
            'Expectancy [%]': {'cn': '期望值', 'en': 'Expectancy [%]', 'desc': '单次交易的平均收益（胜率×平均盈利 - 败率×平均亏损）。'},
            # 交易行为指标​​
            '# Trades': {'cn': '交易次数', 'en': '# Trades', 'desc': '策略活跃度。高频策略可能达数千次，长线策略可能仅数次。'},
            'Win Rate [%]': {'cn': '胜率', 'en': 'Win Rate [%]', 'desc': '盈利交易占总交易的比例。'},
            'Best Trade [%]': {'cn': '最佳交易', 'en': 'Best Trade [%]', 'desc': '单笔交易的最大盈利百分比。'},
            'Worst Trade [%]': {'cn': '最差交易', 'en': 'Worst Trade [%]', 'desc': '单笔交易的最大亏损百分比。'},
            'Avg. Trade [%]': {'cn': '平均交易收益率', 'en': 'Avg. Trade [%]', 'desc': '所有交易的平均盈利百分比。'},
            'Max. Trade Duration': {'cn': '最大持仓时间​​', 'en': 'Max. Trade Duration', 'desc': '显示策略可能长期持有头寸，需关注资金占用和机会成本。'},
            'Avg. Trade Duration': {'cn': '平均持仓时间', 'en': 'Avg. Trade Duration', 'desc': '反映策略的中短期交易风格。'},
            'Total Trades': {'cn': '总交易次数', 'en': 'Total Trades', 'desc': '策略交易的总次数，反映策略的活跃度。'},
            'Max. Drawdown Duration': {'cn': '最大回撤时长', 'en': 'Max. Drawdown Duration', 'desc': '显示策略可能长期持有头寸，需关注资金占用和机会成本。'},
            'Avg. Drawdown Duration': {'cn': '平均回撤时长', 'en': 'Avg. Drawdown Duration', 'desc': '反映策略的风险承受能力。'},
            'SQN': {'cn': '系统质量数', 'en': 'SQN', 'desc': '衡量交易系统质量的综合指标，结合交易次数、盈亏比和稳定性。'},
            'Kelly Criterion': {'cn': '凯利准则', 'en': 'Kelly Criterion', 'desc': '优化资金分配比例，最大化长期收益。最大回撤限制​​：若策略历史最大回撤为 D%，建议凯利仓位不超过 D% / 最大回撤。夏普比率校准​​：若策略夏普比率 S < 1，建议凯利仓位减半'},
            # 可以根据实际输出结果添加更多映射
        }

    def to_dict(self, result):
        # 创建翻译后的结果字典
        translated_result = []
        for key, value in result.items():
            if key in ['_strategy', '_equity_curve', '_trade_list', '_trades']:
                continue
            # 如果键在翻译字典中存在，则使用中文键，否则保留原键
            translated_value = self.translations.get(key, key)
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, pd.Timedelta):
                value = timedelta_to_localized_string(value)
            translated_value['value'] = value
            translated_result.append(translated_value)
        return translated_result

    def run(self):
        candles = get_candles_from_db(
            self.exchange, self.symbol, self.interval, self.start, self.end)
        del candles['id']
        # 将open_time时间戳转换为时间字符串
        candles['open_time'] = candles['open_time'].apply(
            lambda x: timestamp_to_datetime(x))
        candles.rename(columns={'open': 'Open', 'close': 'Close',
                       'high': 'High', 'low': 'Low', 'volume': 'Volume'}, inplace=True)
        candles.set_index('open_time', drop=True, inplace=True)
        # 动态加载策略类
        strategy_class = load_strategy_class(self.strategy)
        self.bt = CustomBacktest(candles, strategy_class, cash=self.cash,
                                 commission=self.commission, exclusive_orders=True)
        self.stats = self.bt.run()
        # 获取交易记录
        trades = self.stats['_trades'].to_dict(orient='records')
        for trade in trades:
            for _k, _v in trade.items():
                if isinstance(_v, datetime):
                    trade[_k] = _v.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(_v, pd.Timedelta):
                    trade[_k] = timedelta_to_localized_string(_v)
            if trade.get('Size', 0) > 0:
                trade['Direction'] = '多单'
            else:
                trade['Direction'] = '空单'
        # 获取策略数据
        strategy_data = self.stats['_strategy'].data.df.to_dict(orient='records')

        # 收集回测记录数据并保存
        strategy_classes = get_strategy_class_names()
        file_name = next(
            (item['filename'] for item in strategy_classes if item['name'] == self.strategy), 'unknown.py')

        parameters = {
            'symbol': self.symbol,
            'interval': self.interval,
            'start': self.start,
            'end': self.end,
            'cash': self.cash,
            'commission': self.commission,
            'exchange': self.exchange
        }

        # 创建结果文件目录并保存结果
        result_dir = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), '../../tmp/backtest_results')
        os.makedirs(result_dir, exist_ok=True)
        result_filename = f"{self.strategy}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        result_file_path = os.path.join(result_dir, result_filename)

        with open(result_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(self.stats), f,
                      ensure_ascii=False, indent=2)

        translated_result = self.to_dict(self.stats)
        total_return = 0.0
        max_drawdown = 0.0
        for i in translated_result:
            if i['cn'] == '收益率':
                total_return = float(i['value'])
            if i['cn'] == '最大回撤':
                max_drawdown = float(i['value'])

        # 保存回测记录到数据库
        try:
            # 数据验证
            if not isinstance(total_return, (int, float)):
                raise ValueError(f"无效的总回报率: {total_return}")
            if not isinstance(max_drawdown, (int, float)):
                raise ValueError(f"无效的最大回撤: {max_drawdown}")

            # 保存回测记录到数据库
            BacktestRecord.create(
                strategy_name=self.strategy,
                start_time=datetime.strptime(self.start, '%Y-%m-%d'),
                end_time=datetime.strptime(self.end, '%Y-%m-%d'),
                file_name=file_name,
                parameters=json.dumps(parameters, ensure_ascii=False),
                results=json.dumps(translated_result,
                                   ensure_ascii=False, default=str),
                trades=json.dumps(trades, ensure_ascii=False, default=str),
                strategy=json.dumps(strategy_data, ensure_ascii=False),
                result_file_path=result_file_path,
                total_return=float(total_return),
                max_drawdown=float(max_drawdown)
            )
            logger.info(f"回测记录保存成功: {file_name}")
        except Exception as e:
            logger.error(f"保存回测记录失败: {str(e)}", exc_info=True)
            raise  # 重新抛出异常以便上层处理

        return translated_result


if __name__ == '__main__':
    # 示例：使用策略类名创建Backtest实例
    backtest = Backtest('SmaCross', 'ETH/USDT', '15m',
                        '2025-01-01', '2025-06-01', 10_000, 0.002)
    stats = backtest.run()
    print(stats)

    # 获取回测记录
    # backtest_records = BacktestRecord.select().order_by(BacktestRecord.start_time.desc())
    # for record in backtest_records:
    #     print(record.to_dict())
    # print(record.strategy_name, record.start_time, record.end_time, record.total_return, record.max_drawdown)
    # backtest.bt.plot()
    # # 示例：获取所有策略类的名称
    # strategy_names = get_strategy_class_names()
    # print(strategy_names)
    # 示例: 手动创建Backtest实例
    # from zbot.utils.dateutils import timestamp_to_datetime, format_datetime
    # # 获取 K 线数据
    # candles = get_candles_from_db(
    #     'binance', "ETH/USDT", "15m", "2025-01-01", "2025-06-01")
    # if not candles.empty:
    #     del candles['id']
    #     # 将open_time时间戳转换为时间字符串
    #     candles['open_time'] = candles['open_time'].apply(
    #         lambda x: timestamp_to_datetime(x))
    #     # del candles['id']
    #     candles.rename(columns={'open': 'Open', 'close': 'Close',
    #                    'high': 'High', 'low': 'Low', 'volume': 'Volume'}, inplace=True)
    #     candles.set_index('open_time', drop=True, inplace=True)
    #     print(candles.tail())
    #     print(candles.columns)
    #     # df = BTCUSD
    #     # print(df.columns)
    #     # print(df.head())
    #     bt = Backtest(candles, SmaCross, cash=10_000,
    #                   commission=0.002, exclusive_orders=True)
    #     bt = FractionalBacktest(candles, SmaCross, fractional_unit=1e-06,
    #                             cash=10_000, commission=0.002, exclusive_orders=True)
    #     stats = bt.run()
    #     print(stats)
    #     bt.plot()
