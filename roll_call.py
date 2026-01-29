import streamlit as st
import pandas as pd
from datetime import datetime
import os
import qrcode
from io import BytesIO


# --- 設定與資料庫 ---
DB_FILE = "attendance_db.csv"
ADMIN_PASSWORD = "ha360admin"  # 你可以修改這個管理密碼

if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame([
        {"姓名": "小明", "簽到時間": None, "簽退時間": None, "積分": 0},
        {"姓名": "小華", "簽到時間": None, "簽退時間": None, "積分": 0}
    ])
    df_init.to_csv(DB_FILE, index=False)

def load_data():
    return pd.read_csv(DB_FILE)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- 介面導航 ---
st.set_page_config(page_title="HA360 點名管理系統", layout="wide")
menu = st.sidebar.radio("功能選單", ["學員簽到頁", "管理員後台"])

# --------------------------
# 頁面 1：學員簽到頁
# --------------------------
if menu == "學員簽到頁":
    st.title("🎓 HA360 自主簽到")
    df = load_data()
    with st.form("checkin", clear_on_submit=True):
        name = st.text_input("輸入您的姓名")
        btn = st.form_submit_button("送出")
        if btn:
            if name in df['姓名'].values:
                idx = df[df['姓名'] == name].index[0]
                now = datetime.now().strftime("%H:%M")
                if pd.isna(df.at[idx, '簽到時間']):
                    df.at[idx, '簽到時間'] = now
                    st.success(f"{name} 簽到成功！")
                elif pd.isna(df.at[idx, '簽退時間']):
                    df.at[idx, '簽退時間'] = now
                    st.info(f"{name} 簽退成功！")
                save_data(df)
            else:
                st.error("名單中無此姓名")

# --------------------------
# 頁面 2：管理員後台
# --------------------------
elif menu == "管理員後台":
    st.title("⚙️ 管理員控制面板")
    
    # 密碼驗證
    pwd = st.text_input("請輸入管理員密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        st.success("身分驗證通過")
        df = load_data()
        # 1. 確保「積分」是整數型態，並把空值補 0
        df['積分'] = pd.to_numeric(df['積分'], errors='coerce').fillna(0).astype(int)
        
        # 2. 確保時間欄位是字串，避免出現 NaN 導致編輯器崩潰
        df['簽到時間'] = df['簽到時間'].fillna("")
        df['簽退時間'] = df['簽退時間'].fillna("")

        # 分成三個控制區塊
        tab1, tab2, tab3, tab4 = st.tabs(["🏆 積分管理", 
                                          "📝 名單編輯", 
                                          "📊 數據導出",
                                          "🎓 現場自主報導"])

        with tab1:
            st.subheader("互動環節加分")
            col1, col2 = st.columns(2)
            with col1:
                target = st.selectbox("選擇學員", df['姓名'])
            with col2:
                points = st.number_input("加分數值", value=5, step=1)
            
            if st.button("確認加分"):
                df.loc[df['姓名'] == target, '積分'] += points
                save_data(df)
                st.balloons()
                st.success(f"已幫 {target} 增加 {points} 分")

        with tab2:
            st.subheader("手動修改資料")
            # 讓管理員可以直接在網頁上編輯表格
            edited_df = st.data_editor(
                df,
                num_rows="dynamic", # 允許動態增減行數
                column_config={
                    "姓名": st.column_config.TextColumn("姓名", help="請輸入學員全名", required=True),
                    "簽到時間": st.column_config.TextColumn("簽到時間", disabled=False),
                    "簽退時間": st.column_config.TextColumn("簽退時間", disabled=False),
                    "積分": st.column_config.NumberColumn(
                        "積分",
                        help="預設值為 0",
                        min_value=0,
                        default=0,  # 這行就是你要的預設值！
                        format="%d 分"
                    ),
                },
                use_container_width=True
            )



            if st.button("儲存所有修改"):
                save_data(edited_df)
                st.toast("資料庫已更新！")

        with tab3:
            st.subheader("下載統計報表")
            st.dataframe(df)
            csv = df.to_csv(index=False).encode('utf-8-sig') # utf-8-sig 解決 Excel 亂碼
            st.download_button(
                label="📥 下載為 CSV 檔案",
                data=csv,
                file_name=f"HA360_Report_{datetime.now().date()}.csv",
                mime="text/csv"
            )

        with tab4:    
            st.subheader("📢 現場點名 QR Code")
            url = "https://ha360-rollcall-axjxhju8fwzvno8ugrnzao.streamlit.app/" # 部署完後產生的網址
            qr_img = qrcode.make(url)
            buf = BytesIO()
            qr_img.save(buf)
            st.image(buf.getvalue(), caption="請學員掃描此 Code 進行自主簽到")


    elif pwd != "":
        st.error("密碼錯誤，請重新輸入")
