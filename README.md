# ZBot

ZBot 是一个量化交易框架，支持加密货币交易策略的开发、回测和实盘运行。

## 主要功能
- 连接交易所（如 Binance）获取市场数据
- 实现多种交易策略（如 SMA 交叉策略）
- 支持历史数据回测
- 提供数据可视化界面

## 项目结构
- `zbot/exchange/`: 交易所接口实现
- `zbot/strategies/`: 交易策略定义
- `zbot/services/`: 核心服务逻辑
- `examples/`: 使用示例代码
- `ui/`: 可视化界面组件

## 安装依赖
```bash
pip install -r requirements.txt
```

## 快速开始
参考 `examples/` 目录下的示例代码，了解如何使用框架进行数据获取和策略回测。
        