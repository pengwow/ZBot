import os
import yaml
from pathlib import Path
from zbot.services.main import config

def config(exchange, api_key, secret_key, proxy_url, trading_mode):
    """
    创建或修改交易所配置信息

    先从配置文件读取现有配置，更新或添加指定交易所的配置参数，然后写回文件。

    参数:
        exchange (str): 交易所名称
        api_key (str): API密钥
        secret_key (str): 密钥
        proxy_url (str): 代理URL
        trading_mode (str): 交易模式
    """
    print(f"配置交易商: {exchange}")
    print(f"api key: {api_key}")
    print(f"secret key: {secret_key}")
    print(f"代理url: {proxy_url}")
    print(f"交易模式: {trading_mode}")
    # 配置文件路径
    config_path = Path(os.path.dirname(os.path.abspath(__file__))).parent / 'config2.yaml'

    # 读取现有配置
    existing_config = {}
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                existing_config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"读取配置文件时出错，将创建新配置: {str(e)}")
            existing_config = {}

    # 确保exchange配置部分存在并更新
    exchange_config = existing_config.get('exchange', {})
    exchange_config['name'] = exchange  # 更新当前选中的交易所名称
    
    # 获取当前交易所的配置，不存在则创建新字典
    current_exchange_config = exchange_config.get(exchange, {})
    current_exchange_config.update({
        'api_key': api_key,
        'secret_key': secret_key,
        'proxy_url': proxy_url,
        'trading_mode': trading_mode
    })
    exchange_config[exchange] = current_exchange_config
    existing_config['exchange'] = exchange_config

    # 将更新后的配置数据写入 yaml 文件
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(existing_config, f, allow_unicode=True, default_flow_style=False)
        print(f"配置已成功写入 {config_path}")
    except Exception as e:
        print(f"写入配置文件时出错: {str(e)}")

if __name__ == "__main__":
    config('binance', '112233', '445566', '111111', '22222')