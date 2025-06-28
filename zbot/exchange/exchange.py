from abc import ABC, abstractmethod
import importlib


class Exchange(ABC):
    def __init__(self, exchange_name, api_key, secret_key, proxy_url, testnet=False):
        self.exchange_name = exchange_name
        self.api_key = api_key
        self.secret_key = secret_key
        self.proxy_url = proxy_url
        self.testnet = testnet

    @abstractmethod
    def download_data(self, *args, **kwargs):
        pass


class ExchangeFactory:
    @staticmethod
    def create_exchange(exchange_name, config):
        module_name = f"zbot.exchange.{exchange_name.lower()}"
        class_name = f"{exchange_name.capitalize()}Exchange"
        try:
            module = importlib.import_module(module_name)
            exchange_class = getattr(module, class_name)
            return exchange_class(
                exchange_name=exchange_name,
                api_key=config.get('api_key'),
                secret_key=config.get('secret_key'),
                proxy_url=config.get('proxy_url'),
                testnet=config.get('testnet', False)
            )
        except ImportError:
            raise ValueError(f"Exchange {exchange_name} is not supported")
        except AttributeError:
            raise ValueError(f"Class {class_name} not found in {module_name}")
