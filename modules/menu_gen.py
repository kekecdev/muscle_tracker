import streamlit as st

def render():
    st.title("(TEST)ベンチプレス目標メニュー自動生成")

    st.markdown("### 身長と体重に応じて、目標ベンチプレス重量を表示します。")

    # 入力：身長・体重
    height = st.number_input("身長（cm）", min_value=100, max_value=250, value=170)
    weight = st.number_input("体重（kg）", min_value=30, max_value=200, value=60)

    # 自動計算
    strength_ratio = 1.2 + (height - 160) * 0.005
    target = round(weight * strength_ratio)

    # 強調表示（色付きボックス）
    st.markdown(f"""
        <div style="border-radius: 0.5em; background-color: #e0f7fa; padding: 1em; border-left: 5px solid #00796b;">
            <h4 style="color:#00796b;"> あなたの目標ベンチプレス重量は <strong>{target} kg</strong> です！</h4>
            <p style="margin: 0; color: black;">（計算式: {strength_ratio:.2f} × 体重 {weight} kg）</p>
        </div>
    """, unsafe_allow_html=True)