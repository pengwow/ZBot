import os
import yaml

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read_config(exchange='', file_path=''):
    """
    读取配置文件内容
    
    :param file_path: 配置文件路径，默认为 'config.yml'
    :return: 配置文件内容的字典
    """
    try:
        file_path = file_path or os.path.join(base_path, 'config.yml')
        with open(file_path, 'r', encoding='utf-8') as file:
            if exchange:
                return yaml.safe_load(file)['EXCHANGES'][exchange]
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"错误：未找到配置文件 {file_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"错误：解析配置文件 {file_path} 时出错 - {e}")
        return {}

if __name__ == '__main__':
    
    config = read_config('BINANCE')
    print(config)

