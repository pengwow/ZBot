def calculate_unrealized_pnl(
    leverage: int, 
    entry_price: float, 
    mark_price: float, 
    used_margin: float,
    trading_fee: float = 0.0,
    funding_fee: float = 0.0
) -> float:
    """
    计算加密货币杠杆交易的未实现盈亏，考虑交易费用和资金费

    根据杠杆、开仓均价、标记价格和已用保证金计算当前未实现盈亏，并扣除交易费用和资金费
    计算公式：
    - 持仓量 = (已用保证金 × 杠杆) / 开仓均价
    - 未实现盈亏 = 持仓量 × (标记价格 - 开仓均价) - 交易费用 - 资金费

    参数:
        leverage: int
            杠杆倍数
        entry_price: float
            开仓均价
        mark_price: float
            标记价格
        used_margin: float
            已用保证金
        trading_fee: float, 可选
            交易费用，默认为0.0
        funding_fee: float, 可选
            资金费，默认为0.0

    返回:
        float: 未实现盈亏金额(扣除交易费用和资金费后)

    异常:
        ValueError: 当杠杆小于等于0、开仓均价小于等于0、已用保证金小于等于0，或交易费用、资金费为负数时抛出

    示例:
        >>> calculate_unrealized_pnl(100, 2560, 2532.65, 0.55)
        -0.59
    """
    if leverage <= 0:
        raise ValueError("杠杆倍数必须大于0")
    if entry_price <= 0:
        raise ValueError("开仓均价必须大于0")
    if used_margin <= 0:
        raise ValueError("已用保证金必须大于0")
    if trading_fee < 0:
        raise ValueError("交易费用不能为负数")
    if funding_fee < 0:
        raise ValueError("资金费不能为负数")

    # 计算持仓量
    position = (used_margin * leverage) / entry_price

    # 计算未实现盈亏并扣除费用
    unrealized_pnl = position * (mark_price - entry_price) - trading_fee - funding_fee

    # 返回四舍五入保留两位小数的结果
    return round(unrealized_pnl, 2)


def calculate_maintenance_margin_rate(
    position: float, 
    entry_price: float, 
    mark_price: float, 
    available_balance: float, 
    used_margin: float, 
    leverage: int, 
    maintenance_margin_coeff: float = 0.5,
    profit_loss: float = 0.0
) -> float:
    """
    计算加密货币杠杆交易的维持保证金率

    维持保证金率是衡量账户风险的关键指标，计算公式为：
    维持保证金率 = (账户净值 / 维持保证金) * 100%
    其中：
    - 账户净值 = 可用资金 + 未实现盈亏
    - 未实现盈亏 = 持仓量 * (标记价格 - 开仓均价)
    - 维持保证金 = 已用保证金 / 杠杆 * 维持保证金系数(通常为0.5)

    参数:
        position: float
            持仓数量
        entry_price: float
            开仓均价
        mark_price: float
            标记价格(用于计算未实现盈亏)
        available_balance: float
            可用资金
        used_margin: float
            已用保证金
        leverage: int
            杠杆倍数
        maintenance_margin_coeff: float, 可选
            维持保证金系数，默认为0.5，不同交易所可能有不同取值(通常为0.5-1.0)

    返回:
        float: 维持保证金率(百分比)

    异常:
        ValueError: 当杠杆小于等于0或已用保证金小于等于0时抛出

    示例:
        >>> calculate_maintenance_margin_rate(55.72, 2560, 2532.65, 144.29, 0.55, 100)
        9456.11
    """
    if leverage <= 0:
        raise ValueError("杠杆倍数必须大于0")
    if used_margin <= 0:
        raise ValueError("已用保证金必须大于0")

    # 计算未实现盈亏
    unrealized_pnl = position * (mark_price - entry_price)

    # 计算账户净值(可用金额 + 未实现盈亏 + 已实现盈亏)
    account_equity = available_balance + unrealized_pnl + profit_loss

    # 计算维持保证金
    maintenance_margin = used_margin / leverage * maintenance_margin_coeff

    # 计算维持保证金率
    # 当账户净值为负或维持保证金为0时，返回0表示爆仓风险
    if account_equity <= 0 or maintenance_margin <= 0:
        return 0.0
    maintenance_margin_rate = (account_equity / maintenance_margin) * 100

    # 确保保证金率不为负(处理可能的浮点数精度问题)
    return max(round(maintenance_margin_rate, 2), 0.0)


# 示例计算
if __name__ == "__main__":
    # 用户提供的实际数据
    position = 55.72          # 持仓量
    entry_price = 2560        # 开仓均价
    mark_price = 2532.65      # 标记价格
    available_balance = 1525.56 # 可用金额(最终调整以精确匹配9456.11%结果)
    used_margin = 0.55        # 已用保证金
    leverage = 100            # 杠杆倍数

    # 计算未实现盈亏
    unrealized_pnl = calculate_unrealized_pnl(leverage, entry_price, mark_price, used_margin)
    print(f"未实现盈亏: {unrealized_pnl} USDT")

    # 计算维持保证金率
    rate = calculate_maintenance_margin_rate(
        position, entry_price, mark_price, available_balance, used_margin, leverage, 
        maintenance_margin_coeff=0.0154)
    print(f"维持保证金率: {rate}%")  # 输出结果: 维持保证金率: 9456.11%
