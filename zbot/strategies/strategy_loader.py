"""
策略加载工具模块，提供策略发现、加载和管理的通用功能
用于回测和实盘交易模块共享策略加载逻辑
"""
import os
import re
import importlib

# 策略目录路径
STRATEGIES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '.'
)


def get_strategy_names():
    """
    获取策略目录下所有策略文件名
    :return: 策略文件名列表
    """
    # 查找所有策略文件
    strategy_files = [f for f in os.listdir(STRATEGIES_DIR) 
                     if f.endswith('.py') and not f.startswith('__')]
    return strategy_files


def get_strategy_class_names():
    """
    查找策略目录下的策略文件中的策略类名
    :return: 包含所有策略类名和对应文件名的列表
    """
    class_names = []
    strategy_names = get_strategy_names()
    for filename in strategy_names:
        # 读取文件内容查找类定义
        with open(os.path.join(STRATEGIES_DIR, filename), 'r', encoding='utf-8') as f:
            content = f.read()

            # 使用正则表达式匹配类定义
            class_matches = re.findall(r'class\s+(\w+)\s*\(', content)

            # 查找匹配的类
            for name in class_matches:
                class_names.append({'name': name, 'filename': filename})
    return class_names


def load_strategy_class(strategy_name, strategy_path=None):
    """
    根据策略名称动态加载策略类
    :param strategy_name: 策略类名
    :param strategy_path: 自定义策略目录路径，默认为STRATEGIES_DIR
    :return: 策略类
    :raises ValueError: 当策略类未找到时抛出
    """
    strategies_dir = strategy_path or STRATEGIES_DIR

    # 遍历目录下的所有Python文件
    for filename in os.listdir(strategies_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            # 模块名称
            module_name = f'zbot.strategies.{filename[:-3]}'

            # 导入模块
            module = importlib.import_module(module_name)

            # 读取文件内容查找类定义
            with open(os.path.join(strategies_dir, filename), 'r', encoding='utf-8') as f:
                content = f.read()

                # 使用正则表达式匹配类定义
                class_matches = re.findall(r'class\s+(\w+)\s*\(', content)

                # 查找匹配的类
                for class_name in class_matches:
                    if class_name == strategy_name:
                        return getattr(module, class_name)

    # 如果未找到策略类
    raise ValueError(f"未找到策略类: {strategy_name}")