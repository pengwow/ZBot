import os
import json
from datetime import datetime, timedelta
import shutil
from flask import Flask
import dash
from dash import Dash, html, dcc, Output, Input, callback, ctx
import feffery_antd_components as fac
import feffery_utils_components as fuc
from zbot.common.config import read_config
from zbot.exchange.exchange import ExchangeFactory


class App(Dash):
    def __init__(self, *arg, **kwarg):
        super().__init__(*arg, **kwarg)
        self._symbols = None
        self.config_data = self.load_init_data()
        self.exchange = self.init_exchange()
        self.layout = html.Div(
            [
                dcc.Location(id="url"),
                dcc.Store(id='global-storage'),  # 全局存储组件
                fac.Fragment(id='global-message-container'),  # 注入全局消息提示容器
                html.Div(
                    [
                        fuc.FefferyDiv(
                            [
                                # 利用fac中的网格系统进行页首元素的排布
                                fac.AntdRow(
                                    [
                                        # logo+标题
                                        fac.AntdCol(
                                            fac.AntdSpace(
                                                [
                                                    fac.AntdImage(
                                                        src=dash.get_asset_url(
                                                            'logo.png'
                                                        ),
                                                        preview=False,
                                                        style={
                                                            'height': 54, 'width': 54}
                                                    ),
                                                    fac.AntdText(
                                                        'ZBot',
                                                        strong=True,
                                                        style={
                                                            'fontSize': 32
                                                        }
                                                    )
                                                ]
                                            ),
                                            flex='none',
                                            style={
                                                'height': 'auto'
                                            }
                                        ),

                                        # 菜单栏
                                        fac.AntdCol(
                                            fac.AntdMenu(
                                                menuItems=[
                                                    {
                                                        'component': 'Item',
                                                        'props': {
                                                            'key': page['name'],
                                                            'title': page['name'],
                                                            'icon': page['icon'],
                                                            'href': page['relative_path']
                                                        }
                                                    }
                                                    for page in dash.page_registry.values()
                                                ],
                                                mode='horizontal',
                                                style={
                                                    'maxWidth': 600,
                                                    'borderBottom': 'none'
                                                }
                                            ),
                                            flex='none',
                                            style={
                                                'height': 'auto'
                                            }
                                        )
                                    ],
                                    align='middle',
                                    justify='space-between',
                                    wrap=False,  # 阻止自动换行
                                    style={
                                        'height': '100%'
                                    }
                                )
                            ],
                            style={
                                'height': 64,
                                'padding': '0 25px',
                                'background': 'white',
                                'borderBottom': '1px solid #f0f0f0'
                            }
                        ),

                    ]
                ),
                html.Div(id="page-content"),
                dash.page_container
            ],
        )

    def load_init_data(self):
        data = read_config()
        print(f"加载全局配置")

        return data

    def init_exchange(self):
        self.exchange = ExchangeFactory.create_exchange(self.config_data['exchange']['name'])
        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            print(f'创建数据目录: {data_dir}')

        # 缓存文件路径
        cache_file = os.path.join(data_dir, 'exchange_cache.json')
        self._symbols = None

        try:
            # 检查缓存文件是否存在且未过期（1天）
            if os.path.exists(cache_file):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
                if datetime.now() - file_mtime < timedelta(days=1):
                    # 读取缓存文件
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    self._symbols = cache_data.get('symbols')
                    print(f'使用缓存数据，缓存时间: {file_mtime}')

            # 如果没有缓存或缓存过期，则从交易所获取数据
            if self._symbols is None:

                self._symbols = self.exchange.symbols
                print(f'从交易所获取数据成功，共{len(self._symbols)}个交易对')

                # 写入缓存文件
                with open(cache_file, 'w') as f:
                    json.dump({'symbols': self._symbols, 'update_time': datetime.now().isoformat()}, f, indent=2)
                print(f'数据已缓存至: {cache_file}')

        except Exception as e:
            print(f"初始化交易所失败: {e}")
            self.exchange = None
            self._symbols = None
        return self.exchange

    @property
    def symbols(self):
        return self._symbols


def run_web_ui(host=None, port=None):
    # 创建 Flask 应用
    # server = Flask(__name__)
    app = App(
        name=__name__,
        # server=server,  # 将 Flask 应用实例传递给 Dash
        assets_folder='assets',  # 对应资源存放目录,可下载后解压到这里
        title='ZBot',
        update_title='Loading...',
        use_pages=True,
        pages_folder='pages',  # 对应的pages存放的目录
        suppress_callback_exceptions=True  # 异常不会触发框架级错误处理
    )

    ctx.global_vars = {
        "config_data": app.config_data,  # 全局配置数据
        "exchange": app.exchange,  # 全局交易所实例
        "symbols": app.symbols,  # 全局交易对
    }
    app.run(host=host,
            port=port,
            debug=True,
            # use_reloader=False # 禁用重载器避免双重加载
            )  


if __name__ == '__main__':
    run_web_ui('127.0.0.1', 8080)
