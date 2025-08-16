import asyncio
import logging
import os
from binance_common.models import WebsocketApiResponse
from zbot.exchange.binance.websocket_connector import BinanceWebSocketConnector

# Configure logging
logging.basicConfig(level=logging.INFO)


def my_callback(data: WebsocketApiResponse):
    """
    用户自定义回调函数
    
    Args:
        data (WebsocketApiResponse): WebSocket 响应数据
    """
    print(f"收到数据: {data}")
    if hasattr(data, 'data') and data.data:
        print(f"数据内容: {data.data}")


async def main():
    """
    主函数，演示如何使用 BinanceWebSocketConnector 连接不同的数据流
    """
    # 创建连接器实例
    proxy = {
        "host": "127.0.0.1",
        "port": 7890,
        "protocol": "http",
    } 
    
    # 从环境变量获取 API 密钥，或者可以在这里直接指定
    api_key = os.getenv("BINANCE_API_KEY")
    secret_key = os.getenv("BINANCE_SECRET_KEY")
    
    connector = BinanceWebSocketConnector(api_key=api_key, secret_key=secret_key, proxy=proxy)
    
    # 设置回调函数
    connector.set_callback(my_callback)
    
    try:
        # 示例1: 连接到标记价格数据流
        print("连接到标记价格数据流...")
        await connector.connect("kline_candlestick_streams", symbol="btcusdt", interval="1m")
        await asyncio.sleep(10)  # 运行10秒
        await connector.disconnect()
        
        # 示例2: 连接到K线数据流 (如果支持)
        # print("连接到K线数据流...")
        # await connector.connect("kline_stream", symbol="btcusdt", interval="1m")
        # await asyncio.sleep(10)  # 运行10秒
        # await connector.disconnect()
        
    except KeyboardInterrupt:
        logging.info("程序被用户中断")
    except Exception as e:
        logging.error(f"程序运行出错: {e}")
    finally:
        # 断开连接
        await connector.disconnect()


if __name__ == "__main__":
    asyncio.run(main())