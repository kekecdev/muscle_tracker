import streamlit as st
import pandas as pd
import plotly.express as px
import re
def load_data():
    CSV_URL = "https://docs.google.com/spreadsheets/d/1ZKqXthJSZf-So75Tb04Md3b2TbaGLcweZ5k-M_5sd38/export?format=csv&gid=1857163881"
    df = pd.read_csv(CSV_URL, skip_blank_lines=True)
    # print(df.columns)
    df = df.dropna(how='all', axis=0)
    # # df['date'] = pd.to_datetime(df['date'], errors='coerce')
    # df = df.dropna(subset=['date'])
    return df

# アプリ実行のたびに読み直される
df = load_data()
df = df.dropna(how='all', axis=0)
df = df.fillna(0,axis=0)
df = df.rename(columns={
    'タイムスタンプ': 'timestamp',
    '記入者名': 'name',
    '記録日': 'date',
    'ベンチプレス(kg × 回数)': 'bench_press',
    'デッドリフト(kg × 回数)': 'deadlift',
    'スクワット(kg × 回数)': 'squat',
    'ラットプルダウン(kg × 回数)': 'latpulldown',
    '懸垂(回数)': 'chinup',
    'マシンショルダープレス(kg × 回数)': 'shoulder_press',
    'レッグプレス(kg × 回数)': 'leg_press',
    '45°レッグプレス(kg × 回数)': 'leg_press_45',
    'メールアドレス': 'email',
    'スコア': 'score',
})
df = df.drop(columns=['timestamp'], axis=1)
df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d', errors='coerce')
def parse_kg_count(value):
    """'50-2' → (50, 2)、'0' や '5' → (0, 5)"""
    if isinstance(value, str) and '-' in value:
        try:
            kg, count = value.split('-')
            return int(kg), int(count)
        except:
            return 0, 0
    try:
        # 懸垂(回数)など → kg=0, count=value
        return 0, int(value)
    except:
        return 0, 0

def apply_parsing_after_rename(df):
    target_columns = [
        'bench_press',
        'deadlift',
        'squat',
        'latpulldown',
        'chinup',               # 懸垂（回数のみ）
        'shoulder_press',
        'leg_press',
        'leg_press_45'
    ]
    
    for col in target_columns:
        df[[f"{col}_kg", f"{col}_count"]] = df[col].apply(
            lambda x: pd.Series(parse_kg_count(x))
        )
    return df

df = apply_parsing_after_rename(df)
def estimate_1rm(weight, reps):
    """Epley式による推定1RM: weight × (1 + reps / 30)"""
    return weight * (1 + reps / 30)

def add_estimated_1rm(df):
    target_columns = [
        'bench_press',
        'deadlift',
        'squat',
        'latpulldown',
        'shoulder_press',
        'leg_press',
        'leg_press_45'
    ]
    
    for col in target_columns:
        kg_col = f"{col}_kg"
        rep_col = f"{col}_count"
        est_col = f"{col}_1rm"
        df[est_col] = df.apply(
            lambda row: estimate_1rm(row[kg_col], row[rep_col]), axis=1
        )
    return df
df = add_estimated_1rm(df)


# # ——— ② 種目リスト ———
exercises = [
    'bench_press',
    'deadlift',
    'squat',
    'latpulldown',
    'chinup',               # 懸垂（回数のみ）
    'leg_press',
    'leg_press_45',
    'shoulder_press'
]

print(df['date'].min())
# ——— ③ サイドバー：フィルタ設定 ———
st.sidebar.title("フィルタ")

# 記入者・メールアドレスフィルタ
authors = sorted(df['name'].dropna().unique())
selected_authors = st.sidebar.multiselect("記入者を選択", authors, default=authors)
# 英語 → 日本語の変換辞書
exercise_labels = {
    'bench_press': 'ベンチプレス',
    'deadlift': 'デッドリフト',
    'squat': 'スクワット',
    'latpulldown': 'ラットプルダウン',
    'chinup': '懸垂',
    'leg_press': 'レッグプレス',
    'leg_press_45': '45°レッグプレス',
    'shoulder_press': 'マシンショルダープレス'
}

# 日本語 → 英語の逆引き辞書を作成
exercise_labels_reverse = {v: k for k, v in exercise_labels.items()}

# サイドバーに日本語で選択肢を表示
selected_japanese = st.sidebar.selectbox("種目を選択", list(exercise_labels.values()))

