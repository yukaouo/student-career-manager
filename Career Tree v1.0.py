import os
import pandas as pd
import streamlit as st

# =========================
# 基本設定
# =========================
st.set_page_config(page_title="Career Tree", page_icon="🐕")
st.title("🐕 Career Tree")
st.caption("就活・インターン管理ダッシュボード")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "companies.csv")

COLUMNS = [
    "企業名",
    "企業ID",
    "企業HP",
    "職種",
    "ステータス",
    "種別",
    "開始日",
    "終了日",
    "単日",
    "メモ"
]

STATUS_COLOR = {
    "プレエントリー前": "#e3f2fd",
    "プレエントリー済み": "#e8f5e9",
    "ES提出済み": "#fff3e0",
    "適性検査受験済み": "#ede7f6",
    "面接中": "#fce4ec",
    "内定": "#c8e6c9",
    "落選": "#ffcdd2"
}

JOB_OPTIONS = ["通信", "インフラ", "メーカー", "コンサル", "SIer", "SE", "その他"]

# =========================
# CSV初期化
# =========================
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False, encoding="utf-8-sig")


def load_data():
    df = pd.read_csv(CSV_FILE)

    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ""

    # 旧データの自動変換
    df["ステータス"] = df["ステータス"].replace({
        "SPI受験済み": "適性検査受験済み"
    })

    df["種別"] = df["種別"].replace({
        "SPI": "適性検査",
        "SPI日": "適性検査日"
    })

    return df[COLUMNS]


def save_data(df):
    df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")


# =========================
# 修正フォーム
# =========================
if "edit_index" in st.session_state:

    st.subheader("✏️ 企業修正")

    df = load_data()
    i = st.session_state["edit_index"]
    row = df.iloc[i]

    name = st.text_input("企業名", row["企業名"], key="edit_name")
    company_id = st.text_input("企業ID", row["企業ID"],key="edit_company_id")
    company_hp = st.text_input("企業HP",row["企業HP"],key="edit_company_hp")
    job_type = st.text_input("職種・コース", row["職種"], key="edit_job")

    status = st.selectbox(
        "ステータス",
        list(STATUS_COLOR.keys()),
        index=list(STATUS_COLOR.keys()).index(row["ステータス"])
        if row["ステータス"] in STATUS_COLOR else 0,
        key="edit_status"
    )

    memo = st.text_area("メモ", row["メモ"], key="edit_memo")

    if st.button("更新保存"):
        df.loc[i, "企業名"] = name
        df.loc[i, "企業ID"] = company_id
        df.loc[i, "企業HP"] = company_hp
        df.loc[i, "職種"] = job_type
        df.loc[i, "ステータス"] = status
        df.loc[i, "メモ"] = memo

        save_data(df)

        del st.session_state["edit_index"]
        st.rerun()


# =========================
# 入力フォーム
# =========================
st.subheader("➕ 新規登録")

name = st.text_input("企業名", key="new_name")

company_id = st.text_input(
    "企業ID（マイページID等）",
    key="new_company_id"
)

company_hp = st.text_input(
    "企業HP",
    placeholder="https://...",
    key="new_company_hp"
)

job_choice = st.selectbox(
    "職種・コース",
    JOB_OPTIONS,
    key="new_job_choice"
)

if job_choice == "その他":
    job_type = st.text_input("その他の職種・コースを入力", key="new_job_other")
else:
    job_type = job_choice

status = st.selectbox(
    "ステータス",
    list(STATUS_COLOR.keys()),
    key="new_status"
)

kind = ""
start_date = ""
end_date = ""
single_date = ""

if status == "プレエントリー前":
    kind = "締切"
    single_date = st.date_input("エントリー締切")

elif status == "プレエントリー済み":
    kind = "ES"
    single_date = st.date_input("ES締切")

elif status == "ES提出済み":
    choice = st.radio("ES後", ["適性検査", "合否通知日", "落選"], horizontal=True)

    if choice == "適性検査":
        kind = "適性検査"
        single_date = st.date_input("適性検査日")

    elif choice == "合否通知日":
        kind = "合否通知日"
        single_date = st.date_input("合否通知日")

    else:
        kind = "落選"

