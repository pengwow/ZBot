
import importlib

from zbot.common.config import read_config
from . import Exchange



    # @abstractmethod
    # def download_data(self, *args, **kwargs):
    #     pass

    # @abstractmethod
    # def get_account_balance(self, *args, **kwargs):
    #     pass

    # @abstractmethod
    # def get_order(self, *args, **kwargs):
    #     pass

    # @abstractmethod
    # def get_orders(self, *args, **kwargs):
    #     pass

    # @abstractmethod
    # def create_order(self, *args, **kwargs):
    #     pass

    # @abstractmethod
    # def cancel_order(self, *args, **kwargs):
    #     pass


class ExchangeFactory:
    @staticmethod
    def create_exchange(exchange_name, config: dict = {}) -> Exchange:
        config = config or read_config('exchange').get(exchange_name)
        module_name = f"zbot.exchange.{exchange_name.lower()}"
        class_name = f"{exchange_name.capitalize()}Exchange"
        try:
            module = importlib.import_module(module_name)
            exchange_class = getattr(module, class_name)
            return exchange_class(
                exchange_name=exchange_name,
                api_key=config.get('api_key'),
                secret_key=config.get('secret_key'),
                trading_mode=config.get('trading_mode'),
                proxy_url=config.get('proxy_url'),
                testnet=config.get('testnet', False)
            )
        except ImportError:
            raise ValueError(f"Exchange {exchange_name} is not supported {module_name}")
        except AttributeError:
            raise ValueError(f"Class {class_name} not found in {module_name}")
