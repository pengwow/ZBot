from abc import ABC, abstractmethod
class Exchange(ABC):
    def __init__(self, exchange_name, api_key, secret_key, trading_mode, proxy_url, testnet=False):
        self.exchange_name = exchange_name
        self.api_key = api_key
        self.secret_key = secret_key
        self.proxy_url = proxy_url
        self.trading_mode = trading_mode
        self.testnet = testnet