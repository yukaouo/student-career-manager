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
DEMO_CSV_FILE = os.path.join(BASE_DIR, "companies_demo.csv")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")

COLUMNS = [
    "企業名",
    "企業ID",
    "企業HP",
    "職種",
    "選考区分",
    "ステータス",
    "種別",
    "開始日",
    "終了日",
    "単日",
    "メモ",
    "ES設問",
    "ES回答",
    "ES提出日",
    "ES結果",
    "ESメモ",
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
    "内定日",
    "落選",
    "未定",
]

JOB_OPTIONS = ["通信", "インフラ", "メーカー", "コンサル", "SIer", "SE"]
FINAL_STATUSES = {"内定", "落選"}
ES_RESULT_OPTIONS = ["未作成", "作成中", "提出済み", "通過", "不通過", "保留"]
SELECTION_TYPE_OPTIONS = ["本選考", "インターン", "その他"]

COMPANY_NAME_FIXES = {
    "センッニコム": "ニッセイコム",
    "ﾆｯｾｲｺﾑ": "ニッセイコム",
    "ニッセイコム ": "ニッセイコム",
    " ニッセイコム": "ニッセイコム",
}

STATUS_ACCENTS = {
    "プレエントリー前": "#7dd3fc",
    "プレエントリー済み": "#34d399",
    "ES提出済み": "#fbbf24",
    "適性検査受験済み": "#a78bfa",
    "面接中": "#fb7185",
    "内定": "#22c55e",
    "落選": "#94a3b8",
}

STATUS_PROGRESS = {
    "プレエントリー前": 8,
    "プレエントリー済み": 18,
    "ES提出済み": 38,
    "適性検査受験済み": 55,
    "面接中": 74,
    "内定": 100,
    "落選": 100,
}

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


def get_config_value(name: str, default: str = "") -> str:
    env_value = os.getenv(name)
    if env_value is not None:
        return str(env_value)

    try:
        secret_value = st.secrets.get(name, default)
    except Exception:
        secret_value = default

    return str(secret_value)


def get_app_mode() -> str:
    mode = get_config_value("CAREER_TREE_MODE", "").strip().lower()
    if mode:
        return mode
    if os.path.exists(CSV_FILE):
        return "local"
    if os.path.exists(DEMO_CSV_FILE):
        return "demo"
    return "local"


def is_read_only_mode() -> bool:
    explicit = get_config_value("CAREER_TREE_READ_ONLY", "").strip().lower()
    if explicit in {"1", "true", "yes", "on"}:
        return True
    if explicit in {"0", "false", "no", "off"}:
        return False
    return get_app_mode() in {"demo", "readonly", "read-only", "cloud"}


