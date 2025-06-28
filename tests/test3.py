import time

import aiohttp
import asyncio

async def fetch(url):
    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector, trust_env=True) as session:
        async with session.get(url) as response:
            print(f"状态码: {response.status}")
            html = await response.text()  # 获取文本响应
            return html[:100]  # 截取前100字符

ddd = asyncio.run(fetch("http://www.baidu.com"))
print('111')
print(ddd)