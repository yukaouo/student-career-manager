import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Student Career Manager",
    page_icon="📋"
)

st.write("現在の作業フォルダ:", os.getcwd())

# CSVファイル名
# このPythonファイルと同じフォルダにCSVを保存
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "companies.csv")




st.title("📋 Student Career Manager")
st.write("就職活動を管理するシンプルなアプリ")

# CSVが存在しない場合は新規作成
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=["企業名"])
    df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")

# CSVを読み込む
df = pd.read_csv(CSV_FILE)

# 入力欄
company = st.text_input("企業名を入力")

# 登録ボタン
if st.button("登録"):
    if company.strip() != "":
        new_data = pd.DataFrame({"企業名": [company]})
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
        st.success(f"「{company}」を登録しました！")
    else:
        st.warning("企業名を入力してください。")

# 最新データを再読込
df = pd.read_csv(CSV_FILE)

st.subheader("登録済み企業一覧")
st.dataframe(df, use_container_width=True)