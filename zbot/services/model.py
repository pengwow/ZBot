import datetime
from importlib import import_module
from typing import List, Optional, Any, Tuple
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


if __name__ == "__main__":
    candles = get_candles_from_db('binance', "BTC/USDT", "15m", "2025-01-01", "2025-01-03")
    print(candles.head())
    print(candles.columns)
    # for candle in candles:
    #     print(timestamp_to_datetime(candle.open_time), candle.close)
    
