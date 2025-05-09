import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
from modules import show_form, show_tracker


st.set_page_config(
    page_title="UEC 筋トレトラッカー",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# st.markdown("""
#     <style>
#         section[data-testid="stSidebar"] {
#             display: none !important;
#         }
#     </style>
# """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📝 記録入力","📊 トラッカー"])

with tab1:
    show_form()

with tab2:
    show_tracker()