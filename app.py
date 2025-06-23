# app.py (読み込み専用・Googleフォーム連携版)

import streamlit as st
import pandas as pd
import base64
from pathlib import Path
from datetime import datetime
import pytz 
from astral.sun import sun
from astral import LocationInfo
import streamlit.components.v1 as components

# 外部サービス連携用のライブラリ
import gspread
from gspread_dataframe import get_as_dataframe
from google.oauth2.service_account import Credentials

# 自作モジュール (formはもう使いませんが、コメントアウトで残します)
# from modules import form
from modules import tracker, ranking

# --- データ読み込み関数 ---
@st.cache_data(ttl=60) # 1分間は結果をキャッシュする
def load_data(sheet_name, worksheet_name):
    """
    指定されたGoogleスプレッドシートからデータを読み込み、DataFrameとして返す。
    """
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)
        df = get_as_dataframe(worksheet)
        
        # --- データクリーニング処理 ---
        # 1. 全ての列が空の行を削除
        df.dropna(how='all', inplace=True)
        if not df.empty:
            # 2. 「記入者名」が空の行を削除する（こちらの方が安全）
            df.dropna(subset=['記入者名'], inplace=True)
        
        # 3. 日付列をdatetime型に変換
        if '記録日' in df.columns:
            df['記録日'] = pd.to_datetime(df['記録日'], errors='coerce')

        return df # DataFrameだけを返す

    except Exception as e:
        st.error(f"スプレッドシートの読み込み中にエラーが発生しました: {e}")
        return pd.DataFrame()

# --- テーマ設定 ---
tokyo_tz = pytz.timezone("Asia/Tokyo")
now = datetime.now(tokyo_tz)
city = LocationInfo("Tokyo", "Japan", "Asia/Tokyo", 35.6895, 139.6917)
s = sun(city.observer, date=now.date(), tzinfo=tokyo_tz)
sunrise = s["sunrise"]
sunset = s["sunset"]

# UIのライト/ダークモード設定
if sunrise <= now <= sunset:
    background = "#ffffff"; text_color = "#000000"; accent = "#2196f3"
else:
    # 現在は常にライトモードになるように設定
    background = "#ffffff"; text_color = "#000000"; accent = "#2196f3"

# --- ページ設定 ---
st.set_page_config(page_title="UEC 筋トレトラッカー", layout="wide", initial_sidebar_state="collapsed")

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# --- セッション管理 ---
if 'df' not in st.session_state:
    # ★★★ ここに、あなたのスプレッドシート名と、フォームの回答シート名を入力 ★★★
    df = load_data("training_log_sheet", "フォームの回答") # 例: "フォームの回答 1"
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
            text-align: center;
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
            color: #444; /* 非選択時の文字色を固定 */
        }}
        div[role="radiogroup"] input:checked + div {{
            font-weight: 700 !important;
            color: {accent} !important;
            border-bottom: 3px solid {accent};
        }}
        .tabs-container {{
            border-bottom: 2px solid #ddd; /* #444から変更 */
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
# st.session_stateに選択中のタブを保存
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "トラッカー"

# コンテナを使って中央揃え
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
    # --- ★★★ ここからが変更点 ★★★ ---
    st.subheader("Googleフォームから記録を入力してください")
    st.markdown("---")
    
    # ★★★ ここに、あなたのGoogleフォームの「共有可能なリンク」を貼り付け ★★★
    google_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdwu012eCGPirIy8ko6h61F4lF2S6sCUz30Sk3dGF1EWLwbMg/viewform?usp=preview" # 例
    st.link_button("Googleフォームを開いて記録する ↗", google_form_url, type="primary")
    
    st.info("💡 入力した内容は、1分程度でアプリに反映されます。")
    st.markdown("---")
    
    st.write("▼ フォームを直接表示することもできます")
    # 埋め込み用URLは、フォーム編集画面の「送信」ボタンから取得できます
    google_form_embed_url = google_form_url.replace("/viewform", "/viewform?embedded=true")
    components.iframe(src=google_form_embed_url, height=800, scrolling=True)
    
    # --- 以前の入力フォーム機能は、いつでも復活できるようにコメントアウト ---
    # from modules import form
    # form.run(st.session_state.df, st.session_state.get('worksheet'))
    
elif st.session_state.active_tab == "トラッカー":
    tracker.run(st.session_state.df)
elif st.session_state.active_tab == "ランキング":
    ranking.run(st.session_state.df)
