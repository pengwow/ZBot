import asyncio
from enum import verify
import aiohttp
import ssl
import certifi

async def fetch_url(url):
    """
    使用异步方式请求指定URL并读取数据
    :param url: 要请求的URL
    :return: 响应内容
    """
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl.create_default_context(cafile=certifi.where()))) as session:
        async with session.get(url) as response:
            return await response.text()

# 示例使用
async def main():
    url = "http://baidu.com"
    data = await fetch_url(url)
    print(data)

if __name__ == "__main__":
    asyncio.run(main())
