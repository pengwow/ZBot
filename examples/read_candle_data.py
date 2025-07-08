"""
使用Peewee ORM直接读取K线数据的示例脚本

该脚本演示如何使用Peewee ORM直接从数据库中检索K线数据，
包括日期时间转换、查询构建和结果处理的完整流程
"""
from datetime import datetime
from zbot.exchange.binance.models import Candle  # 导入Binance交易所的Candle模型
# from zbot.common.config import db  # 导入数据库配置
from zbot.services.db import database


def parse_datetime(date_str: str) -> int:
    """将日期时间字符串转换为毫秒级时间戳

    参数:
        date_str: 日期时间字符串，支持格式: YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS

    返回:
        int: 毫秒级时间戳
    """
    for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S']:
        try:
            return int(datetime.strptime(date_str, fmt).timestamp() * 1000)
        except ValueError:
            continue
    raise ValueError(f"无效的日期格式: {date_str}")


def main():
    # 配置查询参数
    symbol = "BTCUSDT"
    interval = "15m"
    start_date = "2023-09-01"
    end_date = "2023-09-02"

    try:
        # 初始化数据库连接
        database.open_connection()

        # 转换日期为时间戳
        start_timestamp = parse_datetime(start_date)
        end_timestamp = parse_datetime(end_date)
        
        # 使用Peewee ORM直接查询数据库
        query = (
            Candle.select()
            .where(
                (Candle.symbol == symbol)
                & (Candle.timeframe == interval)
                & (Candle.open_time >= start_timestamp)
                & (Candle.open_time <= end_timestamp)
            )
            .order_by(Candle.open_time.asc())
            .distinct(Candle.open_time)  # 去重
        )

        # 执行查询并获取结果
        candles = list(query)

        # 打印查询结果摘要
        print(f"成功查询到 {len(candles)} 条{symbol} {interval} K线数据")
        print(f"时间范围: {start_date} ~ {end_date}")

        # 打印前5条K线详情
        if candles:
            print("\n前5条K线数据详情:")
            for i, candle in enumerate(candles[:5]):
                print(f"\nK线 #{i+1}:")
                print(f"时间戳: {candle.timestamp} ({datetime.fromtimestamp(candle.timestamp/1000)})")
                print(f"开盘价: {candle.open:.4f}")
                print(f"最高价: {candle.high:.4f}")
                print(f"最低价: {candle.low:.4f}")
                print(f"收盘价: {candle.close:.4f}")
                print(f"成交量: {candle.volume:.6f}")

    except Exception as e:
        print(f"查询失败: {str(e)}")
    finally:
        # 确保数据库连接关闭
        database.closed()


if __name__ == "__main__":
    main()