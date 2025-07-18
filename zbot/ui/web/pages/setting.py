from re import S
import dash
from dash import html, dcc, callback, Input, Output
import feffery_utils_components as fuc
import feffery_antd_components as fac
from zbot.common.config import read_config

# 注册pages
dash.register_page(__name__, icon='antd-setting', name='配置')

class Setting(object):
    def __init__(self) -> None:
        self.config = read_config()
        self.exchange = self.config['exchange']['name']
        self.exchange_config = self.config['exchange'][self.exchange]
        self.layout = html.Div(
            [
                fuc.FefferyDiv(
                    [
                        
                        fac.AntdCenter(
                            fac.AntdForm(
                                [
                                    fac.AntdDivider('交易商'),
                                    fac.AntdFormItem(
                                        fac.AntdSelect(id='exchange_form', options=['binance']),
                                        label=f'交易商', hasFeedback=True
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdSelect(id='trade_mode_form', options=['spot', 'future']),
                                        label=f'交易模式', hasFeedback=True
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(
                                            id='api_key_form', mode='password'),
                                        label=f'api key', hasFeedback=True
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(
                                            id='secret_key_form', mode='password'),
                                        label=f'secret key', hasFeedback=True
                                    ),
                                    fac.AntdDivider('服务端'),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id='host_form'),
                                        label=f'host', hasFeedback=True
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInput(id='port_form'),
                                        label=f'port', hasFeedback=True
                                    ),
                                ],
                                id='setting_form',
                                enableBatchControl=True,
                                layout='vertical',
                                values={
                                    'exchange_form': 'binance',
                                    'trade_mode_form': self.exchange_config['trading_mode'],
                                    'api_key_form': self.exchange_config['api_key'],
                                    'secret_key_form': self.exchange_config['secret_key'],
                                    'host_form': self.config['server']['host'],
                                    'port_form': str(self.config['server']['port']),
                                }
                            ),
                        )


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


_setting = Setting()
layout = _setting.layout
