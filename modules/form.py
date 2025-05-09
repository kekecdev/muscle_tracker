import streamlit as st
import streamlit.components.v1 as components

def render():
    st.title("筋トレ記録入力フォーム")

    # Googleフォームの埋め込み
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSfWDTsokCezAqiM-VNxHv1rOpTiJJd7rCYUOqoTchg_3h4zdA/viewform?embedded=true"
    components.iframe(src=form_url, height=1000, scrolling=True)