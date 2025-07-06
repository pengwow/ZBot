import redis
import configparser

def read_redis_config(config_path='redis_config.ini'):
    """
    读取 Redis 配置文件
    :param config_path: 配置文件路径，默认为 'redis_config.ini'
    :return: 包含 Redis 配置的字典
    """
    config = configparser.ConfigParser()
    config.read(config_path)
    if 'redis' not in config:
        raise ValueError("配置文件中未找到 'redis' 部分")
    
    redis_config = {
        'host': config['redis'].get('host', 'localhost'),
        'port': config['redis'].getint('port', 6379),
        'password': config['redis'].get('password', None),
        'db': config['redis'].getint('db', 0),
        'decode_responses': config['redis'].getboolean('decode_responses', True)
    }
    return redis_config

def redis_operation_example(key, value=None, operation='get'):
    """
    Redis 读取写入示例函数
    :param key: Redis 键
    :param value: 写入的值，当操作为写入时需要提供
    :param operation: 操作类型，'get' 为读取，'set' 为写入
    :return: 读取操作返回对应的值，写入操作返回操作结果
    """
    try:
        redis_config = read_redis_config()
        r = redis.StrictRedis(**redis_config)
        
        if operation == 'get':
            return r.get(key)
        elif operation == 'set':
            if value is None:
                raise ValueError("写入操作需要提供 value 参数")
            return r.set(key, value)
        else:
            raise ValueError("不支持的操作类型，仅支持 'get' 和 'set'")
    except Exception as e:
        print(f"Redis 操作出错: {e}")
        return None
