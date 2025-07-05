from zbot.common.config import read_config
from zbot.exchange.exchange import ExchangeFactory

exchange_name = 'binance'
# 从配置文件读取交易所信息
config = read_config('exchange').get(exchange_name)

# 使用工厂类动态创建交易所实例
exchange = ExchangeFactory.create_exchange(exchange_name, config)

# 调用下载数据方法
if exchange:
    print(f"成功加载{exchange.exchange_name}交易所模块")
    candles = exchange.download_data(
        symbol='BTC/USDT', interval='15m', start_time='2025-01-01', end_time='2025-01-02')
    print(f"下载完成，共获取{len(candles)}条K线数据")
else:
    print("交易所模块加载失败")