elif status == "適性検査受験済み":
    choice = st.radio(
        "適性検査後",
        ["面接", "インターン参加日程", "合否通知日", "落選"],
        horizontal=True
    )

    if choice == "面接":
        kind = "面接"
        single_date = st.date_input("面接日")

    elif choice == "インターン参加日程":
        kind = "インターン参加日程"

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("開始日")
        with col2:
            end_date = st.date_input("終了日")

    elif choice == "合否通知日":
        kind = "合否通知日"
        single_date = st.date_input("合否通知日")

    else:
        kind = "落選"

elif status == "面接中":
    choice = st.radio("面接後", ["次選考", "合否通知日", "落選"], horizontal=True)

    if choice == "次選考":
        kind = "面接"
        single_date = st.date_input("面接日")

    elif choice == "合否通知日":
        kind = "合否通知日"
        single_date = st.date_input("合否通知日")

    else:
        kind = "落選"

elif status == "内定":
    kind = "内定"
    single_date = st.date_input("内定日")

elif status == "落選":
    kind = "落選"

# メモは日程入力の下
memo = st.text_area("メモ", key="new_memo")


# =========================
# 登録
# =========================
if st.button("登録🐕") and name:

    df = load_data()

    df = pd.concat([df, pd.DataFrame([{
        "企業名": name,
        "企業ID": company_id,
        "企業HP": company_hp,
        "職種": job_type,
        "ステータス": status,
        "種別": kind,
        "開始日": str(start_date) if start_date else "",
        "終了日": str(end_date) if end_date else "",
        "単日": str(single_date) if single_date else "",
        "メモ": memo
    }])], ignore_index=True)

    save_data(df)
    st.rerun()


# =========================
# ダッシュボード
# =========================
df_dashboard = load_data()

active_count = len(df_dashboard[~df_dashboard["ステータス"].isin(["内定", "落選"])])
interview_count = len(df_dashboard[df_dashboard["ステータス"] == "面接中"])
offer_count = len(df_dashboard[df_dashboard["ステータス"] == "内定"])
fail_count = len(df_dashboard[df_dashboard["ステータス"] == "落選"])
waiting_count = len(
    df_dashboard[
        df_dashboard["種別"] == "合否通知日"
    ]
)

st.subheader("📊 ダッシュボード")

col1, col2, col3, col4,col5 = st.columns(5)

with col1:
    st.metric("進行中", active_count)

with col2:
    st.metric("面接中", interview_count)

with col3:
    st.metric("合否待ち", waiting_count)

with col4:
    st.metric("内定", offer_count)

with col5:
    st.metric("落選", fail_count)

# =========================
# 締切アラート
# =========================
st.subheader("🚨 締切アラート")

df_alert = load_data()

today = pd.Timestamp.today().normalize()

df_alert["単日"] = pd.to_datetime(df_alert["単日"], errors="coerce")
df_alert["残り日数"] = (df_alert["単日"] - today).dt.days

alert_df = df_alert[
    (df_alert["単日"].notna())
    &
    (df_alert["残り日数"] >= 0)
    &
    (df_alert["残り日数"] <= 3)
    &
    (~df_alert["ステータス"].isin(["内定", "落選"]))
]

alert_df = alert_df.sort_values("残り日数")

if len(alert_df) == 0:
    st.info("直近3日以内の締切はありません🐕")
else:
    for _, row in alert_df.iterrows():
        if row["残り日数"] == 0:
            st.error(f"🚨 本日：{row['企業名']}（{row['種別']}）")
        elif row["残り日数"] == 1:
            st.warning(f"⚠️ あと1日：{row['企業名']}（{row['種別']}）")
        else:
            st.warning(f"⏰ あと{row['残り日数']}日：{row['企業名']}（{row['種別']}）")

# =========================
# インターン開始アラート
# =========================

df_start = load_data()

df_start["開始日"] = pd.to_datetime(
    df_start["開始日"],
    errors="coerce"
)

df_start["開始まで"] = (
    df_start["開始日"] - today
).dt.days

