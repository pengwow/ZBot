import asyncio
import json
import os
from typing import Dict, List, Optional, Type
from zbot.trading.connectors.base_connector import AsyncExchange
from zbot.trading.strategy import AsyncBaseStrategy, AsyncDataProvider
from zbot.trading.connectors.binance_connector import AsyncBinanceExchange
from zbot.common.config import read_config


class TradingEngine(object):
    """实盘交易引擎，协调连接器、数据提供器和策略的执行"""
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or read_config('trading', default={})
        self.loop = asyncio.get_event_loop()
        self.connectors: Dict[str, AsyncExchange] = {}
        self.data_providers: Dict[str, AsyncDataProvider] = {}
        self.strategies: Dict[str, AsyncBaseStrategy] = {}
        self.running = False
        self._task: Optional[asyncio.Task] = None

    async def initialize(self):
        """初始化交易引擎"""
        # 初始化交易所连接器
        await self._init_connectors()
        # 初始化数据提供器
        await self._init_data_providers()
        # 加载策略
        await self._load_strategies()

    async def _init_connectors(self):
        """初始化交易所连接器"""
        exchange_configs = self.config.get('exchanges', {})
        for name, cfg in exchange_configs.items():
            exchange_type = cfg.get('type', 'binance')
            connector_cls: Type[AsyncExchange] = self._get_connector_class(exchange_type)

            if connector_cls:
                connector = connector_cls(
                    api_key=cfg.get('api_key'),
                    secret_key=cfg.get('secret_key'),
                    proxy_url=cfg.get('proxy_url'),
                    testnet=cfg.get('testnet', False)
                )
                await connector.initialize()
                self.connectors[name] = connector
                print(f"已初始化连接器: {name} ({exchange_type})")

    async def _init_data_providers(self):
        """初始化数据提供器"""
        # 默认使用交易所连接器作为数据提供器
        for name, connector in self.connectors.items():
            self.data_providers[name] = connector
            print(f"已注册数据提供器: {name}")

    async def _load_strategies(self):
        """加载策略"""
        strategy_configs = self.config.get('strategies', {})
        for strategy_name, cfg in strategy_configs.items():
            strategy_class = self._import_strategy_class(cfg.get('class_path'))
            if not strategy_class:
                continue

            # 获取关联的连接器和数据提供器
            connector_name = cfg.get('connector', 'default')
            data_provider_name = cfg.get('data_provider', connector_name)

            connector = self.connectors.get(connector_name)
            data_provider = self.data_providers.get(data_provider_name)

            if not connector or not data_provider:
                print(f"策略 {strategy_name} 缺少连接器或数据提供器")
                continue

            # 创建策略实例
            strategy = strategy_class(params=cfg.get('params', {}))
            await strategy.initialize(connector, data_provider)
            self.strategies[strategy_name] = strategy
            
            # 订阅WebSocket市场数据
            strategy_params = cfg.get('params', {})
            symbol = strategy_params.get('symbol')
            interval = strategy_params.get('interval', '1m')
            
            if symbol and connector:
                try:
                    await connector.subscribe_to_ohlcv(symbol, interval)
                    print(f"已订阅 {symbol} {interval} 的K线数据WebSocket")
                except Exception as e:
                    print(f"订阅WebSocket失败: {str(e)}")
            
            print(f"已加载策略: {strategy_name}")

    def _get_connector_class(self, exchange_type: str) -> Optional[Type[AsyncExchange]]:
        """获取连接器类"""
        connector_map = {
            'binance': AsyncBinanceExchange,
            # 可添加其他交易所连接器
        }
        return connector_map.get(exchange_type.lower())

    def _import_strategy_class(self, class_path: str) -> Optional[Type[AsyncBaseStrategy]]:
        """动态导入策略类"""
        try:
            module_name, class_name = class_path.rsplit('.', 1)
            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        except Exception as e:
            print(f"导入策略类失败 {class_path}: {str(e)}")
            return None

    async def start(self):
        """启动交易引擎"""
        if self.running:
            return

        self.running = True
        # 启动所有策略
        for name, strategy in self.strategies.items():
            await strategy.start()
            print(f"策略 {name} 已启动")

        # 启动引擎主循环
        self._task = asyncio.create_task(self._engine_loop())
        print("交易引擎已启动")

    async def _engine_loop(self):
        """引擎主循环"""
        while self.running:
            # 检查所有策略状态
            for name, strategy in self.strategies.items():
                if not strategy._running:
                    print(f"策略 {name} 已停止，尝试重启...")
                    await strategy.start()
            await asyncio.sleep(5)  # 每5秒检查一次

    async def stop(self):
        """停止交易引擎"""
        if not self.running:
            return

        self.running = False
        # 停止所有策略
        for name, strategy in self.strategies.items():
            await strategy.stop()
            print(f"策略 {name} 已停止")

        # 关闭所有连接器
        for name, connector in self.connectors.items():
            await connector.close()
            print(f"连接器 {name} 已关闭")

        # 取消引擎主循环任务
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        print("交易引擎已停止")

    async def add_strategy(self, strategy_name: str, strategy_class: Type[AsyncBaseStrategy],
                          connector_name: str = 'default', data_provider_name: str = None,
                          params: Dict = None) -> bool:
        """动态添加策略"""
        data_provider_name = data_provider_name or connector_name
        connector = self.connectors.get(connector_name)
        data_provider = self.data_providers.get(data_provider_name)

        if not connector or not data_provider:
            return False

        strategy = strategy_class(params=params or {})
        await strategy.initialize(connector, data_provider)
        self.strategies[strategy_name] = strategy
        await strategy.start()
        print(f"已动态添加策略: {strategy_name}")
        return True

    async def remove_strategy(self, strategy_name: str) -> bool:
        """移除策略"""
        strategy = self.strategies.get(strategy_name)
        if not strategy:
            return False

        await strategy.stop()
        del self.strategies[strategy_name]
        print(f"已移除策略: {strategy_name}")
        return True

    async def __aenter__(self):
        await self.initialize()
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop()
        return False


# 命令行启动入口
async def main():
    import sys
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = 'config/trading.json'

    # 加载配置文件
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {str(e)}")
        return

    # 启动交易引擎
    engine = TradingEngine(config)
    try:
        await engine.initialize()
        await engine.start()
        # 保持运行
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("收到停止信号")
    finally:
        await engine.stop()

if __name__ == '__main__':
    asyncio.run(main())