# app.py (Google Sheets API対応版)

import streamlit as st
import pandas as pd
# plotly.express と streamlit.components.v1 は現在このファイルでは使われていませんが、念のため残しておきます
import plotly.express as px
import streamlit.components.v1 as components
import base64

from pathlib import Path
from datetime import datetime
from astral.sun import sun
from astral import LocationInfo
import pytz 

from modules import form, tracker, ranking

# 必要なライブラリを追加
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from google.oauth2.service_account import Credentials

# --- データ読み込み関数をGoogleスプレッドシート対応に全面改訂 ---
@st.cache_data(ttl=60) # 60秒間は結果をキャッシュして、APIへのアクセスを減らす
def load_data(sheet_name):
    try:
        # StreamlitのSecretsから認証情報を読み込む
        scopes = ['https://www.googleapis.com/auth/spreadsheets',
                  'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
        client = gspread.authorize(creds)
        
        # スプレッドシート名でファイルを開き、最初のシートを取得
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.worksheet("シート1") # あなたのシート名が違う場合は修正してください

        # シートの内容をPandas DataFrameとして読み込む
        df = get_as_dataframe(worksheet)
        
        # 不要な行や列を削除する前処理
        df.dropna(how='all', inplace=True)
        if not df.empty:
            df.dropna(subset=[df.columns[0]], inplace=True)
        
        # 日付列をdatetime型に変換
        if '記録日' in df.columns:
            df['記録日'] = pd.to_datetime(df['記録日'], errors='coerce')

        return worksheet, df # worksheetオブジェクトも後で使うので返す

    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"スプレッドシート '{sheet_name}' が見つかりません。名前が正しいか、サービスアカウントに共有されているか確認してください。")
        return None, pd.DataFrame()
    except Exception as e:
        st.error(f"データの読み込み中にエラーが発生しました: {e}")
        return None, pd.DataFrame()


# --- タイムゾーン・テーマ設定 (変更なし) ---
tokyo_tz = pytz.timezone("Asia/Tokyo")
now = datetime.now(tokyo_tz)
city = LocationInfo("Tokyo", "Japan", "Asia/Tokyo", 35.6895, 139.6917)
s = sun(city.observer, date=now.date(), tzinfo=tokyo_tz)
sunrise = s["sunrise"]
sunset = s["sunset"]

if sunrise <= now <= sunset:
    background = "#ffffff"
    text_color = "#000000"
    accent = "#2196f3"
else:
    background = "#121212"
    text_color = "#ffffff"
    accent = "#2196f3"

# --- ページ設定 (変更なし) ---
st.set_page_config(
    page_title="UEC 筋トレトラッカー",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Base64エンコード関数 (変更なし) ---
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    return f"data:image/png;base64,{encoded}"

# --- st.session_stateの初期化処理を修正 ---
if 'df' not in st.session_state:
    # "training_log_sheet" の部分は、あなたが作成したGoogleスプレッドシートの名前に置き換えてください
    worksheet, df = load_data("training_log_sheet") 
    st.session_state.worksheet = worksheet
    st.session_state.df = df

# --- カスタムスタイルとヘッダー ---
image_data = get_base64_image("uecmuscle_icon.png")
# この部分はUIデザインに必要なので、コメントアウトを解除してください
st.markdown(f"""
    <style>
        [data-testid="stAppViewContainer"] {{
            background-color: {background};
            color: {text_color};
        }}
        [data-testid="stMarkdownContainer"] {{
            color: {text_color};
        }}
        [data-testid="stForm"] {{
            padding: 0px;
        }}
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
        /* ... (他のCSSは省略) ... */
    </style>
    <div class="blue-header">
        <div style="display: flex; align-items: center; justify-content: center; gap: 16px;">
            <img src="{image_data}" alt="logo" width="80" height="80">
            <span>UEC 筋トレサークル</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- タブの表示部分を修正 ---
tab1, tab2, tab3 = st.tabs(["記録入力", "トラッカー", "ランキング"])

with tab1:
    # formモジュールに、worksheetオブジェクトを渡す
    form.run(st.session_state.df, st.session_state.get('worksheet'))
with tab2:
    tracker.run(st.session_state.df)
with tab3:
    ranking.run(st.session_state.df)