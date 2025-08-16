from abc import ABC, abstractmethod
import pandas as pd

class Exchange(ABC):
    def __init__(self, exchange_name, api_key, secret_key, trading_mode, proxy_url, testnet=False, api_passphrase=None):
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

    @abstractmethod
    def health_check(self) -> bool:
        """
        策略健康检查，确保市场数据和账户信息正常，是做市风险控制的第一道防线
        
        健康检查在加密货币做市中至关重要，因为实时市场数据和账户状态的准确性直接影响：
        1. 订单定价合理性
        2. 风险敞口控制
        3. 策略决策有效性
        
        检查项包括：
        1. 订单簿数据新鲜度（延迟不超过设定阈值）
        2. 订单簿校验和（确保数据完整性，防止传输错误）
        3. 账户信息时效性
        
        :return: True表示健康状态良好，False表示存在异常需要处理
        """
        pass