# modules/form.py (Google Sheets API対応版)

import streamlit as st
import pandas as pd
from datetime import datetime
# スプレッドシートに書き込むためのライブラリをインポート
from gspread_dataframe import set_with_dataframe

# run関数の引数を data_file_path から worksheet に変更
def run(df, worksheet):
    st.title("筋トレ記録入力フォーム")
    st.markdown("### 今日のトレーニングを記録しよう！")
    
    st.markdown("##### 記入者")
    
    user_type = st.radio(
        "記入者タイプを選択してください",
        ["既存メンバー", "新規メンバー"],
        horizontal=True,
    )
    
    with st.form(key=f'training_form_{user_type}', clear_on_submit=True):
        name = ""
        
        if user_type == "既存メンバー":
            if '記入者名' in df.columns and not df['記入者名'].dropna().empty:
                user_list = sorted(df['記入者名'].dropna().unique().tolist())
                options = [""] + user_list
                name = st.selectbox(
                    "リストから名前を選択してください",
                    options,
                    label_visibility="collapsed"
                )
            else:
                # フォームの中ではst.infoがうまく表示されないことがあるため、
                # ラジオボタンの外にメッセージを出すか、何もしないのが良い
                pass

        else: # "新規メンバー" が選択された場合
            name = st.text_input(
                "新しい名前を入力してください",
                placeholder="ここに名前を入力",
                label_visibility="collapsed"
            )

        record_date = st.date_input("記録日", datetime.now())
        
        st.markdown("---")
        st.markdown("##### BIG 3")
        bench_press = st.text_input("ベンチプレス (kg-回数)", placeholder="例: 80-10")
        deadlift = st.text_input("デッドリフト (kg-回数)", placeholder="例: 120-8")
        squat = st.text_input("スクワット (kg-回数)", placeholder="例: 100-12")
        
        st.markdown("---")
        st.markdown("##### その他")
        latpulldown = st.text_input("ラットプルダウン (kg-回数)")
        chinup = st.text_input("懸垂 (回数)", placeholder="例: 15")
        shoulder_press = st.text_input("マシンショルダープレス (kg-回数)")
        leg_press = st.text_input("レッグプレス (kg-回数)")
        leg_press_45 = st.text_input("45°レッグプレス (kg-回数)")

        submit_button = st.form_submit_button(label='この内容で記録する', type='primary')

    # 送信ボタンが押された後の処理
    if submit_button:
        if not name:
            st.warning("記入者を選択、または新しい名前を入力してください。")
            st.stop()
        
        # worksheetオブジェクトが正常に渡されているかチェック
        if worksheet is None:
            st.error("スプレッドシートに接続できません。設定を確認してください。")
            st.stop()

        new_record = pd.DataFrame([{
            'タイムスタンプ': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
            'メールアドレス': '', '記入者名': name,
            '記録日': record_date.strftime('%Y-%m-%d 00:00:00'),
            'ベンチプレス(kg × 回数)': bench_press, 'デッドリフト(kg × 回数)': deadlift,
            'スクワット(kg × 回数)': squat, 'ラットプルダウン(kg × 回数)': latpulldown,
            '懸垂(回数)': chinup, 'マシンショルダープレス(kg × 回数)': shoulder_press,
            'レッグプレス(kg × 回数)': leg_press, '45°レッグプレス(kg × 回数)': leg_press_45,
        }])
        
        updated_df = pd.concat([df, new_record], ignore_index=True)

        # ★★★ CSVへの書き込み処理を、スプレッドシートへの書き込み処理に差し替え ★★★
        try:
            set_with_dataframe(worksheet, updated_df, include_index=False, resize=True)
            st.session_state.df = updated_df
            st.success(f"{name}さんの記録が正常に追加されました！ 🎉")
        except gspread.exceptions.APIError as e:
            st.error(f"スプレッドシートへの書き込み中にエラーが発生しました。Google Cloudの権限などを確認してください。エラー: {e}")