start_alert = df_start[
    (df_start["開始日"].notna())
    &
    (df_start["開始まで"] >= 0)
    &
    (df_start["開始まで"] <= 3)
]

if len(start_alert) > 0:

    st.subheader("🎯 インターン開始アラート")

    start_alert = start_alert.sort_values("開始まで")

    for _, row in start_alert.iterrows():

        if row["開始まで"] == 0:
            st.error(
                f"🚀 本日開始：{row['企業名']}"
            )

        elif row["開始まで"] == 1:
            st.warning(
                f"⚠️ 明日開始：{row['企業名']}"
            )

        else:
            st.info(
                f"📅 あと{row['開始まで']}日：{row['企業名']}"
            )

# =========================
# 登録一覧
# =========================
st.subheader("📋 登録一覧")

df = load_data()

search_word = st.text_input("🔍 検索", placeholder="企業名・職種・メモで検索")

status_filter = st.selectbox(
    "📂 ステータス絞り込み",
    ["すべて"] + list(STATUS_COLOR.keys()),
    key="status_filter"
)

sort_type = st.selectbox(
    "🔃 並び替え",
    ["登録順", "企業名順", "単日が近い順", "開始日が近い順"],
    key="sort_select"
)

if status_filter != "すべて":
    df = df[df["ステータス"] == status_filter]

if search_word:
    df = df[
        df["企業名"].astype(str).str.contains(search_word, case=False, na=False)
        |
        df["職種"].astype(str).str.contains(search_word, case=False, na=False)
        |
        df["メモ"].astype(str).str.contains(search_word, case=False, na=False)
    ]

if sort_type == "企業名順":
    df = df.sort_values("企業名")

elif sort_type == "単日が近い順":
    df["単日_sort"] = pd.to_datetime(df["単日"], errors="coerce")
    df = df.sort_values("単日_sort", na_position="last")
    df = df.drop(columns=["単日_sort"])

elif sort_type == "開始日が近い順":
    df["開始日_sort"] = pd.to_datetime(df["開始日"], errors="coerce")
    df = df.sort_values("開始日_sort", na_position="last")
    df = df.drop(columns=["開始日_sort"])

for i, row in df.iterrows():

    if "落選" in str(row["ステータス"]) or "落選" in str(row["種別"]):
        bg = "#ffcdd2"
    else:
        bg = STATUS_COLOR.get(row["ステータス"], "#ffffff")

    # 日付表示
    date_text = ""

    if pd.notna(row["単日"]) and str(row["単日"]) != "":
        date_text = str(row["単日"])

    elif pd.notna(row["開始日"]) and pd.notna(row["終了日"]):
        if str(row["開始日"]) != "" and str(row["終了日"]) != "":
            date_text = f"{row['開始日']} ～ {row['終了日']}"

    # 企業ID
    id_text = ""

    if pd.notna(row["企業ID"]) and str(row["企業ID"]) != "":
        id_text = f"🆔 {row['企業ID']}<br>"

    # メモ
    memo_text = ""

    if pd.notna(row["メモ"]) and str(row["メモ"]) != "":
        memo_text = f"📝 {row['メモ']}<br>"

    st.markdown(f"""
    <div style="
        background:{bg};
        padding:12px;
        border-radius:10px;
        border:1px solid #ddd;
        margin-bottom:8px;
    ">
        🐕 <b>{row['企業名']}</b><br>
            {id_text}
        💼 {row['職種']}<br>
        📌 {row['ステータス']} / {row['種別']}<br>
        📅 {date_text}<br>
        {memo_text}
    </div>
    """, unsafe_allow_html=True)
    if pd.notna(row["企業HP"]) and str(row["企業HP"]) != "":
        st.link_button("🌐 企業HPを開く", str(row["企業HP"]))
    
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("修正", key=f"edit_{i}"):
            st.session_state["edit_index"] = i
            st.rerun()

    with col2:
        if st.button("削除", key=f"del_{i}"):
            full_df = load_data()
            full_df = full_df.drop(i).reset_index(drop=True)
            save_data(full_df)
            st.rerun()