# 内部処理では英語キーを使用
exercise = exercise_labels_reverse[selected_japanese]

start_date, end_date = st.sidebar.date_input(
    "表示期間",
    value=[
        df['date'].min().to_pydatetime(),
        df['date'].max().to_pydatetime()
    ]
)

# ——— ④ フィルタを適用 ———
mask = (
    df['name'].isin(selected_authors) &
    (df['date'] >= pd.to_datetime(start_date)) &
    (df['date'] <= pd.to_datetime(end_date))
)
dff = df.loc[mask].copy()



# # ——— ⑦ メイン画面 ———
st.title("UEC 筋トレサークル トラッカー")

st.markdown(f"""
- **記入者**：{', '.join(selected_authors)}  
- **種目**：{selected_japanese}
- **期間**：{start_date}～{end_date}  
- **データ件数**：{len(dff)} 件
""")

with st.expander("データプレビュー"):
    dff_display = dff[[
        'name', 'date',
        f'{exercise}_kg', f'{exercise}_count',
        f'{exercise}_1rm' if exercise != 'chinup' else f'{exercise}_count',
        'score'
    ]].rename(columns={
        f'{exercise}_kg': '重量',
        f'{exercise}_count': '回数',
        f'{exercise}_1rm': '推定1RM',
        'score': 'スコア',
        'name': '記入者',
        'date': '記録日'
    }) if exercise != 'chinup' else dff[[
        'name',  'date',
        f'{exercise}_count', 'score'
    ]].rename(columns={
        f'{exercise}_count': 'reps',
        'score': 'スコア',
        'name': '記入者',
        'date': '記録日'       
    })
    st.dataframe(dff_display)

# ⑧ グラフ表示
if exercise != "chinup":
    st.subheader("重量推移")
    fig_w = px.line(
        dff, x='date', y=f'{exercise}_kg', markers=True,
        labels={'date': '日付', f'{exercise}_kg': '重量(kg)'}
    )
    fig_w.update_xaxes(rangeslider_visible=True)
    st.plotly_chart(fig_w, use_container_width=True)

    
    st.subheader("推定1RM推移")
    fig_1rm = px.line(
        dff, x='date', y=f'{exercise}_1rm', markers=True,
        labels={'date': '日付', f'{exercise}_1rm': '推定1RM(kg)'}
    )
    fig_1rm.update_xaxes(rangeslider_visible=True)
    st.plotly_chart(fig_1rm, use_container_width=True)
else:
    st.subheader("回数推移")
    fig_r = px.line(
        dff, x='date', y=f'{exercise}_count', markers=True,
        labels={'date': '日付', f'{exercise}_count': '回数'}
    )
    fig_r.update_xaxes(rangeslider_visible=True)
    st.plotly_chart(fig_r, use_container_width=True)

# # 生データ表示
# with st.expander("▶️ 生データプレビュー"):
#     st.dataframe(dff[[
#         'タイムスタンプ','記入者名','メールアドレス','記録日',
#         exercise,'weight','reps','est_1rm','スコア'
#     ]])

# # ——— ⑧ グラフ表示 ———
# if exercise != "懸垂(回数)":
#     st.subheader("重量推移")
#     fig_w = px.line(
#         dff, x='記録日', y='weight', markers=True,
#         labels={'記録日':'日付','weight':'重量(kg)'}
#     )
#     fig_w.update_xaxes(rangeslider_visible=True)
#     st.plotly_chart(fig_w, use_container_width=True)

#     st.subheader("推定1RM推移")
#     fig_1rm = px.line(
#         dff, x='記録日', y='est_1rm', markers=True,
#         labels={'記録日':'日付','est_1rm':'推定1RM(kg)'}
#     )
#     fig_1rm.update_xaxes(rangeslider_visible=True)
#     st.plotly_chart(fig_1rm, use_container_width=True)
# else:
#     st.subheader("回数推移")
#     fig_r = px.line(
#         dff, x='記録日', y='reps', markers=True,
#         labels={'記録日':'日付','reps':'回数'}
#     )
#     fig_r.update_xaxes(rangeslider_visible=True)
#     st.plotly_chart(fig_r, use_container_width=True)

# # ——— ⑨ スコア分布（例） ———
# st.subheader("スコア分布")
# fig_s = px.histogram(
#     dff, x='スコア',
#     nbins=20, labels={'スコア':'スコア'}
# )
# st.plotly_chart(fig_s, use_container_width=True)