import time
from datetime import datetime, timedelta
from typing import Optional, Union


def timestamp_to_datetime(timestamp: Union[int, float, str], unit: str = 'ms', tz: str = 'UTC') -> Optional[datetime]:
    """
    将时间戳转换为datetime对象
    :param timestamp: 时间戳，可以是整数、浮点数或字符串
    :param unit: 时间单位，'ms'表示毫秒，'s'表示秒
    :param tz: 时区，默认为 'UTC'
    :return: datetime对象或None
    """
    try:
        import pytz
        timestamp = float(timestamp)
        if unit == 'ms':
            timestamp /= 1000
        tz_obj = pytz.timezone(tz)
        # 先将时间戳转换为带时区的datetime对象，再去除时区信息
        dt = datetime.fromtimestamp(timestamp, tz_obj)
        return dt.replace(tzinfo=None)
    except (ValueError, TypeError):
        return None
    except pytz.UnknownTimeZoneError:
        return None


def datetime_to_timestamp(dt: datetime, unit: str = 'ms') -> int:
    """
    将datetime对象转换为时间戳
    :param dt: datetime对象
    :param unit: 时间单位，'ms'表示毫秒，'s'表示秒
    :return: 时间戳
    """
    timestamp = dt.timestamp()
    if unit == 'ms':
        return int(timestamp * 1000)
    return int(timestamp)


def format_datetime(dt: Optional[datetime] = None, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    格式化datetime对象为字符串
    :param dt: datetime对象，默认为当前时间
    :param fmt: 格式化字符串
    :return: 格式化后的时间字符串
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)


def parse_datetime(datetime_str: str, fmt: str = '%Y-%m-%d %H:%M:%S') -> Optional[datetime]:
    """
    将字符串解析为datetime对象
    :param datetime_str: 时间字符串
    :param fmt: 格式化字符串
    :return: datetime对象或None
    """
    try:
        return datetime.strptime(datetime_str, fmt)
    except ValueError:
        return None


def get_time_ago(days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> datetime:
    """
    获取指定时间前的datetime对象
    :param days: 天数
    :param hours: 小时数
    :param minutes: 分钟数
    :param seconds: 秒数
    :return: datetime对象
    """
    return datetime.now() - timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


def get_time_after(days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> datetime:
    """
    获取指定时间后的datetime对象
    :param days: 天数
    :param hours: 小时数
    :param minutes: 分钟数
    :param seconds: 秒数
    :return: datetime对象
    """
    return datetime.now() + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


def is_valid_datetime(datetime_str: str, fmt: str = '%Y-%m-%d %H:%M:%S') -> bool:
    """
    检查时间字符串是否符合指定格式
    :param datetime_str: 时间字符串
    :param fmt: 格式化字符串
    :return: 是否有效的布尔值
    """
    return parse_datetime(datetime_str, fmt) is not None


def convert_timezone(dt: datetime, from_tz: str = 'UTC', to_tz: str = 'Asia/Shanghai') -> datetime:
    """
    转换时区
    :param dt: datetime对象
    :param from_tz: 原时区
    :param to_tz: 目标时区
    :return: 转换后的datetime对象
    """
    import pytz
    from_tz = pytz.timezone(from_tz)
    to_tz = pytz.timezone(to_tz)
    return from_tz.localize(dt).astimezone(to_tz)

def get_date_range(start_date: str, end_date: str, fmt: str = '%Y-%m-%d') -> list:
    """
    根据开始和结束时间返回一个列表，每个元素为时间范围内的日期字符串
    :param start_date: 开始日期字符串
    :param end_date: 结束日期字符串
    :param fmt: 日期格式化字符串，默认为 '%Y-%m-%d'
    :return: 日期字符串列表
    """
    start_dt = parse_datetime(start_date, fmt)
    end_dt = parse_datetime(end_date, fmt)
    if start_dt is None or end_dt is None:
        return []
    
    date_range = []
    current_dt = start_dt
    while current_dt <= end_dt:
        date_range.append(current_dt.strftime(fmt))
        current_dt += timedelta(days=1)
    return date_range



def get_timestamp_range_by_date(date_str: str, fmt: str = '%Y-%m-%d', unit: str = 'ms') -> Optional[tuple]:
    """
    根据日期字符串生成该日期从0点到23:59:59的时间戳范围
    :param date_str: 日期字符串，如 "2025-01-01"
    :param fmt: 日期格式化字符串，默认为 '%Y-%m-%d'
    :param unit: 时间单位，'ms'表示毫秒，'s'表示秒
    :return: 时间戳范围元组 (开始时间戳, 结束时间戳) 或 None
    """
    try:
        # 解析日期字符串为datetime对象
        date_dt = datetime.strptime(date_str, fmt)
        
        # 生成当天0点的datetime对象
        start_dt = date_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 生成当天23:59:59的datetime对象
        end_dt = date_dt.replace(hour=23, minute=59, second=59, microsecond=59)
        
        # 转换为时间戳
        start_timestamp = datetime_to_timestamp(start_dt, unit)
        end_timestamp = datetime_to_timestamp(end_dt, unit)
        
        return start_timestamp, end_timestamp
    except ValueError:
        return None

if __name__ == '__main__':
    # 示例用法
    print("当前时间格式化:", format_datetime())
    print("时间戳转datetime:", timestamp_to_datetime(1730073599999))
    print("datetime转时间戳(ms):", datetime_to_timestamp(datetime.now()))
    print("3天前的时间:", format_datetime(get_time_ago(days=3)))
    print("是否有效的时间格式:", is_valid_datetime("2023-13-01"))  # 无效月份
    print("时区转换:", format_datetime(convert_timezone(datetime(2023, 1, 1))))
    print("日期范围:", get_date_range("2023-01-01", "2023-01-10"))
    print("日期转时间戳范围:", get_timestamp_range_by_date("2023-01-01"))
