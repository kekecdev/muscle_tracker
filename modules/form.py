# modules/form.py (最終完成・同時書き込み対応版)

import streamlit as st
import pandas as pd
from datetime import datetime
import gspread # エラーハンドリングのためにインポート

# run関数の引数は df と worksheet
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
                st.info("まだ登録メンバーがいません。「新規メンバー」を選択してください。")

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

    # --- ↓↓↓ 送信ボタンが押された後の処理を、「1行追記」型に全面改訂 ↓↓↓ ---
    if submit_button:
        if not name:
            st.warning("記入者を選択、または新しい名前を入力してください。")
            st.stop()
        
        if worksheet is None:
            st.error("スプレッドシートに接続できません。設定を確認してください。")
            st.stop()

        # 1. スプレッドシートのヘッダー順に合わせて、1行分のデータを「リスト」として作成
        #    この順番は、スプレッドシートの列の順番と完全に一致させる必要があります。
        new_row_data = [
            datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
            '', # メールアドレス
            name,
            record_date.strftime('%Y-%m-%d 00:00:00'),
            bench_press,
            deadlift,
            squat,
            latpulldown,
            chinup,
            shoulder_press,
            leg_press,
            leg_press_45,
            # 今後列を追加した場合は、ここにも同じ順番で追加
        ]

        try:
            # 2. スプレッドシートの末尾に、作成したリストを1行追記する
            worksheet.append_row(new_row_data)

            # 3. 現在のセッションの表示を更新するために、手元のデータフレームにも追加
            #    スプレッドシートのヘッダーを取得して、列名を合わせる
            headers = worksheet.get_all_values()[0]
            new_record_df = pd.DataFrame([new_row_data], columns=headers)
            # 日付の型を他のデータと合わせておく
            new_record_df['記録日'] = pd.to_datetime(new_record_df['記録日'])
            
            updated_df = pd.concat([df, new_record_df], ignore_index=True)
            st.session_state.df = updated_df
            
            st.success(f"{name}さんの記録が正常に追加されました！ 🎉")
            # 画面を再実行して、入力フォームをクリアしつつ表示を最新にする
            st.rerun()

        except gspread.exceptions.APIError as e:
            st.error(f"スプレッドシートへの書き込み中にエラーが発生しました。Google Cloudの権限などを確認してください。エラー: {e}")