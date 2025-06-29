#!/usr/bin/env python3
from nicegui import ui

with ui.header().classes(replace='row items-center') as header:
    # ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
    with ui.tabs() as tabs:
        ui.tab('图表')
        ui.tab('日志')
        ui.tab('回测')
        ui.tab('数据')
        ui.tab('配置')


with ui.footer(value=False) as footer:
    ui.label('Footer')

# with ui.left_drawer().classes('bg-blue-100') as left_drawer:
#     ui.label('Side menu')

# with ui.page_sticky(position='bottom-right', x_offset=20, y_offset=20):
#     ui.button(on_click=footer.toggle, icon='contact_support').props('fab')

with ui.tab_panels(tabs, value='A').classes('w-full'):
    with ui.tab_panel('图表'):
        ui.label('Content of 图表 ')
    with ui.tab_panel('日志'):
        log = ui.log(max_lines=1000).classes('w-full h-1500')
    with ui.tab_panel('回测'):
        ui.label('Content of 回测')
    with ui.tab_panel('数据'):
        exchange = ['binance', 'okx']
        symbol = ['BTC/USDT', 'ETH/USDT', 'DOGE/USDC']
        with ui.row():
            ui.select(exchange, multiple=False,
                      value=exchange[0], label='交易所').classes('w-64')
            ui.select(symbol, multiple=True, with_input=True,
                      value=symbol[0], label='货币对').classes('w-64').props('use-chips')
            ui.select(['1m', '3m', '5m', '15m', '30m', '1h', '4h',
                      '1d', '1s'], value='1h', label='时间间隔').classes('w-64')
        start_time = ''
        end_time = ''
        with ui.row():
            with ui.input('开始时间') as date:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(date):
                        with ui.row().classes('justify-end'):
                            ui.button('确定', on_click=menu.close).props('flat')
                with date.add_slot('append'):
                    ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
            with ui.input('结束时间') as date:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(date):
                        with ui.row().classes('justify-end'):
                            ui.button('确定', on_click=menu.close).props('flat')
                with date.add_slot('append'):
                    ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
    with ui.tab_panel('配置'):
        ui.label('Content of E')

ui.run()
