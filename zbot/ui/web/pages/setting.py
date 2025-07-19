from operator import call
from re import S
import dash
from dash import html, dcc, callback, Input, Output, State
import feffery_utils_components as fuc
import feffery_antd_components as fac
from sqlalchemy import values
from zbot.common.config import read_config, write_config

# 注册pages
dash.register_page(__name__, icon='antd-setting', name='配置')

config = read_config()
exchange = config['exchange']['name']
exchange_config = config['exchange'][exchange]


layout = html.Div(
    [
        fuc.FefferyDiv(
            [

                fac.AntdCenter(
                    fac.AntdForm(
                        [
                            fac.AntdDivider('交易商'),
                            fac.AntdFormItem(
                                fac.AntdSelect(
                                    id='exchange', options=['binance']),
                                label=f'交易商', hasFeedback=True
                            ),
                            fac.AntdFormItem(
                                fac.AntdSelect(id='trading_mode', options=[
                                    'spot', 'future']),
                                label=f'交易模式', hasFeedback=True
                            ),
                            fac.AntdFormItem(
                                fac.AntdInput(
                                    id='api_key'),
                                label=f'api key', hasFeedback=True
                            ),
                            fac.AntdFormItem(
                                fac.AntdInput(
                                    id='secret_key'),
                                label=f'secret key', hasFeedback=True
                            ),
                            fac.AntdFormItem(
                                fac.AntdInput(id='proxy_url'),
                                label=f'代理url', hasFeedback=True
                            ),
                            fac.AntdDivider('服务端'),
                            fac.AntdFormItem(
                                fac.AntdInput(id='host'),
                                label=f'host', hasFeedback=True
                            ),
                            fac.AntdFormItem(
                                fac.AntdInput(id='port'),
                                label=f'port', hasFeedback=True
                            ),
                            fac.AntdButton(
                                "保存", id="save_setting_button", block=True, type='primary')
                        ],
                        id='setting_form',
                        enableBatchControl=True,
                        layout='vertical',
                        values={
                            'exchange': 'binance',
                            'trading_mode': exchange_config['trading_mode'],
                            'api_key': exchange_config['api_key'],
                            'secret_key': exchange_config['secret_key'],
                            'proxy_url': exchange_config['proxy_url'],
                            'host': config['server']['host'],
                            'port': str(config['server']['port']),
                        }
                    ),
                ),

                html.Div(id='message-div'),
            ],
            shadow='always-shadow-light',
            style={
                'borderRadius': 8,
                'background': 'white',
                'padding': 24
            }
        ),
    ],
    style={
        'minHeight': 'calc(100vh - 64px)',
        'background': '#f0f2f5',
        'padding': 20
    }
)


@callback(
    Output('message-div', 'children'),
    Input("save_setting_button", "nClicks"),
    State("setting_form", "values"),
    prevent_initial_call=True  # 防止初始加载触发
)
def save_setting(n_clicks, values: dict):
    # 确保exchange配置部分存在并更新
    exchange = values.get('exchange', '')
    exchange_config['name'] = exchange  # 更新当前选中的交易所名称
    print(values)
    # 获取当前交易所的配置，不存在则创建新字典
    current_exchange_config = config['exchange'].get(exchange, {})
    current_exchange_config.update({
        'api_key': values.get('api_key'),
        'secret_key': values.get('secret_key'),
        'proxy_url': values.get('proxy_url'),
        'trading_mode': values.get('trading_mode'),
    })

    config['exchange'][exchange] = current_exchange_config
    server = {
        'host': values.get('host'),
        'port': int(values.get('port')),
    }
    config['server'] = server
    # 将更新后的配置数据写入 yaml 文件
    write_config(config)
    print(config)
    return fac.AntdMessage(content='保存成功', type='success')
