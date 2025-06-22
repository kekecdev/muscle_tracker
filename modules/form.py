# modules/form.py (st.toastを使った最終完成版)

import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from gspread_dataframe import set_with_dataframe
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def append_row_with_retry(worksheet, data):
    """gspreadのAPIエラーが起きてもリトライする、append_rowのラッパー関数"""
    worksheet.append_row(data)


def run(df, worksheet):
    # run関数の先頭にあったsession_stateのメッセージ処理は、もう不要なので削除します。

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
                # このst.infoはformの中にあるため、送信ボタンを押すまで表示されません。
                # ユーザー体験を考慮し、ラジオボタンの外に移動させるのが望ましいですが、
                # 今は機能修正を優先します。
                st.info("まだ登録メンバーがいません。「新規メンバー」を選択してください。")
        else:
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

    if submit_button:
        if not name:
            st.warning("記入者を選択、または新しい名前を入力してください。")
            st.stop()
        
        if worksheet is None:
            st.error("スプレッドシートに接続できません。設定を確認してください。")
            st.stop()

        new_row_data = [
            datetime.now().strftime('%Y/%m/%d %H:%M:%S'), '', name,
            record_date.strftime('%Y-%m-%d 00:00:00'),
            bench_press, deadlift, squat, latpulldown, chinup,
            shoulder_press, leg_press, leg_press_45,
        ]

        try:
            append_row_with_retry(worksheet, new_row_data)
            
            # session_stateのデータ更新は、他のタブとの連携のために継続
            headers = worksheet.get_all_values()[0]
            new_record_df = pd.DataFrame([new_row_data], columns=headers)
            new_record_df['記録日'] = pd.to_datetime(new_record_df['記録日'])
            updated_df = pd.concat([df, new_record_df], ignore_index=True)
            st.session_state.df = updated_df
            
            # ★★★ st.successとst.rerunを、st.toastに変更 ★★★
            st.toast(f'{name}さんの記録を追加しました！', icon='🎉')

        except Exception as e:
            st.error(f"書き込み中に予期せぬエラーが発生しました: {e}")