def apply_style(dark_mode: bool) -> None:
    bg = "#08111f" if dark_mode else "#f5f8fb"
    panel = "#101927" if dark_mode else "#ffffff"
    panel_soft = "#162234" if dark_mode else "#f8fafc"
    text = "#eef6ff" if dark_mode else "#172033"
    muted = "#9fb0c4" if dark_mode else "#64748b"
    border = "#26364d" if dark_mode else "#dbe4ee"
    input_bg = "#151b25" if dark_mode else "#ffffff"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(circle at 20% 0%, {"#10233a" if dark_mode else "#e7f7ff"} 0, transparent 32%),
                linear-gradient(180deg, {bg} 0%, {"#0c1320" if dark_mode else "#f8fbff"} 100%);
            color: {text};
        }}
        .block-container {{
            max-width: 1040px;
            padding-top: 1.4rem;
            padding-bottom: 6rem;
        }}
        [data-testid="stSidebar"] {{
            background: {panel};
        }}
        div[data-testid="stTabs"] div[role="tablist"] {{
            gap: 8px;
            border-bottom: 0;
        }}
        div[data-testid="stTabs"] button[role="tab"] {{
            background: {panel_soft};
            border: 1px solid {border};
            border-radius: 999px;
            color: {text};
            min-height: 42px;
            padding: 8px 16px;
        }}
        div[data-testid="stTabs"] button[aria-selected="true"] {{
            background: linear-gradient(135deg, #5eead4, #60a5fa);
            color: #06111f;
            border-color: transparent;
            font-weight: 800;
        }}
        .app-hero {{
            background:
                linear-gradient(135deg, {"#101b2c" if dark_mode else "#ffffff"} 0%, {"#13243a" if dark_mode else "#eaf8ff"} 100%);
            border: 1px solid {border};
            border-radius: 8px;
            padding: 22px;
            margin-bottom: 16px;
            box-shadow: 0 18px 42px rgba(2, 8, 23, 0.20);
        }}
        .brand-word {{
            font-size: clamp(2rem, 5vw, 3.4rem);
            line-height: 1;
            font-weight: 900;
            letter-spacing: 0;
            color: {text};
        }}
        .brand-word span {{
            color: #5eead4;
        }}
        .hero-copy {{
            color: {muted};
            font-weight: 700;
            margin-top: 8px;
        }}
        .mode-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 12px;
            border-radius: 999px;
            border: 1px solid {border};
            color: {text};
            background: {"#0e1727" if dark_mode else "#ffffff"};
            font-weight: 800;
            font-size: 0.86rem;
            margin-top: 14px;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 10px;
            margin: 12px 0 18px;
        }}
        .kpi-card {{
            min-height: 86px;
            background: {panel};
            border: 1px solid {border};
            border-top: 3px solid var(--accent);
            border-radius: 8px;
            padding: 12px;
            box-shadow: 0 10px 28px rgba(2, 8, 23, 0.12);
        }}
        .kpi-label {{
            color: {muted};
            font-weight: 800;
            font-size: 0.82rem;
        }}
        .kpi-value {{
            color: {text};
            font-size: 2rem;
            line-height: 1.1;
            font-weight: 900;
            margin-top: 4px;
        }}
        .deadline-list {{
            display: grid;
            gap: 8px;
            margin: 8px 0 18px;
        }}
        .deadline-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            border: 1px solid var(--accent);
            background: color-mix(in srgb, var(--accent) 14%, transparent);
            border-radius: 8px;
            padding: 12px 14px;
            color: {text};
        }}
        .deadline-main {{
            font-weight: 900;
        }}
        .deadline-sub {{
            color: {muted};
            font-size: 0.86rem;
            margin-top: 2px;
        }}
        .deadline-days {{
            white-space: nowrap;
            font-weight: 900;
            color: var(--accent);
        }}
        .career-card, .calendar-wrap {{
            background: {panel};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 14px 34px rgba(2, 8, 23, 0.16);
        }}
        .career-card {{
            border-left: 4px solid var(--accent);
        }}
        .career-title {{
            font-size: 1.25rem;
            font-weight: 900;
            color: {text};
            margin-bottom: 6px;
        }}
        .career-meta {{
            color: {muted};
            line-height: 1.7;
            font-size: 0.94rem;
        }}
        .career-topline {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
        }}
        .status-chip, .deadline-chip {{
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 999px;
            color: {text};
            border: 1px solid var(--accent);
            background: color-mix(in srgb, var(--accent) 16%, transparent);
            font-size: 0.8rem;
            font-weight: 900;
            white-space: nowrap;
        }}
        .deadline-chip {{
            border-color: var(--urgency);
            background: color-mix(in srgb, var(--urgency) 18%, transparent);
            color: var(--urgency);
        }}
        .progress-track {{
            width: 100%;
            height: 8px;
            border-radius: 999px;
            background: {"#263244" if dark_mode else "#e2e8f0"};
            margin: 12px 0 8px;
            overflow: hidden;
        }}
        .progress-bar {{
            height: 100%;
            width: var(--progress);
            border-radius: 999px;
            background: linear-gradient(90deg, #5eead4, var(--accent));
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
        input, textarea, select, div[data-baseweb="select"] > div {{
            background-color: {input_bg} !important;
            border-color: {border} !important;
            color: {text} !important;
            border-radius: 8px !important;
        }}
        div[data-testid="stDataFrame"] {{
            border: 1px solid {border};
            border-radius: 8px;
            overflow: hidden;
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
        .es-archive-card {{
            background: {panel};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 10px;
        }}
        .es-answer {{
            white-space: pre-wrap;
            color: {text};
            line-height: 1.7;
            font-size: 0.92rem;
        }}
        section[data-testid="stSidebar"] button,
        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button,
        div[data-testid="stLinkButton"] > a {{
            min-height: 42px;
        }}
        @media (max-width: 760px) {{
            .block-container {{
                padding-left: 0.75rem;
                padding-right: 0.75rem;
                padding-top: 1rem;
            }}
            .app-hero {{
                padding: 18px;
                margin-left: -2px;
                margin-right: -2px;
            }}
            .kpi-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
            .kpi-card {{
                min-height: 76px;
                padding: 10px;
            }}
            .kpi-value {{
                font-size: 1.65rem;
            }}
            .career-topline {{
                flex-direction: column;
                gap: 8px;
            }}
            .deadline-row {{
                align-items: flex-start;
            }}
            div[data-testid="stHorizontalBlock"] {{
                flex-direction: column;
            }}
            div[data-testid="stHorizontalBlock"] > div {{
                width: 100% !important;
            }}
            div[data-testid="stButton"] > button,
            div[data-testid="stDownloadButton"] > button,
            div[data-testid="stLinkButton"] > a {{
                width: 100%;
            }}
            div[data-testid="stTabs"] div[role="tablist"] {{
                overflow-x: auto;
                white-space: nowrap;
                flex-wrap: nowrap;
            }}
            div[data-testid="stMetric"] {{
                background: {panel};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 8px;
            }}
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
        if os.path.exists(DEMO_CSV_FILE):
            return read_csv_file(DEMO_CSV_FILE)

        df = pd.DataFrame(columns=COLUMNS)
        save_data(df, make_backup=False)
        return df

    return read_csv_file(CSV_FILE)


def read_csv_file(path: str) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            df = pd.read_csv(path, dtype=str, encoding=encoding).fillna("")
            break
        except UnicodeDecodeError:
            continue
    else:
        df = pd.read_csv(path, dtype=str).fillna("")

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
            "インターン期間": "インターン期間",
            "インターン開始日": "インターン期間",
            "インターン終了日": "インターン期間",
            "インターン": "インターン期間",
        }
    )
    df["選考区分"] = df.apply(infer_selection_type, axis=1)
    return df[COLUMNS].fillna("")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy().fillna("")
    for column in COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""
    normalized["種別"] = normalized["種別"].replace(
        {
            "SPI": "適性検査日",
            "SPI日": "適性検査日",
            "締切": "エントリー締切",
            "インターン期間": "インターン期間",
            "インターン開始日": "インターン期間",
            "インターン終了日": "インターン期間",
            "インターン": "インターン期間",
        }
    )
    normalized["選考区分"] = normalized.apply(infer_selection_type, axis=1)
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


def to_optional_date_input_value(value: object):
    parsed = parse_date(value)
    if pd.isna(parsed):
        return None
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


def infer_selection_type(row: pd.Series) -> str:
    current = str(row.get("選考区分", "")).strip()
    if current in SELECTION_TYPE_OPTIONS:
        return current

    text = " ".join(
        str(row.get(column, ""))
        for column in ["種別", "メモ", "職種", "ステータス"]
    )
    if "インターン" in text:
        return "インターン"
    return "本選考"


def is_rejected_row(row: pd.Series) -> bool:
    return str(row.get("ステータス", "")) == "落選" or str(row.get("種別", "")) == "落選"


def is_final_row(row: pd.Series) -> bool:
    return str(row.get("ステータス", "")) in FINAL_STATUSES or str(row.get("種別", "")) == "落選"


def normalize_company_name(value: object) -> str:
    text = str(value).strip()
    text = text.replace("　", " ").strip()
    text = " ".join(text.split())
    return COMPANY_NAME_FIXES.get(text, text)


def find_duplicate_rows(
    df: pd.DataFrame,
    name: str,
    company_id: str,
    current_row_id: int | None = None,
) -> pd.DataFrame:
    name = normalize_company_name(name).casefold()
    company_id = company_id.strip().casefold()

    if not name and not company_id:
        return pd.DataFrame(columns=df.columns)

    working = df.copy()
    if current_row_id is not None and current_row_id in working.index:
        working = working.drop(current_row_id)

    name_match = (
        working["企業名"].astype(str).map(normalize_company_name).str.casefold() == name
        if name
        else pd.Series(False, index=working.index)
    )
    id_match = (
        working["企業ID"].astype(str).str.strip().str.casefold() == company_id
        if company_id
        else pd.Series(False, index=working.index)
    )

    return working[name_match | id_match]


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


def get_status_accent(status: object) -> str:
    return STATUS_ACCENTS.get(str(status), "#5eead4")


def get_status_progress(status: object) -> int:
    return STATUS_PROGRESS.get(str(status), 0)


def next_event_date(row: pd.Series):
    dates = [parse_date(row.get(column, "")) for column in ("単日", "開始日", "終了日")]
    dates = [value for value in dates if not pd.isna(value)]
    if not dates:
        return pd.NaT
    return min(dates)


def deadline_state(row: pd.Series) -> tuple[str, str, str]:
    event_date = next_event_date(row)
    if pd.isna(event_date):
        return "予定未定", "#94a3b8", ""

    days_left = (event_date.normalize() - pd.Timestamp.today().normalize()).days
    if days_left < 0:
        return "期限経過", "#94a3b8", event_date.strftime("%Y-%m-%d")
    if days_left == 0:
        return "本日", "#ef4444", event_date.strftime("%Y-%m-%d")
    if days_left <= 1:
        return "あと1日", "#ef4444", event_date.strftime("%Y-%m-%d")
    if days_left <= 3:
        return f"あと{days_left}日", "#f59e0b", event_date.strftime("%Y-%m-%d")
    return f"あと{days_left}日", "#5eead4", event_date.strftime("%Y-%m-%d")


def render_hero(read_only: bool) -> None:
    today = pd.Timestamp.today()
    mode_label = "閲覧専用" if read_only else "編集可能"
    hero_html = (
        '<div class="app-hero">'
        '<div class="brand-word">CAREER <span>TREE</span></div>'
        '<div class="hero-copy">選考もESも、次の一手がすぐ見える就活ダッシュボード。</div>'
        f'<div class="mode-pill">{mode_label} / {today.month}/{today.day} {today.strftime("%a")}</div>'
        "</div>"
    )
    st.markdown(hero_html, unsafe_allow_html=True)


def render_kpi_tiles(metrics: list[tuple[str, int, str]]) -> None:
    items = []
    for label, value, accent in metrics:
        items.append(
            f'<div class="kpi-card" style="--accent:{accent};">'
            f'<div class="kpi-label">{html.escape(label)}</div>'
            f'<div class="kpi-value">{value}</div>'
            "</div>"
        )

    st.markdown(f'<div class="kpi-grid">{"".join(items)}</div>', unsafe_allow_html=True)


def render_deadline_rows(rows: list[tuple[int, str, str, str]]) -> None:
    if not rows:
        st.info("直近3日以内の締切・開始日はありません。")
        return

    parts = []
    for days_left, company, kind, accent in rows:
        if days_left == 0:
            days_label = "本日"
        else:
            days_label = f"あと{days_left}日"

        parts.append(
            f'<div class="deadline-row" style="--accent:{accent};">'
            "<div>"
            f'<div class="deadline-main">{html.escape(company)}</div>'
            f'<div class="deadline-sub">{html.escape(kind)}</div>'
            "</div>"
            f'<div class="deadline-days">{days_label}</div>'
            "</div>"
        )

    st.markdown(f'<div class="deadline-list">{"".join(parts)}</div>', unsafe_allow_html=True)

def date_fields(prefix: str, kind: str, row: pd.Series | None = None) -> tuple[str, str, str]:
    row = row if row is not None else pd.Series(dtype=object)
    start_date = ""
    end_date = ""
    single_date = ""

    if kind == "インターン期間":
        st.caption("YYYY-MM-DD形式で入力してください。例：2026-08-25")

        col1, col2 = st.columns(2)

        with col1:
            start_date = st.text_input(
                "インターン開始日",
                value=str(row.get("開始日", "")),
                placeholder="2026-08-25",
                key=f"{prefix}_intern_start_text",
            ).strip()

        with col2:
            end_date = st.text_input(
                "インターン終了日",
                value=str(row.get("終了日", "")),
                placeholder="2026-08-29",
                key=f"{prefix}_intern_end_text",
            ).strip()

    elif kind not in {"落選", "未定"}:
        single_date = st.text_input(
            "日付",
            value=str(row.get("単日", "")),
            placeholder="2026-07-01",
            key=f"{prefix}_single_text",
        ).strip()

    return start_date, end_date, single_date

def render_card(row: pd.Series, status_colors: dict[str, str]) -> None:
    company = html.escape(str(row.get("企業名", "")))
    company_id = html.escape(str(row.get("企業ID", "")))
    job = html.escape(str(row.get("職種", "")))
    status_raw = str(row.get("ステータス", ""))
    status = html.escape(status_raw)
    selection_type = html.escape(infer_selection_type(row))
    kind = html.escape(str(row.get("種別", "")))
    memo = html.escape(str(row.get("メモ", "")))
    es_result = html.escape(str(row.get("ES結果", "")))
    es_submitted = html.escape(str(row.get("ES提出日", "")))
    date_text = html.escape(date_label(row))
    accent = get_status_accent(status_raw)
    progress = get_status_progress(status_raw)
    deadline_label, urgency_color, deadline_date = deadline_state(row)

    job_tags = "".join(f'<span class="tag">{html.escape(tag)}</span>' for tag in split_jobs(job))
    memo_html = f"<br>メモ：{memo}" if memo else ""
    id_html = f"<br>企業ID：{company_id}" if company_id else ""
    es_parts = []
    if es_result:
        es_parts.append(f"ES：{es_result}")
    if es_submitted:
        es_parts.append(f"提出日：{es_submitted}")
    es_html = f"<br>{' / '.join(es_parts)}" if es_parts else ""

    card_html = (
        f'<div class="career-card" style="--accent:{accent}; --urgency:{urgency_color}; --progress:{progress}%;">'
        '<div class="career-topline">'
        "<div>"
        f'<div class="career-title">{company}</div>'
        f"<div>{job_tags}</div>"
        "</div>"
        f'<div class="status-chip">{status}</div>'
        "</div>"
        '<div class="progress-track"><div class="progress-bar"></div></div>'
        '<div class="career-meta">'
        f"区分：{selection_type}<br>"
        f"種別：{kind}<br>"
        f"日付：{date_text}"
        f"{id_html}"
        f"{memo_html}"
        f"{es_html}"
        "</div>"
        '<div style="margin-top:10px;">'
        f'<span class="deadline-chip">{html.escape(deadline_label)}</span>'
        f'<span class="career-meta"> {html.escape(deadline_date)}</span>'
        "</div>"
        "</div>"
    )
    st.markdown(card_html, unsafe_allow_html=True)


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
            selection_type_default = infer_selection_type(row)
            selection_type = st.selectbox(
                "選考区分",
                SELECTION_TYPE_OPTIONS,
                index=SELECTION_TYPE_OPTIONS.index(selection_type_default),
                key=f"{prefix}_selection_type",
            )

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

        has_es_archive = bool(
            str(row.get("ES設問", "")).strip()
            or str(row.get("ES回答", "")).strip()
            or str(row.get("ESメモ", "")).strip()
        )
        with st.expander("ESアーカイブ", expanded=has_es_archive):
            es_result_default = str(row.get("ES結果", "未作成"))
            if es_result_default not in ES_RESULT_OPTIONS:
                es_result_default = "未作成"
            es_col1, es_col2 = st.columns(2)
            with es_col1:
                es_result = st.selectbox(
                    "ES状態",
                    ES_RESULT_OPTIONS,
                    index=ES_RESULT_OPTIONS.index(es_result_default),
                    key=f"{prefix}_es_result",
                )
            with es_col2:
                es_submitted_date = st.date_input(
                    "ES提出日",
                    value=to_optional_date_input_value(row.get("ES提出日", "")),
                    key=f"{prefix}_es_submitted_date",
                )

            es_question = st.text_area(
                "ES設問",
                value=str(row.get("ES設問", "")),
                height=100,
                key=f"{prefix}_es_question",
            )
            es_answer = st.text_area(
                "ES回答",
                value=str(row.get("ES回答", "")),
                height=180,
                key=f"{prefix}_es_answer",
            )
            es_memo = st.text_area(
                "ESメモ",
                value=str(row.get("ESメモ", "")),
                height=80,
                key=f"{prefix}_es_memo",
            )

        allow_duplicate = st.checkbox(
            "同じ企業名・企業IDがあっても保存する",
            value=False,
            key=f"{prefix}_allow_duplicate",
        )

        submitted = st.form_submit_button("保存" if is_edit else "登録", type="primary")

    if not submitted:
        return

    clean_name = normalize_company_name(name)
    if not clean_name:
        st.error("企業名は必須です。")
        return

    if clean_name != name.strip():
        st.warning(f"企業名を補正しました：{name.strip()} → {clean_name}")

    duplicate_rows = find_duplicate_rows(df, clean_name, company_id, row_id)
    if not duplicate_rows.empty and not allow_duplicate:
        duplicate_labels = [
            f"{item['企業名']} / ID: {item['企業ID'] or '未入力'} / {item['ステータス']}"
            for _, item in duplicate_rows.head(5).iterrows()
        ]
        st.error("同じ企業名または企業IDの登録があります。確認してから保存してください。")
        st.write(duplicate_labels)
        return

    next_df = df.copy()
    values = {
        "企業名": clean_name,
        "企業ID": company_id.strip(),
        "企業HP": normalize_url(company_hp),
        "職種": build_job_value(selected_jobs, other_job),
        "選考区分": selection_type,
        "ステータス": status,
        "種別": kind,
        "開始日": start_date,
        "終了日": end_date,
        "単日": single_date,
        "メモ": memo.strip(),
        "ES設問": es_question.strip(),
        "ES回答": es_answer.strip(),
        "ES提出日": date_to_str(es_submitted_date),
        "ES結果": es_result,
        "ESメモ": es_memo.strip(),
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
    final_mask = df.apply(is_final_row, axis=1) if not df.empty else pd.Series(dtype=bool)
    rejected_mask = df.apply(is_rejected_row, axis=1) if not df.empty else pd.Series(dtype=bool)
    active_count = len(df[~final_mask]) if not df.empty else 0
    interview_count = len(df[df["ステータス"] == "面接中"])
    waiting_count = len(df[df["種別"] == "合否通知日"])
    offer_count = len(df[df["ステータス"] == "内定"])
    es_count = len(df[df.apply(has_es_content, axis=1)]) if not df.empty else 0
    main_rejected_count = len(df[rejected_mask & (df["選考区分"] == "本選考")]) if not df.empty else 0
    intern_rejected_count = len(df[rejected_mask & (df["選考区分"] == "インターン")]) if not df.empty else 0

    render_kpi_tiles(
        [
            ("進行中", active_count, "#60a5fa"),
            ("面接中", interview_count, "#fb7185"),
            ("合否待ち", waiting_count, "#f59e0b"),
            ("内定", offer_count, "#22c55e"),
            ("本選考落選", main_rejected_count, "#94a3b8"),
            ("インターン落選", intern_rejected_count, "#38bdf8"),
            ("ES保存", es_count, "#5eead4"),
        ]
    )

    st.markdown("#### ステータス別件数")
    status_summary = (
        df["ステータス"]
        .value_counts()
        .reindex(STATUS_OPTIONS, fill_value=0)
        .reset_index()
    )
    status_summary.columns = ["ステータス", "件数"]
    st.dataframe(status_summary, hide_index=True, use_container_width=True)

    st.markdown("#### 選考区分別件数")
    selection_summary = (
        df["選考区分"]
        .value_counts()
        .reindex(SELECTION_TYPE_OPTIONS, fill_value=0)
        .reset_index()
    )
    selection_summary.columns = ["選考区分", "件数"]
    st.dataframe(selection_summary, hide_index=True, use_container_width=True)


def show_alerts(df: pd.DataFrame) -> None:
    today = pd.Timestamp.today().normalize()
    alert_rows = []

    for row_id, row in df.iterrows():
        if is_final_row(row):
            continue

        single = parse_date(row["単日"])
        if not pd.isna(single):
            days_left = (single.normalize() - today).days
            if 0 <= days_left <= 3:
                accent = "#ef4444" if days_left <= 1 else "#f59e0b"
                alert_rows.append((days_left, row["企業名"], row["種別"], accent))

        start = parse_date(row["開始日"])
        if not pd.isna(start):
            days_left = (start.normalize() - today).days
            if 0 <= days_left <= 3:
                accent = "#ef4444" if days_left <= 1 else "#f59e0b"
                alert_rows.append((days_left, row["企業名"], "インターン開始", accent))

    st.subheader("締切アラート")
    render_deadline_rows(sorted(alert_rows))


def show_upcoming_events(df: pd.DataFrame) -> None:
    today = pd.Timestamp.today().normalize()
    rows = []

    for _, row in df.iterrows():
        if is_final_row(row):
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


def collect_calendar_events(
    df: pd.DataFrame,
    year: int,
    month: int,
    selected_types: list[str],
) -> dict[int, list[dict[str, str]]]:
    events: dict[int, list[dict[str, str]]] = {}

    def add_event(row: pd.Series, value: object, label: str, event_type: str) -> None:
        if event_type not in selected_types:
            return

        parsed = parse_date(value)
        if pd.isna(parsed):
            return

        if parsed.year == year and parsed.month == month:
            events.setdefault(parsed.day, []).append(
                {
                    "date": parsed.strftime("%Y-%m-%d"),
                    "company": str(row["企業名"]),
                    "label": label,
                    "status": str(row["ステータス"]),
                }
            )

    for _, row in df.iterrows():
        kind = str(row["種別"])
        if str(row["単日"]).strip():
            add_event(row, row["単日"], kind or "単日予定", "単日")

        start = parse_date(row["開始日"])
        end = parse_date(row["終了日"])
        if not pd.isna(start) and not pd.isna(end):
            if end < start:
                start, end = end, start
            for current in pd.date_range(start.normalize(), end.normalize(), freq="D"):
                if current == start.normalize():
                    add_event(row, current, "インターン開始", "開始日")
                elif current == end.normalize():
                    add_event(row, current, "インターン終了", "終了日")
                else:
                    add_event(row, current, "インターン期間中", "期間中")
        else:
            if not pd.isna(start):
                add_event(row, start, "インターン開始", "開始日")
            if not pd.isna(end):
                add_event(row, end, "インターン終了", "終了日")

    return events


def show_calendar(df: pd.DataFrame) -> None:
    st.subheader("カレンダー")

    today = date.today()
    year_options = list(range(today.year - 1, today.year + 4))
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        year = st.selectbox(
            "年",
            year_options,
            index=year_options.index(today.year),
            key="calendar_year",
        )
    with col2:
        month = st.selectbox(
            "月",
            list(range(1, 13)),
            index=today.month - 1,
            format_func=lambda value: f"{value}月",
            key="calendar_month",
        )
    with col3:
        selected_types = st.multiselect(
            "表示する日付",
            ["単日", "開始日", "期間中", "終了日"],
            default=["単日", "開始日", "期間中", "終了日"],
            key="calendar_event_types",
        )

    month_name = f"{year}年{month}月"
    events = collect_calendar_events(df, year, month, selected_types)

    weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(year, month)
    weekday_names = ["日", "月", "火", "水", "木", "金", "土"]

    st.markdown(f"#### {month_name}")

    header_cols = st.columns(7)
    for col, weekday_name in zip(header_cols, weekday_names):
        col.markdown(f"**{weekday_name}**")

    for week in weeks:
        day_cols = st.columns(7)
        for index, day in enumerate(week):
            col = day_cols[index]
            with col.container(border=True):
                if day == 0:
                    st.write("")
                    st.caption(" ")
                    continue

                if year == today.year and month == today.month and day == today.day:
                    st.markdown(f"**{day} 今日**")
                else:
                    st.markdown(f"**{day}**")

                day_events = events.get(day, [])
                if not day_events:
                    st.caption("予定なし")
                    continue

                for event in day_events[:3]:
                    st.caption(f"{event['company']} / {event['label']}")

                if len(day_events) > 3:
                    st.caption(f"ほか {len(day_events) - 3} 件")

    flat_events = [
        event
        for day in sorted(events)
        for event in events[day]
    ]

    st.markdown("#### 月内予定")
    if not flat_events:
        st.info("この月の予定はありません。")
        return

    calendar_df = pd.DataFrame(flat_events)
    calendar_df = calendar_df.rename(
        columns={
            "date": "日付",
            "company": "企業名",
            "label": "予定",
            "status": "ステータス",
        }
    )
    st.dataframe(calendar_df, hide_index=True, use_container_width=True)


def show_company_list(df: pd.DataFrame, status_colors: dict[str, str], read_only: bool) -> None:
    st.subheader("登録一覧")

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        search_word = st.text_input("検索", placeholder="企業名・職種・メモで検索")
    with col2:
        selection_filter = st.selectbox("選考区分", ["すべて"] + SELECTION_TYPE_OPTIONS)
    with col3:
        status_filter = st.selectbox("ステータス", ["すべて"] + STATUS_OPTIONS)
    with col4:
        sort_type = st.selectbox("並び替え", ["登録順", "企業名順", "単日が近い順", "開始日が近い順"])

    working = df.copy()
    working["_row_id"] = working.index

    if selection_filter != "すべて":
        working = working[working["選考区分"] == selection_filter]

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

        if read_only:
            continue

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


def has_es_content(row: pd.Series) -> bool:
    return any(
        str(row.get(column, "")).strip()
        for column in ["ES設問", "ES回答", "ES提出日", "ESメモ"]
    ) or str(row.get("ES結果", "")).strip() not in {"", "未作成"}


def show_es_archive(df: pd.DataFrame, read_only: bool) -> None:
    st.subheader("ESアーカイブ")

    working = df.copy()
    working["_row_id"] = working.index
    working = working[working.apply(has_es_content, axis=1)]

    if working.empty:
        st.info("ESアーカイブはまだありません。登録・編集画面の「ESアーカイブ」から保存できます。")
        return

    total_count = len(working)
    submitted_count = len(working[working["ES結果"].isin(["提出済み", "通過", "不通過"])])
    passed_count = len(working[working["ES結果"] == "通過"])

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("保存ES", total_count)
    metric_col2.metric("提出済み", submitted_count)
    metric_col3.metric("通過", passed_count)

    filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])
    with filter_col1:
        search_word = st.text_input("ES検索", placeholder="企業名・設問・回答・メモで検索")
    with filter_col2:
        result_filter = st.selectbox("ES状態", ["すべて"] + ES_RESULT_OPTIONS)
    with filter_col3:
        sort_type = st.selectbox("ES並び替え", ["提出日が近い順", "企業名順", "状態順"])

    if result_filter != "すべて":
        working = working[working["ES結果"] == result_filter]

    if search_word:
        needle = search_word.strip()
        working = working[
            working["企業名"].astype(str).str.contains(needle, case=False, na=False)
            | working["ES設問"].astype(str).str.contains(needle, case=False, na=False)
            | working["ES回答"].astype(str).str.contains(needle, case=False, na=False)
            | working["ESメモ"].astype(str).str.contains(needle, case=False, na=False)
        ]

    if sort_type == "企業名順":
        working = working.sort_values("企業名")
    elif sort_type == "状態順":
        working = working.sort_values("ES結果")
    else:
        working["_sort_date"] = pd.to_datetime(working["ES提出日"], errors="coerce")
        working = working.sort_values("_sort_date", ascending=False, na_position="last")

    export_columns = ["企業名", "企業ID", "職種", "選考区分", "ステータス", "ES結果", "ES提出日", "ES設問", "ES回答", "ESメモ"]
    st.download_button(
        "ESアーカイブCSVをダウンロード",
        data=working[export_columns].to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name="es_archive.csv",
        mime="text/csv",
    )

    if working.empty:
        st.info("条件に一致するESはありません。")
        return

    for _, row in working.iterrows():
        row_id = int(row["_row_id"])
        with st.container(border=True):
            header_col1, header_col2 = st.columns([2, 1])
            with header_col1:
                st.markdown(f"**{row['企業名']}**")
                st.caption(f"{row['職種']} / {row['ステータス']}")
            with header_col2:
                st.write(f"ES状態：{row['ES結果'] or '未作成'}")
                st.caption(f"提出日：{row['ES提出日'] or '未入力'}")

            if str(row["ES設問"]).strip():
                st.markdown("**設問**")
                st.write(row["ES設問"])

            if str(row["ES回答"]).strip():
                st.markdown("**回答**")
                st.text_area(
                    "回答本文",
                    value=str(row["ES回答"]),
                    height=180,
                    disabled=True,
                    key=f"archive_answer_{row_id}",
                    label_visibility="collapsed",
                )

            if str(row["ESメモ"]).strip():
                st.caption(f"メモ：{row['ESメモ']}")

            if not read_only:
                with st.expander("このESを編集", expanded=False):
                    upsert_form(f"es_edit_{row_id}", df, row_id=row_id)


def show_settings(df: pd.DataFrame, read_only: bool) -> None:
    st.subheader("データ管理")
    if read_only:
        st.info("閲覧専用モードです。登録・編集・削除・CSV取り込みは無効です。")
    else:
        st.caption(f"CSV保存先：{CSV_FILE}")

    st.download_button(
        "CSVをダウンロード",
        data=df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name="companies.csv",
        mime="text/csv",
    )

    st.divider()
    st.markdown("#### 重複候補")
    normalized_name = df["企業名"].astype(str).map(normalize_company_name).str.casefold()
    normalized_id = df["企業ID"].astype(str).str.strip()
    duplicate_mask = (
        (normalized_name.ne("") & normalized_name.duplicated(keep=False))
        | (
            normalized_id.ne("")
            & normalized_id.duplicated(keep=False)
        )
    )
    duplicate_df = df[duplicate_mask]

    if duplicate_df.empty:
        st.info("企業名・企業IDの重複候補はありません。")
    else:
        st.warning(f"重複候補が {len(duplicate_df)} 件あります。")
        st.dataframe(
            duplicate_df[["企業名", "企業ID", "職種", "選考区分", "ステータス", "種別", "単日"]],
            hide_index=True,
            use_container_width=True,
        )

    if not read_only:
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
    dark_mode = st.sidebar.toggle("集中モード", value=True)
    read_only = is_read_only_mode()
    apply_style(dark_mode)
    status_colors = DARK_STATUS_COLORS if dark_mode else LIGHT_STATUS_COLORS

    render_hero(read_only)
    if read_only:
        st.info("閲覧専用モードで起動中です。スマホから登録済み内容を安全に確認できます。")

    df = read_csv_safely()

    if read_only:
        tab_dashboard, tab_list, tab_calendar, tab_es_archive, tab_settings = st.tabs(
            ["ダッシュボード", "企業一覧", "カレンダー", "ESアーカイブ", "データ"]
        )
    else:
        tab_dashboard, tab_register, tab_list, tab_calendar, tab_es_archive, tab_settings = st.tabs(
            ["ダッシュボード", "登録", "一覧・編集", "カレンダー", "ESアーカイブ", "データ"]
        )

    with tab_dashboard:
        show_dashboard(df)
        show_alerts(df)
        show_upcoming_events(df)

    if not read_only:
        with tab_register:
            st.subheader("新規登録")
            upsert_form("new", df)

    with tab_list:
        show_company_list(df, status_colors, read_only)

    with tab_calendar:
        show_calendar(df)

    with tab_es_archive:
        show_es_archive(df, read_only)

    with tab_settings:
        show_settings(df, read_only)


if __name__ == "__main__":
    main()
