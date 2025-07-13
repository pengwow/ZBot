from abc import ABC, abstractmethod
import pandas as pd

class Exchange(ABC):
    def __init__(self, exchange_name, api_key, secret_key, trading_mode, proxy_url, testnet=False):
        self.exchange_name = exchange_name
        self.api_key = api_key
        self.secret_key = secret_key
        self.proxy_url = proxy_url
        self.trading_mode = trading_mode
        self.testnet = testnet
    
    @abstractmethod
    def download_data(self, *args, **kwargs):
        pass

    @abstractmethod
    def load_data(self, *args, **kwargs) -> pd.DataFrame:
        pass
