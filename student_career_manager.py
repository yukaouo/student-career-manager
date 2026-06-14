import calendar
import html
import io
import os
import shutil
from datetime import date, datetime

import pandas as pd
import streamlit as st


st.set_page_config(page_title="Career Tree", page_icon="🌳", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "companies.csv")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")

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
    "メモ",
]

STATUS_OPTIONS = [
    "プレエントリー前",
    "プレエントリー済み",
    "ES提出済み",
    "適性検査受験済み",
    "面接中",
    "内定",
    "落選",
]

EVENT_OPTIONS = [
    "エントリー締切",
    "ES締切",
    "適性検査日",
    "面接日",
    "合否通知日",
    "インターン期間",
    "インターン開始日",
    "インターン終了日",
    "内定日",
    "落選",
    "未定",
]

JOB_OPTIONS = ["通信", "インフラ", "メーカー", "コンサル", "SIer", "SE"]
FINAL_STATUSES = {"内定", "落選"}

LIGHT_STATUS_COLORS = {
    "プレエントリー前": "#e8f1ff",
    "プレエントリー済み": "#e8f7ee",
    "ES提出済み": "#fff3d8",
    "適性検査受験済み": "#f0e9ff",
    "面接中": "#ffe8f1",
    "内定": "#dff5df",
    "落選": "#ffe0e0",
}

DARK_STATUS_COLORS = {
    "プレエントリー前": "#182b45",
    "プレエントリー済み": "#173523",
    "ES提出済み": "#3b2d12",
    "適性検査受験済み": "#2a2145",
    "面接中": "#3e1d2a",
    "内定": "#183820",
    "落選": "#421f20",
}


