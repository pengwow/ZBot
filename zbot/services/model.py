import datetime
from importlib import import_module
from typing import List, Optional, Any, Tuple, Dict
import pandas as pd
from datetime import timedelta
import re
from zbot.utils.dateutils import str_to_timestamp, timestamp_to_datetime


def parse_timeframe(timeframe: str) -> timedelta:
    """
    将时间周期字符串转换为timedelta对象

    :param timeframe: 时间周期字符串，如'1m', '5m', '1h', '1d'
    :return: 对应的timedelta对象
    :raises ValueError: 如果时间周期格式无效
    """
    match = re.match(r'^(\d+)([mhd])$', timeframe)
    if not match:
        raise ValueError(f"无效的时间周期格式: {timeframe}, 应为数字加单位(m/h/d)")
    value, unit = int(match.group(1)), match.group(2)
    if unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    else:
        raise ValueError(f"不支持的时间单位: {unit}, 支持的单位为m/h/d")

def fill_missing_candles(candles: List[Any], timeframe: str) -> Tuple[List[Any], List[datetime]]:
    """
    识别并填充K线数据中的缺失值，使用均值填充法，并记录缺失的数据点

    :param candles: K线数据列表，每个元素应为包含open_time、open、high、low、close、volume等属性的对象
    :param timeframe: K线周期，如'1m', '15m', '1h'
    :return: 元组，包含两个元素：
             - 填充后的K线数据列表
             - 缺失数据点的时间列表(datetime对象)
    """
    if not candles:
        return [], []

    # 解析时间周期为timedelta
    interval = parse_timeframe(timeframe)
    filled_candles = []
    missing_times = []
    prev_candle = None

    for current_candle in candles:
        if prev_candle is None:
            filled_candles.append(current_candle)
            prev_candle = current_candle
            continue

        # 计算当前蜡烛和前一个蜡烛之间的预期时间差
        prev_time = timestamp_to_datetime(prev_candle.open_time, unit='us')
        current_time = timestamp_to_datetime(current_candle.open_time, unit='us')
        expected_next_time = prev_time + interval

        # 检查是否有缺失数据
        while current_time > expected_next_time:
            # 记录缺失时间
            missing_times.append(expected_next_time)

            # 计算缺失数据的均值填充值
            # 使用前后有效数据的均值
            fill_values = {
                'open': (prev_candle.close + current_candle.open) / 2,
                'high': max(prev_candle.high, current_candle.high),
                'low': min(prev_candle.low, current_candle.low),
                'close': (prev_candle.close + current_candle.open) / 2,
                'volume': (prev_candle.volume + current_candle.volume) / 2,
                # 其他需要填充的字段可以在这里添加
            }

            # 创建填充的蜡烛对象（假设Candle类有构造函数或可以通过关键字参数创建）
            # 获取当前蜡烛的类，保持类型一致
            CandleClass = type(current_candle)
            filled_candle = CandleClass(
                symbol=prev_candle.symbol,
                timeframe=prev_candle.timeframe,
                open_time=str_to_timestamp(expected_next_time, 'us'),
                open=fill_values['open'],
                high=fill_values['high'],
                low=fill_values['low'],
                close=fill_values['close'],
                volume=fill_values['volume'],
                # 其他必要字段使用默认值或前一个蜡烛的值
                **{k: v for k, v in prev_candle.__dict__.items() if k not in ['symbol', 'timeframe', 'open_time', 'open', 'high', 'low', 'close', 'volume']}
            )

            filled_candles.append(filled_candle)
            prev_candle = filled_candle
            expected_next_time += interval

        # 添加当前蜡烛
        filled_candles.append(current_candle)
        prev_candle = current_candle

    return filled_candles, missing_times

def get_candles_from_db(
    exchange: str,
    symbol: str,
    timeframe: str,
    start: str,
    end: str
) -> pd.DataFrame:
    """从数据库读取指定交易所的K线数据并进行排序和去重

    根据交易所动态导入对应的Candle模型，查询指定时间范围内的K线数据，
    按时间戳升序排序并去除重复数据后返回

    参数:
        exchange: 交易所名称(如'binance')
        symbol: 交易对(如'BTC/USDT')
        timeframe: K线周期(如'1m')
        start: 开始时间
        end: 结束时间

    返回:
        pd.DataFrame: 去重并排序后的K线数据，包含以下列:
            - open_time: 开盘时间戳(微秒)
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量
            其他列根据交易所模型可能有所不同
    """
    # 动态导入对应交易所的Candle模型
    try:
        candle_module = import_module(f"zbot.exchange.{exchange}.models")
        Candle = candle_module.Candle
    except ImportError:
        raise ValueError(f"不支持的交易所: {exchange}")
    start = str_to_timestamp(start, 'us')
    end = str_to_timestamp(end, 'us')
    # 查询指定条件的K线数据并按时间戳排序
    candles = list(
        Candle.select().where(
            (Candle.symbol == symbol)
            & (Candle.timeframe == timeframe)
            & Candle.open_time.between(start, end)
        ).order_by(Candle.open_time)
    )

    # 基于时间戳去重，保留第一个出现的记录
    seen_timestamps = set()
    unique_candles = []
    for candle in candles:
        if candle.open_time not in seen_timestamps:
            seen_timestamps.add(candle.open_time)
            unique_candles.append(candle)
    pd_candles = pd.DataFrame([candle.__data__ for candle in candles])
    return pd_candles


