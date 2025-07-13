# coding=utf-8
from sqlalchemy.util import symbol
from zbot.exchange.exchange import ExchangeFactory


# 使用工厂类动态创建交易所实例
exchange = ExchangeFactory.create_exchange('binance')

# 调用下载数据方法
if exchange:
    print(f"成功加载{exchange.exchange_name}交易所模块")
    symbol = 'ETC/USDT'
    interval = '15m'
    start_time = '2025-01-01'
    end_time = '2025-07-10'
    candles = exchange.download_data(symbol=symbol, interval=interval, start_time=start_time, end_time=end_time)
