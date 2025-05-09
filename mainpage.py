import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
from modules import show_form, show_tracker, show_menu_gen


st.set_page_config(
    page_title="UEC 筋トレトラッカー",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        .blue-header {
            background-color: #2196f3;
            padding: 12px 24px;
            color: white;
            font-size: 20px;
            font-weight: bold;
            border-radius: 0 0 8px 8px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }
    </style>
    <div class="blue-header">
        UEC 筋トレサークル
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 記録入力","📊 トラッカー","メニュー生成"])

with tab1:
    show_form()

with tab2:
    show_tracker()

with tab3:
    show_menu_gen()