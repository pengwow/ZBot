#!/usr/bin/env python3
import time
from nicegui import ui, binding
import httpx
from contextlib import contextmanager

from data_view import download_data_view
from data import DownloadData



@contextmanager
def disable(button: ui.button):
    button.disable()
    try:
        yield
    finally:
        button.enable()


async def get_slow_response(button: ui.button) -> None:
    with disable(button):
        async with httpx.AsyncClient() as client:
            response = await client.get('https://httpbin.org/delay/1', timeout=5)
            ui.notify(f'Response code: {response.status_code}')


@ui.page('/')
def main_page():
    download_data = DownloadData()
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
    with ui.tab_panels(tabs, value='A').classes('w-full'):
        with ui.tab_panel('图表'):
            ui.label('Content of 图表 ')
        with ui.tab_panel('日志'):
            log = ui.log(max_lines=1000).classes('w-full h-1500')
        with ui.tab_panel('回测'):
            ui.label('Content of 回测')
        with ui.tab_panel('数据'):
            download_data_view(download_data)
        with ui.tab_panel('配置'):
            ui.label('Content of E')


# with ui.left_drawer().classes('bg-blue-100') as left_drawer:
#     ui.label('Side menu')

# with ui.page_sticky(position='bottom-right', x_offset=20, y_offset=20):
#     ui.button(on_click=footer.toggle, icon='contact_support').props('fab')


ui.run()
