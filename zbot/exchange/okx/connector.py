import asyncio
import aiohttp
import time
import hmac
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import urllib.parse
import json
from zbot.services.connectors.base_connector import Exchange
from zbot.common.config import read_config


class OkxExchange(Exchange):
    """Okx交易所连接器实现"""
    def __init__(self, api_key: str, secret_key: str, proxy_url: str = None, testnet: bool = False):
        super().__init__(api_key, secret_key, proxy_url, testnet)
        self.base_url = 'https://www.okx.com' if not testnet else 'https://www.okx.com'
        self.api_key = api_key
        self.secret_key = secret_key
        self.proxy_url = proxy_url
        self.testnet = testnet
        self.session = aiohttp.ClientSession()
        self.headers = {
            'Content-Type': 'application/json',
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': '',
            'OK-ACCESS-TIMESTAMP': '',
            'OK-ACCESS-PASSPHRASE': ''
        }
        self.passphrase = hmac.new(self.secret_key.encode(), b'OK_ACCESS', hashlib.sha256).hexdigest()

    async def close(self):
        """关闭aiohttp会话"""
        await self.session.close()

    async def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """通用请求方法"""
        url = f"{self.base_url}{endpoint}"
        timestamp = str(int(time.time()))
        self.headers['OK-ACCESS-TIMESTAMP'] = timestamp
        self.headers['OK-ACCESS-PASSPHRASE'] = self.passphrase
        self.headers['OK-ACCESS-SIGN'] = self._generate_sign(method, endpoint, timestamp, params, data)
        async with self.session.request(method, url, headers=self.headers, params=params, data=data) as response:
            return await response.json()

    def _generate_sign(self, method: str, endpoint: str, timestamp: str, params: Dict = None, data: Dict = None) -> str:
        """生成签名"""
        if params:
            query_string = urllib.parse.urlencode(params)
            endpoint = f"{endpoint}?{query_string}"
        if data:
            data = json.dumps(data)
        message = f"{timestamp}{method.upper()}{endpoint}{data or ''}"
        return hmac.new(self.secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()