def analyze_candle_data_completeness(
    exchange_name: str
) -> List[Dict[str, Any]]:
    """
    分析指定交易所所有货币对的K线数据完整度

    该函数从配置文件读取默认时间范围和时间单位，从数据库获取该交易所的所有货币对，
    批量分析各货币对K线数据完整度并返回结构化结果。

    :param exchange_name: 交易所名称，如'binance'
    :return: 包含以下键的字典列表：
             - 'currency_pair': 货币对名称
             - 'timeframe': 时间单位
             - 'start_time': 请求开始时间(格式化字符串)
             - 'end_time': 请求结束时间(格式化字符串)
             - 'expected_count': 理论预期K线数量
             - 'actual_count': 实际K线数量
             - 'completeness': 数据完整度(百分比)
             - 'missing_count': 缺失K线数量
             - 'missing_ratio': 缺失比例(小数)
    """
    from zbot.utils.dateutils import parse_timeframe, timestamp_to_datetime, str_to_timestamp
    from typing import List, Dict, Any
    import pandas as pd
    from zbot.common.config import read_config
    from zbot.models.candle import Candle
    from zbot.services.db import database

    # 从配置文件读取默认参数
    config = read_config()
    exchange_config = config.get('exchanges', {}).get(exchange_name, {})
    timeframe = exchange_config.get('default_timeframe', '15m')
    start_date_str = exchange_config.get('default_start_date', '2025-01-01')
    end_date_str = exchange_config.get('default_end_date', '2025-01-03')

    # 从数据库获取该交易所的所有货币对
    database.open_connection()
    try:
        # 注意：Candle模型需要添加exchange字段才能过滤
        currency_pairs = [
            row.symbol for row in Candle.select(Candle.symbol).where(
                Candle.exchange == exchange_name
            ).distinct()
        ]
    except Exception as e:
        print(f"获取货币对列表失败: {e}")
        currency_pairs = []
    finally:
        database.closed()

    results = []
    # 解析时间范围
    start_timestamp = str_to_timestamp(start_date_str)
    end_timestamp = str_to_timestamp(end_date_str, is_end=True)
    start_time = timestamp_to_datetime(start_timestamp, unit='ms')
    end_time = timestamp_to_datetime(end_timestamp, unit='ms')
    interval = parse_timeframe(timeframe)
    total_seconds = (end_time - start_time).total_seconds()
    expected_count = int(total_seconds / interval.total_seconds()) + 1  # +1包含起始点

    for pair in currency_pairs:
        try:
            # 获取单个货币对数据
            data = get_candles_from_db(
                exchange_name=exchange_name,
                currency_pair=pair,
                timeframe=timeframe,
                start_time=start_date_str,
                end_time=end_date_str
            )

            actual_count = len(data)
            missing_count = max(0, expected_count - actual_count)
            completeness = (actual_count / expected_count) * 100 if expected_count > 0 else 0
            missing_ratio = 1 - (actual_count / expected_count) if expected_count > 0 else 1

            results.append({
                'currency_pair': pair,
                'timeframe': timeframe,
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'expected_count': expected_count,
                'actual_count': actual_count,
                'completeness': round(completeness, 2),
                'missing_count': missing_count,
                'missing_ratio': round(missing_ratio, 4)
            })
        except Exception as e:
            # 记录错误并继续处理其他货币对
            results.append({
                'currency_pair': pair,
                'timeframe': timeframe,
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'expected_count': expected_count,
                'actual_count': 0,
                'completeness': 0.0,
                'missing_count': expected_count,
                'missing_ratio': 1.0,
                'error': str(e)
            })

    return results


if __name__ == "__main__":
    candles = get_candles_from_db('binance', "BTC/USDT", "15m", "2025-01-01", "2025-01-03")
    print(candles.head())
    print(candles.columns)
    # for candle in candles:
    #     print(timestamp_to_datetime(candle.open_time), candle.close)
    
