import plotly.graph_objects as go
import pandas as pd

# 创建蜡烛图
def create_candlestick_chart(df: pd.DataFrame) -> go.Figure:
    print(df.columns)
    # 自定义悬停模板
    hovertext = (
        f"日期: {df['Date'].iloc[-1]}<br>"
        f"开盘: {df['Open'].iloc[-1]}<br>"
        f"最高: {df['High'].iloc[-1]}<br>"
        f"最低: {df['Low'].iloc[-1]}<br>"
        f"收盘: {df['Close'].iloc[-1]}<br>"
        f"成交量: {df['Volume'].iloc[-1]}<br>"
    )
    # 创建蜡烛图
    fig = go.Figure(data=[go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing_line_color='green',
        decreasing_line_color='red',
        hoverinfo='text',
        hovertext=hovertext,
    )])
    # 添加标签
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Close'],
        mode='text',
        text='开多',
        textposition='top center',
        marker=dict(size=10, color='green'),
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Close'],
        mode='text',
        text='开空',
        textposition='bottom center',
        marker=dict(size=10, color='red'),
        showlegend=False,
    ))
    # 格式化时间轴
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1天", step="day", stepmode="backward"),
                dict(count=7, label="1周", step="day", stepmode="backward"),
                dict(count=1, label="1月", step="month", stepmode="backward"),
                dict(count=6, label="6月", step="month", stepmode="backward"),
                dict(count=1, label="1年", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    
    fig.update_xaxes(tickformat='%m.%d %H:%M')
    # # 添加注释
    # fig.add_annotation(
    #     x=df['Date'].iloc[-1],
    #     y=df['Close'].iloc[-1],
    #     text=f"最后价格: {df['Close'].iloc[-1]:.2f}",
    #     showarrow=True,
    #     arrowhead=1,
    #     ax=0,
    #     ay=-40,
    #     bordercolor='red',
    #     borderwidth=1,
    #     borderpad=4,
    #     bgcolor='white',
    #     opacity=0.8,
    # )

    # 更新布局
    fig.update_layout(
        title=f'价格 (最后价格: {df["Close"].iloc[-1]:.2f})',
        xaxis_title='时间',
        yaxis_title='价格',
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        height=600,
        width=800
    )

    # 设置Y轴范围，添加一些边距
    y_min = df['Low'].min() * 0.99
    y_max = df['High'].max() * 1.01
    fig.update_yaxes(range=[y_min, y_max])

    return fig