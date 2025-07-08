import datetime
from importlib import import_module
from typing import List, Optional, Any
from zbot.utils.dateutils import str_to_timestamp


def get_candles_from_db(
    exchange: str,
    symbol: str,
    timeframe: str,
    start: str,
    end: str
) -> List[Any]:
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
        List[Any]: 去重并排序后的K线数据列表
    """
    # 动态导入对应交易所的Candle模型
    try:
        candle_module = import_module(f"zbot.exchange.{exchange}.models")
        Candle = candle_module.Candle
    except ImportError:
        raise ValueError(f"不支持的交易所: {exchange}")
    start = str_to_timestamp(start)
    end = str_to_timestamp(end)
    # 查询指定条件的K线数据并按时间戳排序
    ddd = Candle.select().where(
            (Candle.symbol == symbol)
            & (Candle.timeframe == timeframe)
            & Candle.open_time.between(start, end)
        ).order_by(Candle.open_time)
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

    return unique_candles


if __name__ == "__main__":
    candles = get_candles_from_db('binance', "BTC/USDT", "15m", "2025-01-01", "2025-01-03")
    
    for candle in candles:
        print(candle.timestamp, candle.close)