def apply_style(dark_mode: bool) -> None:
    bg = "#0f172a" if dark_mode else "#f7f8fb"
    panel = "#111827" if dark_mode else "#ffffff"
    text = "#e5e7eb" if dark_mode else "#1f2937"
    muted = "#9ca3af" if dark_mode else "#6b7280"
    border = "#374151" if dark_mode else "#e5e7eb"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {bg};
            color: {text};
        }}
        [data-testid="stSidebar"] {{
            background: {panel};
        }}
        .career-card, .calendar-wrap {{
            background: {panel};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 10px;
        }}
        .career-title {{
            font-size: 1.05rem;
            font-weight: 700;
            color: {text};
            margin-bottom: 6px;
        }}
        .career-meta {{
            color: {muted};
            line-height: 1.7;
            font-size: 0.94rem;
        }}
        .tag {{
            display: inline-block;
            padding: 2px 8px;
            margin: 0 4px 4px 0;
            border: 1px solid {border};
            border-radius: 999px;
            color: {text};
            font-size: 0.82rem;
        }}
        .calendar-grid {{
            display: grid;
            grid-template-columns: repeat(7, minmax(0, 1fr));
            gap: 6px;
        }}
        .calendar-head {{
            color: {muted};
            font-weight: 700;
            text-align: center;
            padding: 6px 0;
        }}
        .calendar-day {{
            min-height: 104px;
            border: 1px solid {border};
            border-radius: 8px;
            padding: 8px;
            background: {"#0b1220" if dark_mode else "#ffffff"};
            overflow: hidden;
        }}
        .calendar-day.empty {{
            opacity: 0.35;
        }}
        .calendar-date {{
            font-weight: 700;
            margin-bottom: 5px;
        }}
        .calendar-event {{
            font-size: 0.76rem;
            line-height: 1.35;
            padding: 3px 5px;
            border-radius: 5px;
            margin-bottom: 4px;
            background: {"#1f2937" if dark_mode else "#eef2ff"};
            color: {text};
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        @media (max-width: 760px) {{
            .calendar-grid {{
                gap: 4px;
            }}
            .calendar-day {{
                min-height: 78px;
                padding: 5px;
            }}
            .calendar-head {{
                font-size: 0.75rem;
            }}
            .calendar-event {{
                font-size: 0.68rem;
                padding: 2px 4px;
            }}
            .career-card {{
                padding: 12px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def read_csv_safely() -> pd.DataFrame:
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=COLUMNS)
        save_data(df)
        return df

    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            df = pd.read_csv(CSV_FILE, dtype=str, encoding=encoding).fillna("")
            break
        except UnicodeDecodeError:
            continue
    else:
        df = pd.read_csv(CSV_FILE, dtype=str).fillna("")

    for column in COLUMNS:
        if column not in df.columns:
            df[column] = ""

    df["ステータス"] = df["ステータス"].replace(
        {
            "SPI受験済み": "適性検査受験済み",
        }
    )
    df["種別"] = df["種別"].replace(
        {
            "SPI": "適性検査日",
            "SPI日": "適性検査日",
            "締切": "エントリー締切",
        }
    )
    return df[COLUMNS].fillna("")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy().fillna("")
    for column in COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""
    return normalized[COLUMNS].fillna("")


def read_uploaded_csv(uploaded_file) -> pd.DataFrame:
    data = uploaded_file.getvalue()
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            uploaded_df = pd.read_csv(io.BytesIO(data), dtype=str, encoding=encoding).fillna("")
            return normalize_columns(uploaded_df)
        except UnicodeDecodeError:
            continue

    uploaded_df = pd.read_csv(io.BytesIO(data), dtype=str).fillna("")
    return normalize_columns(uploaded_df)


def create_backup() -> None:
    if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"companies_{timestamp}.csv")
    shutil.copy2(CSV_FILE, backup_file)

    backup_files = sorted(
        [name for name in os.listdir(BACKUP_DIR) if name.endswith(".csv")],
        reverse=True,
    )
    for old_name in backup_files[30:]:
        os.remove(os.path.join(BACKUP_DIR, old_name))


def save_data(df: pd.DataFrame, make_backup: bool = True) -> None:
    if make_backup:
        create_backup()

    clean_df = df.copy()
    for column in clean_df.columns:
        if column.startswith("_"):
            clean_df = clean_df.drop(columns=[column])
    clean_df = clean_df.reindex(columns=COLUMNS, fill_value="")
    clean_df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")


def parse_date(value: object):
    if value is None or str(value).strip() == "":
        return pd.NaT
    return pd.to_datetime(value, errors="coerce")


def to_date_input_value(value: object) -> date:
    parsed = parse_date(value)
    if pd.isna(parsed):
        return date.today()
    return parsed.date()


def date_to_str(value: object) -> str:
    if not value:
        return ""
    return str(value)


def split_jobs(value: object) -> list[str]:
    if value is None or str(value).strip() == "":
        return []
    raw = str(value).replace(",", " / ")
    return [part.strip() for part in raw.split("/") if part.strip()]


def build_job_value(selected_jobs: list[str], other_job: str) -> str:
    jobs = [job for job in selected_jobs if job]
    if other_job.strip():
        jobs.append(other_job.strip())
    return " / ".join(dict.fromkeys(jobs))


def is_url(value: object) -> bool:
    text = str(value).strip()
    return text.startswith("http://") or text.startswith("https://")


def normalize_url(value: object) -> str:
    text = str(value).strip()
    if not text:
        return ""
    if text.startswith("http://") or text.startswith("https://"):
        return text
    if "." in text and " " not in text:
        return f"https://{text}"
    return text


def date_label(row: pd.Series) -> str:
    single = str(row.get("単日", "")).strip()
    start = str(row.get("開始日", "")).strip()
    end = str(row.get("終了日", "")).strip()

    if single:
        return single
    if start and end:
        return f"{start} 〜 {end}"
    if start:
        return start
    if end:
        return end
    return "未定"


def next_event_date(row: pd.Series):
    dates = [parse_date(row.get(column, "")) for column in ("単日", "開始日", "終了日")]
    dates = [value for value in dates if not pd.isna(value)]
    if not dates:
        return pd.NaT
    return min(dates)


def date_fields(prefix: str, kind: str, row: pd.Series | None = None) -> tuple[str, str, str]:
    row = row if row is not None else pd.Series(dtype=object)
    start_date = ""
    end_date = ""
    single_date = ""

    if kind == "インターン期間":
        col1, col2 = st.columns(2)
        with col1:
            start_date = date_to_str(
                st.date_input(
                    "開始日",
                    value=to_date_input_value(row.get("開始日", "")),
                    key=f"{prefix}_start_date",
                )
            )
        with col2:
            end_date = date_to_str(
                st.date_input(
                    "終了日",
                    value=to_date_input_value(row.get("終了日", "")),
                    key=f"{prefix}_end_date",
                )
            )
    elif kind == "インターン開始日":
        start_date = date_to_str(
            st.date_input(
                "開始日",
                value=to_date_input_value(row.get("開始日", "")),
                key=f"{prefix}_start_only",
            )
        )
    elif kind == "インターン終了日":
        end_date = date_to_str(
            st.date_input(
                "終了日",
                value=to_date_input_value(row.get("終了日", "")),
                key=f"{prefix}_end_only",
            )
        )
    elif kind not in {"落選", "未定"}:
        single_date = date_to_str(
            st.date_input(
                "日付",
                value=to_date_input_value(row.get("単日", "")),
                key=f"{prefix}_single_date",
            )
        )

    return start_date, end_date, single_date


def render_card(row: pd.Series, status_colors: dict[str, str]) -> None:
    company = html.escape(str(row.get("企業名", "")))
    company_id = html.escape(str(row.get("企業ID", "")))
    job = html.escape(str(row.get("職種", "")))
    status = html.escape(str(row.get("ステータス", "")))
    kind = html.escape(str(row.get("種別", "")))
    memo = html.escape(str(row.get("メモ", "")))
    date_text = html.escape(date_label(row))
    bg = status_colors.get(str(row.get("ステータス", "")), "#ffffff")

    job_tags = "".join(f'<span class="tag">{html.escape(tag)}</span>' for tag in split_jobs(job))
    memo_html = f"<br>メモ：{memo}" if memo else ""
    id_html = f"<br>企業ID：{company_id}" if company_id else ""

    st.markdown(
        f"""
        <div class="career-card" style="background:{bg};">
            <div class="career-title">🌳 {company}</div>
            <div>{job_tags}</div>
            <div class="career-meta">
                ステータス：{status} / {kind}<br>
                日付：{date_text}
                {id_html}
                {memo_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def upsert_form(prefix: str, df: pd.DataFrame, row_id: int | None = None) -> None:
    is_edit = row_id is not None
    row = df.loc[row_id] if is_edit else pd.Series(dtype=object)
    selected_existing_jobs = [job for job in split_jobs(row.get("職種", "")) if job in JOB_OPTIONS]
    other_existing_jobs = [job for job in split_jobs(row.get("職種", "")) if job not in JOB_OPTIONS]

    with st.form(f"{prefix}_form", clear_on_submit=not is_edit):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("企業名", value=str(row.get("企業名", "")), key=f"{prefix}_name")
            company_id = st.text_input("企業ID", value=str(row.get("企業ID", "")), key=f"{prefix}_id")
            company_hp = st.text_input(
                "企業HP",
                value=str(row.get("企業HP", "")),
                placeholder="https://...",
                key=f"{prefix}_hp",
            )
        with col2:
            status_default = str(row.get("ステータス", STATUS_OPTIONS[0]))
            if status_default not in STATUS_OPTIONS:
                status_default = STATUS_OPTIONS[0]
            status = st.selectbox(
                "ステータス",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(status_default),
                key=f"{prefix}_status",
            )

            kind_default = str(row.get("種別", "未定"))
            if kind_default not in EVENT_OPTIONS:
                kind_default = "未定"
            kind = st.selectbox(
                "種別",
                EVENT_OPTIONS,
                index=EVENT_OPTIONS.index(kind_default),
                key=f"{prefix}_kind",
            )

        selected_jobs = st.multiselect(
            "職種タグ",
            JOB_OPTIONS,
            default=selected_existing_jobs,
            key=f"{prefix}_jobs",
        )
        other_job = st.text_input(
            "その他の職種・コース",
            value=" / ".join(other_existing_jobs),
            key=f"{prefix}_other_job",
        )

        start_date, end_date, single_date = date_fields(prefix, kind, row)
        memo = st.text_area("メモ", value=str(row.get("メモ", "")), key=f"{prefix}_memo")

        submitted = st.form_submit_button("保存" if is_edit else "登録", type="primary")

    if not submitted:
        return

    if not name.strip():
        st.error("企業名は必須です。")
        return

    next_df = df.copy()
    values = {
        "企業名": name.strip(),
        "企業ID": company_id.strip(),
        "企業HP": normalize_url(company_hp),
        "職種": build_job_value(selected_jobs, other_job),
        "ステータス": status,
        "種別": kind,
        "開始日": start_date,
        "終了日": end_date,
        "単日": single_date,
        "メモ": memo.strip(),
    }

    if is_edit:
        for key, value in values.items():
            next_df.loc[row_id, key] = value
    else:
        next_df = pd.concat([next_df, pd.DataFrame([values])], ignore_index=True)

    save_data(next_df)
    st.success("保存しました。")
    st.rerun()


def show_dashboard(df: pd.DataFrame) -> None:
    active_count = len(df[~df["ステータス"].isin(FINAL_STATUSES)])
    interview_count = len(df[df["ステータス"] == "面接中"])
    waiting_count = len(df[df["種別"] == "合否通知日"])
    offer_count = len(df[df["ステータス"] == "内定"])
    fail_count = len(df[df["ステータス"] == "落選"])

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("進行中", active_count)
    col2.metric("面接中", interview_count)
    col3.metric("合否待ち", waiting_count)
    col4.metric("内定", offer_count)
    col5.metric("落選", fail_count)


def show_alerts(df: pd.DataFrame) -> None:
    today = pd.Timestamp.today().normalize()
    alert_rows = []

    for row_id, row in df.iterrows():
        if row["ステータス"] in FINAL_STATUSES:
            continue

        single = parse_date(row["単日"])
        if not pd.isna(single):
            days_left = (single.normalize() - today).days
            if 0 <= days_left <= 3:
                alert_rows.append((days_left, row_id, row["企業名"], row["種別"], "期限"))

        start = parse_date(row["開始日"])
        if not pd.isna(start):
            days_left = (start.normalize() - today).days
            if 0 <= days_left <= 3:
                alert_rows.append((days_left, row_id, row["企業名"], "インターン開始", "開始"))

    st.subheader("アラート")
    if not alert_rows:
        st.info("直近3日以内の締切・開始日はありません。")
        return

    for days_left, _, company, kind, alert_type in sorted(alert_rows):
        if days_left == 0:
            st.error(f"本日：{company} / {kind}")
        elif days_left == 1:
            st.warning(f"あと1日：{company} / {kind}")
        else:
            message = f"あと{days_left}日：{company} / {kind}"
            st.warning(message if alert_type == "期限" else message)


def show_upcoming_events(df: pd.DataFrame) -> None:
    today = pd.Timestamp.today().normalize()
    rows = []

    for _, row in df.iterrows():
        if row["ステータス"] in FINAL_STATUSES:
            continue

        candidates = [
            ("単日", row["単日"], row["種別"]),
            ("開始日", row["開始日"], "インターン開始"),
            ("終了日", row["終了日"], "インターン終了"),
        ]

        for _, value, label in candidates:
            parsed = parse_date(value)
            if pd.isna(parsed):
                continue

            days_left = (parsed.normalize() - today).days
            if days_left < 0:
                continue

            rows.append(
                {
                    "日付": parsed.strftime("%Y-%m-%d"),
                    "残り日数": f"あと{days_left}日" if days_left > 0 else "本日",
                    "企業名": row["企業名"],
                    "予定": label,
                    "ステータス": row["ステータス"],
                }
            )

    st.subheader("直近予定")
    if not rows:
        st.info("今後の予定はまだ登録されていません。")
        return

    upcoming_df = pd.DataFrame(rows).sort_values("日付").head(10)
    st.dataframe(upcoming_df, hide_index=True, use_container_width=True)


def collect_calendar_events(df: pd.DataFrame, year: int, month: int) -> dict[int, list[str]]:
    events: dict[int, list[str]] = {}

    def add_event(value: object, label: str) -> None:
        parsed = parse_date(value)
        if pd.isna(parsed):
            return
        if parsed.year == year and parsed.month == month:
            events.setdefault(parsed.day, []).append(label)

    for _, row in df.iterrows():
        company = str(row["企業名"])
        kind = str(row["種別"])
        if str(row["単日"]).strip():
            add_event(row["単日"], f"{company} / {kind}")
        if str(row["開始日"]).strip():
            add_event(row["開始日"], f"{company} / 開始")
        if str(row["終了日"]).strip():
            add_event(row["終了日"], f"{company} / 終了")

    return events


def show_calendar(df: pd.DataFrame) -> None:
    st.subheader("カレンダー")
    selected_month = st.date_input("表示月", value=date.today())
    year = selected_month.year
    month = selected_month.month
    month_name = f"{year}年{month}月"
    events = collect_calendar_events(df, year, month)

    weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(year, month)
    weekday_names = ["日", "月", "火", "水", "木", "金", "土"]

    html_parts = [f'<div class="calendar-wrap"><h3>{month_name}</h3><div class="calendar-grid">']
    html_parts.extend(f'<div class="calendar-head">{name}</div>' for name in weekday_names)

    for week in weeks:
        for day in week:
            if day == 0:
                html_parts.append('<div class="calendar-day empty"></div>')
                continue

            day_events = events.get(day, [])
            event_html = "".join(
                f'<div class="calendar-event">{html.escape(event)}</div>'
                for event in day_events[:3]
            )
            if len(day_events) > 3:
                event_html += f'<div class="calendar-event">+{len(day_events) - 3}件</div>'

            html_parts.append(
                f'<div class="calendar-day"><div class="calendar-date">{day}</div>{event_html}</div>'
            )

    html_parts.append("</div></div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def show_company_list(df: pd.DataFrame, status_colors: dict[str, str]) -> None:
    st.subheader("登録一覧")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_word = st.text_input("検索", placeholder="企業名・職種・メモで検索")
    with col2:
        status_filter = st.selectbox("ステータス", ["すべて"] + STATUS_OPTIONS)
    with col3:
        sort_type = st.selectbox("並び替え", ["登録順", "企業名順", "単日が近い順", "開始日が近い順"])

    working = df.copy()
    working["_row_id"] = working.index

    if status_filter != "すべて":
        working = working[working["ステータス"] == status_filter]

    if search_word:
        needle = search_word.strip()
        working = working[
            working["企業名"].astype(str).str.contains(needle, case=False, na=False)
            | working["職種"].astype(str).str.contains(needle, case=False, na=False)
            | working["メモ"].astype(str).str.contains(needle, case=False, na=False)
        ]

    if sort_type == "企業名順":
        working = working.sort_values("企業名")
    elif sort_type == "単日が近い順":
        working["_sort_date"] = pd.to_datetime(working["単日"], errors="coerce")
        working = working.sort_values("_sort_date", na_position="last")
    elif sort_type == "開始日が近い順":
        working["_sort_date"] = pd.to_datetime(working["開始日"], errors="coerce")
        working = working.sort_values("_sort_date", na_position="last")

    if working.empty:
        st.info("条件に一致する企業はありません。")
        return

    for _, row in working.iterrows():
        row_id = int(row["_row_id"])
        render_card(row, status_colors)

        action_col1, _ = st.columns([1, 5])
        with action_col1:
            if is_url(row["企業HP"]):
                st.link_button("企業HP", row["企業HP"])

        with st.expander("編集・削除", expanded=False):
            upsert_form(f"edit_{row_id}", df, row_id=row_id)

            st.divider()
            st.caption("削除すると一覧から消えます。保存前のCSVは backups フォルダに自動保存されます。")
            confirm_delete = st.checkbox(
                f"{row['企業名']} を削除する",
                key=f"confirm_delete_{row_id}",
            )
            if st.button("削除を実行", key=f"delete_{row_id}", disabled=not confirm_delete):
                next_df = df.drop(row_id).reset_index(drop=True)
                save_data(next_df)
                st.success("削除しました。")
                st.rerun()


def show_settings(df: pd.DataFrame) -> None:
    st.subheader("データ管理")
    st.caption(f"CSV保存先：{CSV_FILE}")

    st.download_button(
        "CSVをダウンロード",
        data=df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name="companies.csv",
        mime="text/csv",
    )

    st.divider()
    st.markdown("#### CSV取り込み")
    uploaded_file = st.file_uploader("companies.csv を選択", type=["csv"])
    import_mode = st.radio("取り込み方法", ["上書き", "追加"], horizontal=True)

    if uploaded_file is not None:
        try:
            uploaded_df = read_uploaded_csv(uploaded_file)
            st.caption(f"読み込み件数：{len(uploaded_df)} 件")

            if st.button("CSVを取り込む", type="primary"):
                if import_mode == "追加":
                    next_df = pd.concat([df, uploaded_df], ignore_index=True)
                else:
                    next_df = uploaded_df
                save_data(next_df)
                st.success("CSVを取り込みました。")
                st.rerun()
        except Exception as exc:
            st.error(f"CSVを読み込めませんでした：{exc}")

    st.divider()
    st.markdown("#### バックアップ")
    if os.path.exists(BACKUP_DIR):
        backup_files = sorted(
            [name for name in os.listdir(BACKUP_DIR) if name.endswith(".csv")],
            reverse=True,
        )
    else:
        backup_files = []

    if not backup_files:
        st.info("バックアップはまだありません。")
    else:
        st.caption("直近のバックアップ")
        for name in backup_files[:5]:
            path = os.path.join(BACKUP_DIR, name)
            size_kb = os.path.getsize(path) / 1024
            st.write(f"{name} / {size_kb:.1f} KB")


def main() -> None:
    st.sidebar.title("Career Tree")
    dark_mode = st.sidebar.toggle("ダークモード", value=False)
    apply_style(dark_mode)
    status_colors = DARK_STATUS_COLORS if dark_mode else LIGHT_STATUS_COLORS

    st.title("🌳 Career Tree")
    st.caption("就活・インターンの企業管理、締切管理、日程管理をまとめるダッシュボード")

    df = read_csv_safely()

    tab_dashboard, tab_register, tab_list, tab_calendar, tab_settings = st.tabs(
        ["ダッシュボード", "登録", "一覧・編集", "カレンダー", "データ"]
    )

    with tab_dashboard:
        show_dashboard(df)
        show_alerts(df)
        show_upcoming_events(df)

    with tab_register:
        st.subheader("新規登録")
        upsert_form("new", df)

    with tab_list:
        show_company_list(df, status_colors)

    with tab_calendar:
        show_calendar(df)

    with tab_settings:
        show_settings(df)


if __name__ == "__main__":
    main()
