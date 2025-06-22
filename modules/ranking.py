# modules/ranking.py (アップグレード版)

import streamlit as st
import pandas as pd
import numpy as np  # numpyをインポート
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- ヘルパー関数 (変更なし) ---
def parse_kg_count(value):
    if isinstance(value, str) and '-' in value:
        try:
            kg, rep = value.split('-')
            return float(kg), int(rep)
        except:
            return 0.0, 0
    try:
        return 0.0, int(value)
    except:
        return 0.0, 0

def estimate_1rm(weight, reps):
    if reps == 0 or weight == 0:
        return 0.0
    return weight * (1 + reps / 40)


# --- メイン関数 ---
def run(df_original):
    st.title("🏆 ランキング")
    st.markdown("---")

    if df_original is None or df_original.empty:
        st.warning("表示できる記録がありません。")
        return

    # --- データ前処理 (共通部分) ---
    df = df_original.copy()
    df = df.rename(columns={'記入者名': 'name', '記録日': 'date'})
    for col in df.columns:
        if 'kg' in col or '回数' in col:
            new_col_name = col.replace('(kg × 回数)', '').replace('(回数)', '').strip()
            df = df.rename(columns={col: new_col_name})
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df.dropna(subset=['date'], inplace=True)
    
    exercise_cols = [
        'ベンチプレス', 'デッドリフト', 'スクワット', 'ラットプルダウン',
        'マシンショルダープレス', 'レッグプレス', '45°レッグプレス'
    ]
    for col in exercise_cols:
        if col in df.columns:
            df[col] = df[col].fillna('0-0')
            df[[f"{col}_kg", f"{col}_reps"]] = df[col].astype(str).apply(lambda x: pd.Series(parse_kg_count(x)))
            df[f"{col}_1rm"] = df.apply(lambda row: estimate_1rm(row[f"{col}_kg"], row[f"{col}_reps"]), axis=1)

    # --- タブによる機能切り替え ---
    tab1, tab2 = st.tabs(["💪 1RMランキング", "📈 成長率ランキング"])

    # --- 1RMランキングタブ ---
    with tab1:
        st.subheader("種目別 自己ベスト(1RM)ランキング")
        selected_exercise_1rm = st.selectbox("種目を選択", exercise_cols, key="1rm_select")
        
        if selected_exercise_1rm and f"{selected_exercise_1rm}_1rm" in df.columns:
            pr_ranking = df.groupby('name')[f'{selected_exercise_1rm}_1rm'].max()
            pr_ranking = pr_ranking[pr_ranking > 0].sort_values(ascending=False).reset_index()
            pr_ranking.index = pr_ranking.index + 1
            pr_ranking.rename(columns={'name': '名前', f'{selected_exercise_1rm}_1rm': '推定1RM (kg)'}, inplace=True)
            
            st.markdown(f"#### {selected_exercise_1rm} トップ10")
            for index, row in pr_ranking.head(10).iterrows():
                cols = st.columns([1, 4, 2])
                rank_str = f"**{index}位**"
                if index == 1: rank_str = f"🥇 {rank_str}"
                elif index == 2: rank_str = f"🥈 {rank_str}"
                elif index == 3: rank_str = f"🥉 {rank_str}"
                cols[0].markdown(rank_str)
                cols[1].markdown(f"**{row['名前']}**")
                cols[2].markdown(f"**{row['推定1RM (kg)']:.1f} kg**")
            
            with st.expander("全ランキングを表示"):
                st.dataframe(pr_ranking, use_container_width=True)

    # --- 成長率ランキングタブ (新機能) ---
    with tab2:
        st.subheader("月間 成長率ランキング")
        col1, col2 = st.columns(2)
        
        with col1:
            # 1. 月の選択肢を生成
            #months = df['date'].dt.to_period('M').unique().sort_values(ascending=False).astype(str)
            months = df['date'].dt.to_period('M').drop_duplicates().sort_values(ascending=False).astype(str)
            selected_month_str = st.selectbox("対象月を選択", months)
        
        with col2:
            selected_exercise_growth = st.selectbox("種目を選択", exercise_cols, key="growth_select")
        
        if selected_month_str and selected_exercise_growth:
            # 2. 選択された月の開始日と終了日を定義
            start_of_month = pd.to_datetime(selected_month_str + "-01")
            end_of_month = start_of_month + pd.offsets.MonthEnd(1)

            # 3. 各ユーザーの月初と月末のベスト1RMを計算
            growth_data = []
            users = df['name'].unique()
            
            for user in users:
                user_df = df[(df['name'] == user) & (df[f'{selected_exercise_growth}_1rm'] > 0)]
                
                # 月初時点でのベスト1RM
                start_df = user_df[user_df['date'] < start_of_month]
                start_1rm = start_df[f'{selected_exercise_growth}_1rm'].max() if not start_df.empty else 0
                
                # 月末時点でのベスト1RM
                end_df = user_df[user_df['date'] <= end_of_month]
                end_1rm = end_df[f'{selected_exercise_growth}_1rm'].max() if not end_df.empty else 0

                # 成長があった場合のみリストに追加
                if end_1rm > start_1rm:
                    growth_data.append({
                        "名前": user,
                        "月初1RM (kg)": start_1rm,
                        "月末1RM (kg)": end_1rm,
                        "成長(kg)": end_1rm - start_1rm
                    })
            
            if not growth_data:
                st.info(f"{selected_month_str}月は、{selected_exercise_growth}で成長したメンバーの記録がありません。")
            else:
                # 4. 成長量でランキングを作成
                growth_ranking = pd.DataFrame(growth_data)
                growth_ranking['成長率(%)'] = (growth_ranking['成長(kg)'] / growth_ranking['月初1RM (kg)']) * 100
                
                # ★★★ +inf% (無限大) や -inf% になった行を削除する処理を追加 ★★★
                growth_ranking.replace([np.inf, -np.inf], np.nan, inplace=True)
                growth_ranking.dropna(subset=['成長率(%)'], inplace=True)
                
                
                growth_ranking = growth_ranking.sort_values(by="成長率(%)", ascending=False).reset_index(drop=True)
                growth_ranking.index = growth_ranking.index + 1

                if growth_ranking.empty:
                    st.info(f"{selected_month_str}月は、ランキング対象となるメンバーの記録がありません。")
                else:


                # --- ↓↓↓ トップ10をスタイリッシュに表示する処理を追加 ↓↓↓ ---
                    st.markdown(f"#### {selected_month_str}月 {selected_exercise_growth} 成長トップ10")
                    for index, row in growth_ranking.head(10).iterrows():
                        cols = st.columns([1, 3, 3])
                        rank_str = f"**{index}位**"
                        if index == 1: rank_str = f"🥇 {rank_str}"
                        elif index == 2: rank_str = f"🥈 {rank_str}"
                        elif index == 3: rank_str = f"🥉 {rank_str}"
                        
                        growth_detail = (
                            f"**+{row['成長率(%)']:.1f} %** "
                            f"<small>({row['月初1RM (kg)']:.1f} → {row['月末1RM (kg)']:.1f} kg)</small>"
                        )
                        
                        cols[0].markdown(rank_str, unsafe_allow_html=True)
                        cols[1].markdown(f"**{row['名前']}**", unsafe_allow_html=True)
                        cols[2].markdown(growth_detail, unsafe_allow_html=True)

                    # --- ↑↑↑ ここまで追加 ↑↑↑ ---              
                    with st.expander("全成長記録を表示"):                
                        st.dataframe(
                            growth_ranking,
                            column_config={
                                "月初1RM (kg)": st.column_config.NumberColumn(format="%.1f"),
                                "月末1RM (kg)": st.column_config.NumberColumn(format="%.1f"),
                                "成長(kg)": st.column_config.ProgressColumn(
                                    "成長(kg)",
                                    format="+%.1f kg",
                                    min_value=0,
                                    max_value=growth_ranking['成長(kg)'].max(),
                                ),
                                "成長率(%)": st.column_config.NumberColumn(format="+%.1f%%"),
                            },
                            use_container_width=True
                        )
    # --- ↓↓↓ この部分が追加されました ↓↓↓ ---
    st.markdown("---")
    st.subheader("📊 データ管理")
    st.info("アプリのコードを更新（git push）する前など、定期的に全記録をダウンロードしてバックアップすることを推奨します。")

    # オリジナルの全データ(df_original)をCSV形式に変換
    # BOM付きUTF-8でエンコードすることで、Excelで開いた際の文字化けを防ぐ
    csv_data = df_original.to_csv(index=False).encode('utf-8-sig')

    st.download_button(
        label="📈 全トレーニング記録をダウンロード (CSV)",
        data=csv_data,
        file_name=f"training_log_backup_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
        help="サーバーに保存されている最新の全トレーニング記録をCSVファイルとしてダウンロードします。",
        type='primary'  # ★★★ この行を追加 ★★★
    )    
                        