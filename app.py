# app.py (最終完成版 - Google Sheets API連携)

import streamlit as st
import pandas as pd
import base64
from pathlib import Path
from datetime import datetime
import pytz 
from astral.sun import sun
from astral import LocationInfo

# 外部サービス連携用のライブラリ
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from google.oauth2.service_account import Credentials

# 自作モジュール
from modules import form, tracker, ranking

# --- データ読み込み関数 ---
@st.cache_data(ttl=60)
def load_data(sheet_name):
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.worksheet("シート1")
        df = get_as_dataframe(worksheet)
        df.dropna(how='all', inplace=True)
        if not df.empty:
            df.dropna(subset=[df.columns[0]], inplace=True)
        if '記録日' in df.columns:
            df['記録日'] = pd.to_datetime(df['記録日'], errors='coerce')
        return worksheet, df
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"スプレッドシート '{sheet_name}' が見つかりません。名前が正しいか、サービスアカウントに共有されているか確認してください。")
        return None, pd.DataFrame()
    except Exception as e:
        st.error(f"データの読み込み中にエラーが発生しました: {e}")
        return None, pd.DataFrame()

# --- テーマ設定 ---
tokyo_tz = pytz.timezone("Asia/Tokyo")
now = datetime.now(tokyo_tz)
city = LocationInfo("Tokyo", "Japan", "Asia/Tokyo", 35.6895, 139.6917)
s = sun(city.observer, date=now.date(), tzinfo=tokyo_tz)
sunrise = s["sunrise"]
sunset = s["sunset"]

if sunrise <= now <= sunset:
    background = "#ffffff"; text_color = "#000000"; accent = "#2196f3"
else:
    background = "#ffffff"; text_color = "#000000"; accent = "#2196f3"

# --- ページ設定 ---
st.set_page_config(page_title="UEC 筋トレトラッカー", layout="wide", initial_sidebar_state="collapsed")

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# --- セッション管理 ---
if 'worksheet' not in st.session_state:
    worksheet, df = load_data("training_log_sheet") # ここはあなたのスプレッドシート名に
    st.session_state.worksheet = worksheet
    st.session_state.df = df

# --- UI描画 ---
image_data = get_base64_image("uecmuscle_icon.png")

# カスタムスタイルとヘッダー
st.markdown(f"""
    <style>
        /* 基本テーマ設定 */
        [data-testid="stAppViewContainer"] {{
            background-color: {background};
            color: {text_color};
        }}
        [data-testid="stForm"] {{
            padding: 0px;
        }}

        /* ヘッダーのデザイン */
        .blue-header {{
            background-color: {accent};
            padding: 16px 28px;
            color: white;
            font-size: 36px;
            font-weight: bold;
            border-radius: 0 0 8px 8px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.25);
            margin-bottom: 28px;
        }}
        
        /* st.radioをタブのように見せるためのCSS */
        div[role="radiogroup"] > label > div:first-child {{
            display: none;
        }}
        div[role="radiogroup"] > label {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            padding: 8px 24px;
            margin: 0;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
            color: {text_color};
        }}
        div[role="radiogroup"] input:checked + div {{
            font-weight: 700 !important;
            color: {accent} !important;
            border-bottom: 3px solid {accent};
        }}
        .tabs-container {{
            border-bottom: 2px solid #444;
            padding-bottom: 0px;
            margin-bottom: 28px;
            display: flex;
            justify-content: center;
            gap: 40px;
        }}
    </style>

    <div class="blue-header">
        <div style="display: flex; align-items: center; justify-content: center; gap: 16px;">
            <img src="data:image/png;base64,{image_data}" alt="logo" width="80" height="80">
            <span>UEC 筋トレサークル</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# st.radioを使ったナビゲーション
with st.container():
    _, center_col, _ = st.columns([1, 6, 1])
    with center_col:
        st.markdown('<div class="tabs-container">', unsafe_allow_html=True)
        active_tab = st.radio(
            "Navigation", 
            options=["記録入力", "トラッカー", "ランキング"],
            horizontal=True,
            label_visibility="collapsed",
            key="active_tab"
        )
        st.markdown('</div>', unsafe_allow_html=True)

# 選択されたタブに応じてコンテンツを表示
if st.session_state.active_tab == "記録入力":
    form.run(st.session_state.df, st.session_state.get('worksheet'))
elif st.session_state.active_tab == "トラッカー":
    tracker.run(st.session_state.df)
elif st.session_state.active_tab == "ランキング":
    ranking.run(st.session_state.df)