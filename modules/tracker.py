import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1ZKqXthJSZf-So75Tb04Md3b2TbaGLcweZ5k-M_5sd38/export?format=csv&gid=1857163881"
    df = pd.read_csv(url)
    df = df.dropna(how='all')
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
        'メールアドレス': 'email'
    })
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df[df['date'] >= pd.to_datetime("2025-04-01")]
    df = df.fillna(0)
    return df

def parse_kg_count(value):
    if isinstance(value, str) and '-' in value:
        try:
            kg, rep = value.split('-')
            return int(kg), int(rep)
        except:
            return 0, 0
    try:
        return 0, int(value)
    except:
        return 0, 0

def estimate_1rm(weight, reps):
    return weight * (1 + reps / 30)

def render():
    st.title("📊 トラッカー")

    df = load_data()

    # 重量・回数に分解
    for col in ['bench_press', 'deadlift', 'squat', 'latpulldown', 'chinup', 'shoulder_press', 'leg_press', 'leg_press_45']:
        df[[f"{col}_kg", f"{col}_count"]] = df[col].apply(lambda x: pd.Series(parse_kg_count(x)))
        if col != 'chinup':
            df[f"{col}_1rm"] = df.apply(lambda row: estimate_1rm(row[f"{col}_kg"], row[f"{col}_count"]), axis=1)

    # フィルター UI（本体エリア）
    st.subheader("🔎 フィルタ")
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_authors = st.multiselect("記入者を選択", df['name'].dropna().unique().tolist())

    with col2:
        exercise_labels = {
            'bench_press': 'ベンチプレス',
            'deadlift': 'デッドリフト',
            'squat': 'スクワット',
            'latpulldown': 'ラットプルダウン',
            'chinup': '懸垂',
            'shoulder_press': 'マシンショルダープレス',
            'leg_press': 'レッグプレス',
            'leg_press_45': '45°レッグプレス',
        }
        exercise_labels_reverse = {v: k for k, v in exercise_labels.items()}
        selected_jp = st.selectbox("種目を選択", list(exercise_labels.values()))
        selected_ex = exercise_labels_reverse[selected_jp]

    with col3:
        start_date, end_date = st.date_input("期間を選択", [df['date'].min(), df['date'].max()])

    # データフィルタリング
    mask = (
        df['name'].isin(selected_authors) &
        (df['date'] >= pd.to_datetime(start_date)) &
        (df['date'] <= pd.to_datetime(end_date))
    )
    dff = df.loc[mask]

    # データ表示
    st.markdown(f"**データ件数**: {len(dff)}")
    st.dataframe(dff[['name', 'date', f'{selected_ex}_kg', f'{selected_ex}_count']], use_container_width=True)

    # グラフ表示
    if selected_ex != "chinup":
        st.subheader("重量推移")
        fig = px.line(dff, x='date', y=f'{selected_ex}_kg', markers=True)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("推定1RM推移")
        fig2 = px.line(dff, x='date', y=f'{selected_ex}_1rm', markers=True)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.subheader("回数推移")
        fig = px.line(dff, x='date', y=f'{selected_ex}_count', markers=True)
        st.plotly_chart(fig, use_container_width=True)