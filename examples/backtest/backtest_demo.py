from zbot.exchange.binance.client import BinanceExchange
from zbot.exchange.binance.data import History
from zbot.strategies.sma_strategy import SMAStrategy
from zbot.strategies.base_strategy import BacktestEngine
from zbot.common.config import read_config


def run_backtest_demo():
    # 1. 读取配置并初始化交易所客户端
    config = read_config('BINANCE')
    exchange = BinanceExchange(
        api_key=config.get('api_key'),
        secret_key=config.get('secret_key'),
        proxy_url=config.get('proxy_url')
    )
    history = History(exchange)

    # 2. 加载历史数据（示例：BTCUSDT 15分钟线）
    print("正在加载历史数据...")
    data = history.load_and_clean_data(
        symbol='BTCUSDT',
        timeframe='15m',
        start_time='2024-01-01',
        end_time='2024-06-01'
    )

    if data.empty:
        print("未获取到数据，无法进行回测")
        return

    print(f"成功加载 {len(data)} 条K线数据")

    # 3. 初始化策略和回测引擎
    strategy_params = {
        'short_window': 20,  # 短期均线窗口
        'long_window': 50    # 长期均线窗口
    }
    backtest_engine = BacktestEngine(
        strategy_class=SMAStrategy,
        data=data,
        params=strategy_params
    )

    # 4. 运行回测
    print("开始回测...")
    results = backtest_engine.run()

    # 5. 打印回测结果摘要
    print("\n回测结果摘要:")
    print(results)

    # 6. 绘制回测图表
    print("\n生成回测图表...")
    backtest_engine.plot(
        title='SMA策略回测结果',
        filename='sma_strategy_backtest.html',
        open_browser=True
    )

    # 7. 参数优化示例（可选）
    print("\n开始参数优化...")
    optimization_results = backtest_engine.optimize(
        parameter_ranges={
            'short_window': range(10, 30, 5),
            'long_window': range(40, 70, 10)
        },
        maximize='Equity Final [$]',
        constraint=lambda param: param.short_window < param.long_window
    )
    print("优化结果最佳参数:")
    print(optimization_results._strategy)


if __name__ == '__main__':
    run_backtest_demo()