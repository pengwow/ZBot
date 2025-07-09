import os
import yaml

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read_config(key='', file_path='') -> dict:
    """
    读取配置文件内容
    
    :param file_path: 配置文件路径，默认为 'config.yml'
    :return: 配置文件内容的字典
    """
    try:
        file_path = file_path or os.path.join(base_path, 'config.yml')
        with open(file_path, 'r', encoding='utf-8') as file:
            if key:
                return yaml.safe_load(file)[key]
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"错误：未找到配置文件 {file_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"错误：解析配置文件 {file_path} 时出错 - {e}")
        return {}

def write_config(data, file_path=''):
    """
    写入配置文件内容
    
    :param data: 要写入的配置数据
    :param file_path: 配置文件路径，默认为 'config.yml'
    """
    try:
        file_path = file_path or os.path.join(base_path, 'config.yml')
        with open(file_path, 'w', encoding='utf-8') as file:
            yaml.dump(data, file, default_flow_style=False)
    except Exception as e:
        print(f"错误：写入配置文件 {file_path} 时出错 - {e}")

