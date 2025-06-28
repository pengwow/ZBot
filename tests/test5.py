import re


def extract_username_tags(text):
    # 正则表达式模式：匹配<@username>格式的标签
    pattern = r'<@(\w+)>'

    # 使用finditer获取所有匹配项及其位置信息
    matches = re.finditer(pattern, text)

    # 构建字典：username -> 原始标签
    result = {match.group(1): match.group(0) for match in matches}

    return result


# 测试用例
at_user_list = '复合人:<@zhangsan><@lisi><@wangwu>'
output = extract_username_tags(at_user_list)
print(output)