import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
import base64

from pathlib import Path
from datetime import datetime
from astral.sun import sun
from astral import LocationInfo
import pytz 

from modules import form, tracker, menu_gen


# --- 定数定義 ---
DATA_FILE = "data/training_log.csv"

# --- データ読み込み関数 ---
def load_data(filepath):
    try:
        # Googleスプレッドシートの形式に合わせて読み込み
        df = pd.read_csv(filepath, header=0)
        # タイムスタンプ列などをここで前処理しても良い
        df['記録日'] = pd.to_datetime(df['記録日'], errors='coerce')
        return df
    except FileNotFoundError:
        # ファイルがない場合は、空のDataFrameを作成
        st.error(f"{filepath} が見つかりません。Step 1 を実行してください。")
        return pd.DataFrame() # 空のDataFrameを返す


# タイムゾーンを明示的に指定
tokyo_tz = pytz.timezone("Asia/Tokyo")
now = datetime.now(tokyo_tz)

city = LocationInfo("Tokyo", "Japan", "Asia/Tokyo", 35.6895, 139.6917)
s = sun(city.observer, date=now.date(), tzinfo=tokyo_tz)

sunrise = s["sunrise"]
sunset = s["sunset"]

# モードの切り替え
if sunrise <= now <= sunset:
    background = "#ffffff"
    text_color = "#000000"
    accent = "#2196f3"
    mode_label = "デイモード"
    # background = "#121212"
    # text_color = "#ffffff"
    # accent = "#2196f3"
    # mode_label = "ナイトモード"
else:
    background = "#121212"
    text_color = "#ffffff"
    accent = "#2196f3"
    mode_label = "ナイトモード"

# ページ設定
st.set_page_config(
    page_title="UEC 筋トレトラッカー",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    return f"data:image/png;base64,{encoded}"
image_data = get_base64_image("uecmuscle_icon.png")



# --- st.session_stateの初期化 ---
# アプリのセッション中にデータを保持するために使用
if 'df' not in st.session_state:
    st.session_state.df = load_data(DATA_FILE)


# --- ↓↓↓ ここからデバッグコードを追加 ↓↓↓ ---
#st.header("【デバッグ情報】")
#st.write("読み込まれたDataFrameの全データ:")
#st.dataframe(st.session_state.df)

# '記入者名'列が存在するか確認してからunique()を呼び出す
#if '記入者名' in st.session_state.df.columns:
#    st.write("DataFrameから取得したユニークな記入者リスト:")
#    st.write(st.session_state.df['記入者名'].unique())
#else:
#    st.write("DataFrameに「記入者名」という列が見つかりません。")
#
#st.markdown("---") # 見やすくするための区切り線
# --- ↑↑↑ デバッグここまで ↑↑↑ ---



# --- カスタムスタイルとヘッダー (変更なし) ---
image_data = get_base64_image("uecmuscle_icon.png")
#st.markdown(f"""...""", unsafe_allow_html=True)
# ちょんちょんいらないよね？？

# カスタムスタイルとヘッダー
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
        
        /* タブのスタイル */
            div[data-baseweb="tab-list"] {{
            display: flex !important;
            justify-content: center !important;
            gap: 60px;
            border-bottom: 2px solid #ddd;
            padding-bottom: 8px;
            margin-bottom: 16px;
        }}
        div[role="tab"] {{
            font-size: 20px !important;
            font-weight: 600 !important;
            background: none !important;
            border: none !important;
            padding: 8px 16px !important;
            border-radius: 0 !important;
            color: #444 !important;
            box-shadow: none !important;
            position: relative;
            transition: color 0.3s ease;
            cursor: pointer;
        }}
        div[role="tab"][aria-selected="true"] {{
            color: {accent} !important;
            font-weight: 700 !important;
        }}
        div[role="tab"][aria-selected="true"]::after {{
            content: "";
            position: absolute;
            bottom: -10px;
            left: 0;
            right: 0;
            height: 3px;
            background-color: {accent};
            border-radius: 3px;
        }}

                .card {{
            background-color: #fff;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            margin-top: 24px;
            margin-bottom: 24px;
        }}

        .form-wrapper {{
            max-width: 800px;
            margin: 0 auto;
        }}

    </style>
    <div class="blue-header">
        <div style="display: flex; align-items: center; justify-content: center; gap: 16px;">
            <img src="{image_data}" alt="logo" width="80" height="80">
            <span>UEC 筋トレサークル</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# タブの表示
tab1, tab2, tab3 = st.tabs(["記録入力", "トラッカー", "メニュー生成"])

with tab1:
    # formモジュールに、データフレームとファイルパスを渡す
    form.run(st.session_state.df, DATA_FILE)
with tab2:
    # trackerモジュールに、データフレームを渡す
    tracker.run(st.session_state.df)
with tab3:
    # menu_genモジュールを呼び出す
    menu_gen.render()