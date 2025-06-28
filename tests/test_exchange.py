

import ccxt

proxies = {
    'http': 'http://127.0.0.1:7890',  # HTTP 代理
    'https': 'http://127.0.0.1:7890',  # HTTPS 代理
    'websocket': 'ws://127.0.0.1:7890/ws'  # WebSocket 代理
}
# proxies = 'http://127.0.0.1:7890/'
# exchange_id = 'binance'

# exchange_class = getattr(ccxt, exchange_id)
# exchange = exchange_class({
#     'apiKey': 'EQejQgZXTqrwORDHLDVBcroKupBfvZzCpOc3qDcDBqDk7Bl6WZVRhc5LBJaxZ99v',
#     'secret': '4i1j4gd7bnvF2QKECIPmK9kxzFD2Y1XOyt3V8LG2kdiFRJudjIII8vBMiDTkZCDX',
#     # 'httpsProxy': 'http://127.0.0.1:7890/'
# })
# exchange.proxyUrl = proxies['http']
# exchange.http_proxy = proxies
# exchange.UpdateProxySettings()
exchange = ccxt.binance({
    'apiKey': 'EQejQgZXTqrwORDHLDVBcroKupBfvZzCpOc3qDcDBqDk7Bl6WZVRhc5LBJaxZ99v',
    'secret': '4i1j4gd7bnvF2QKECIPmK9kxzFD2Y1XOyt3V8LG2kdiFRJudjIII8vBMiDTkZCDX',
    'httpsProxy': 'http://127.0.0.1:7890/'
})
# exchange.proxyUrl = proxies['http']
exchange.httpProxyUrl = proxies['http']
import time
def get_raw_ohlcv():
    """获取原始蜡烛图数据"""
    prase_ohlcv_original = exchange.parse_ohlcv
    def prase_ohlcv_custom(ohlcv, market):
        res = prase_ohlcv_original(ohlcv, market)
        res.append(ohlcv)
        return res
    exchange.parse_ohlcv = prase_ohlcv_custom
    res = exchange.fetch_ohlcv('BTC/USDT', '1d', limit=10)
    return res

print(get_raw_ohlcv())

# if exchange.has['fetchOHLCV']:
#     prase_ohlcv_original = exchange.parse_ohlcv
#     def prase_ohlcv_custom(ohlcv, market):
#         res = prase_ohlcv_original(ohlcv, market)
#         res.append(ohlcv)
#         return res
#
#
#     exchange.parse_ohlcv = prase_ohlcv_custom
#     res = exchange.fetch_ohlcv('BTC/USDT', '1d')
#     print(res)
# import asyncio
# 原始蜡烛图数据
# async def test():
#     ex = ccxt.async_support.coinbase()
#     prase_ohlcv_original = ex.parse_ohlcv
#     def prase_ohlcv_custom(ohlcv, market):
#         res = prase_ohlcv_original(ohlcv, market)
#         res.append(ohlcv)
#         return res
#     ex.parse_ohlcv = prase_ohlcv_custom
#     result = await ex.fetch_ohlcv('BTC/USDT', '1m')
#     print (result[0])
#
# asyncio.run(test())
# import random
# if (exchange.has['fetchTicker']):
#     print(exchange.fetch_ticker('BTC/USDT')) # ticker for LTC/ZEC
#     symbols = list(exchange.markets.keys())
#     print(exchange.fetch_ticker(random.choice(symbols))) # ticker for a random symbol