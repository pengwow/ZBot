import streamlit as st

pg = st.navigation([
    st.Page("chat_page.py", title="图表", icon="📊"),
    st.Page("data_page.py", title="数据下载", icon="💾"),
])
pg.run()