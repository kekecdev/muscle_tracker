import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

'''
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

'''

def parse_kg_count(value):
    if isinstance(value, str) and '-' in value:
        try:
            kg, rep = value.split('-')
            return float(kg), int(rep)
        except:
            return 0, 0
    try:
        return 0, int(value)
    except:
        return 0, 0

def estimate_1rm(weight, reps):
    if reps == 0:
        return 0
    return weight * (1 + reps / 40)

# 関数名を 'run' にし、引数(df)を受け取るように変更
def run(df_original):
    st.title("筋トレ記録トラッカー")

    if df_original is None or df_original.empty:
        st.warning("表示できる記録がありません。「記録入力」タブからデータを追加してください。")
        return

    # 元のデータフレームをコピーして加工することで、他のタブに影響を与えない
    df = df_original.copy()
    
    # --- tracker.py内で行っていたデータ前処理 ---
      # 1. カラム名を英語に統一
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

    # 2. 'date'列をdatetime型に変換。変換できないものはNaT(Not a Time)になる
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # 3. 'date'が無効(NaT)な行を完全に削除する（これが重要！）
    df.dropna(subset=['date'], inplace=True)
    if df.empty:
        st.warning("有効な日付の記録がありません。")
        return

    # 4. トレーニング種目の列だけを0で埋める
    exercise_cols = [
        'bench_press', 'deadlift', 'squat', 'latpulldown', 'chinup', 
        'shoulder_press', 'leg_press', 'leg_press_45'
    ]
    for col in exercise_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0) # 各種目列のNaNだけを0で埋める
        else:
            df[col] = 0 # 列自体が存在しない場合は0で作成
     # 重量・回数に分解
    exercise_cols = ['bench_press', 'deadlift', 'squat', 'latpulldown', 'chinup', 'shoulder_press', 'leg_press', 'leg_press_45']
    for col in exercise_cols:
        if col in df.columns:
            # 文字列でないとapplyできない場合があるので、型を変換
            df[col] = df[col].astype(str)
            df[[f"{col}_kg", f"{col}_count"]] = df[col].apply(lambda x: pd.Series(parse_kg_count(x)))
            if col != 'chinup':
                df[f"{col}_1rm"] = df.apply(lambda row: estimate_1rm(row[f"{col}_kg"], row[f"{col}_count"]), axis=1)
    # フィルター UI（本体エリア）
    st.subheader("フィルタ")
    col1, col2, col3 = st.columns(3)

    with col1:
        # name列が存在し、空でない場合のみフィルタを表示
        if 'name' in df and not df['name'].dropna().empty:
            selected_authors = st.multiselect("記入者を選択", df['name'].dropna().unique().tolist())
        else:
            selected_authors = []
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
    # 不正データ（重量・回数ともにゼロ）を除外
    if selected_ex != "chinup":
        dff = dff[~((dff[f"{selected_ex}_kg"] == 0) & (dff[f"{selected_ex}_count"] == 0))]
    else:
        dff = dff[dff[f"{selected_ex}_count"] != 0]

     # グラフ表示 V1
    # if selected_ex != "chinup":
    #     st.subheader("重量推移")
    #     fig = px.line(dff, x='date', y=f'{selected_ex}_kg', markers=True)
    #     st.plotly_chart(fig, use_container_width=True)

    #     st.subheader("推定1RM推移")
    #     fig2 = px.line(dff, x='date', y=f'{selected_ex}_1rm', markers=True)
    #     st.plotly_chart(fig2, use_container_width=True)
    # else:
    #     st.subheader("回数推移")
    #     fig = px.line(dff, x='date', y=f'{selected_ex}_count', markers=True)
    #     st.plotly_chart(fig, use_container_width=True)
    
    # グラフ表示 V2
    end_range = dff['date'].max() + pd.Timedelta(days=2)
    start_range = end_range - pd.Timedelta(days=15)
    
    if selected_ex != "chinup":
        st.subheader("重量推移")
        fig = px.line(
            dff,
            x='date',
            y=f'{selected_ex}_kg',
            color='name' if len(dff['name'].unique()) > 1 else None,
            markers=True,
            title=f"{exercise_labels[selected_ex]} の重量推移",
            labels={'date': '日付', f'{selected_ex}_kg': '重量 (kg)'}
        )
        fig.update_traces(
            mode="lines+markers+text",
            text=dff[f'{selected_ex}_kg'].round(1),
            textposition="top center"
        )
        fig.update_layout(
            plot_bgcolor="white",
            title_x=0.5,
            xaxis=dict(
                showgrid=True, 
                gridcolor="#e0e0e0",
                range=[start_range, end_range],
                rangeslider_visible=False       
                ),
            yaxis=dict(
                showgrid=True, 
                gridcolor="#e0e0e0",
                )
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("推定1RM推移")
        fig2 = px.line(
            dff,
            x='date',
            y=f'{selected_ex}_1rm',
            color='name' if len(dff['name'].unique()) > 1 else None,
            markers=True,
            title=f"{exercise_labels[selected_ex]} の推定1RM推移",
            labels={'date': '日付', f'{selected_ex}_1rm': '推定1RM (kg)'}
        )
        fig2.update_traces(
            mode="lines+markers+text",
            text=dff[f'{selected_ex}_1rm'].round(1),
            textposition="top center"
        )
        fig2.update_layout(
            plot_bgcolor="white",
            title_x=0.5,
            xaxis=dict(
                showgrid=True, 
                gridcolor="#e0e0e0",
                range=[start_range, end_range],
                rangeslider_visible=False       
                ),
            yaxis=dict(
                showgrid=True, 
                gridcolor="#e0e0e0",
                )
        )
        fig2.update_xaxes(rangeslider_visible=False)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.subheader("回数推移")
        fig = px.line(
            dff,
            x='date',
            y=f'{selected_ex}_count',
            color='name' if len(dff['name'].unique()) > 1 else None,
            markers=True,
            title=f"{exercise_labels[selected_ex]} の回数推移",
            labels={'date': '日付', f'{selected_ex}_count': '回数'}
        )
        fig.update_traces(
            mode="lines+markers+text",
            text=dff[f'{selected_ex}_count'].round(1),
            textposition="top center"
        )
        fig.update_layout(
            plot_bgcolor="white",
            title_x=0.5,
            xaxis=dict(showgrid=True, gridcolor="#e0e0e0"),
            yaxis=dict(showgrid=True, gridcolor="#e0e0e0")
        )
        fig.update_xaxes(rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

 # データ表示
    st.markdown(f"**データ件数**: {len(dff)}")
    st.dataframe(dff[['name', 'date', f'{selected_ex}_kg', f'{selected_ex}_count']], use_container_width=True)