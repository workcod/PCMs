import os
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "poll"

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

import streamlit as st
import pandas as pd
import pythoncom
import win32com.client
import sqlite3
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

st.set_page_config(page_title="Shabakkat Team Dashboard", layout="wide")

# إعدادات ثابتة
APP_BG_PATH = r"D:\\download1.jpg"
LOGIN_BG_PATH = r"D:\\Screenshot 2025-05-28 121615.png"
VALID_USERNAME = "mohamed.hassan"
VALID_PASSWORD = "Moody@123"
DB_PATH = "pcm_data.db"
FIELDS = [
    "PCM ID", "TT ID", "Title", "Site ID", "Alarm status", "Cleared time", "Duration", "Region", "Impact",
    "Fault First Occur Time", "Fault Level", "Received Time",
    "Power Type", "BB Status", "EOL Gen", "Site Owner", "Connectivity",
]
FAULT_LEVELS = ["Emergency", "Critical", "Major", "Minor"]
CORE_SITE_IDS = set([
    "TBK2013", "TBK2M2013", "TBK2M4013", "TBK2M8013", "TBK2MN2013",
    "SAK0585", "SAK2M1585", "SAK2M3585", "SAK2M7585", "SAK2MN0585",
    "JBL0465", "JBL2M1465", "JBL2M3465", "JBL2M7465", "JBL2MN0465",
    "ARR0518", "ARR2M1518", "ARR2M3518", "ARR2M7518", "ARR2MN0518",
    "DAM6092", "DAM2U6192", "DAM2U6392", "DAM2U6792",
    "YNB0155", "YNB2M1155", "YNB2M3155", "YNB2M7155", "YNB2MN0155",
    "MAK0106", "MAK1M3106", "MAK1M9106", "MAK1MNC0106",
    "HAJ0164", "HAJ0102",
    "DM1", "MD1", "RY4", "RY2", "RY1", "JD1", "JD2", "JB1", "HF1", "HB1",
    "AR1", "SK1", "YB2", "TB1", "HL1", "MD2", "JZ1", "AB1", "BR1",
    "KJ1", "RY3", "JD3", "TF1", "HA1", "MK1", "MK4", "HM1", "KB2", "HQ2"
])
EMAIL_ACCOUNT = "Mohamed.Mahmoud@Shabakkatksa.com"
MAIL_FOLDER = "PCMs"
DB_FILE_PATH = r"D:\New folder (4)\data base.xlsx"
PCM_SHEET_NAME = "PCM"
DURATION_COL = "Duration"
REGIONS = ["Region_1", "Region_2", "Region_3", "Region_4", "Region_5", "Region_6"]

# CSS عام
st.markdown("""
<style>
.block-container {
    padding: 0.07rem !important;
    max-width: 100vw !important;
    background: rgba(255,255,255,0.98);
}
h1, h2, h3 {
    margin-top: 0.04rem !important;
    margin-bottom: 0.09rem !important;
}
.dashboard-clock {
    font-size: 0.85rem !important;
    color: #1b2436;
    text-align: center;
    font-weight: bold;
    margin-top: -0.13rem !important;
    margin-bottom: -0.09rem !important;
}
.stDownloadButton {
    margin-top: 0.07rem !important;
    margin-bottom: 0.07rem !important;
}
.stSelectbox>div>div {
    font-size: 1.07rem !important;
}
</style>
""", unsafe_allow_html=True)

def clean_tt_id(val):
    if pd.isnull(val):
        return ""
    val = str(val).strip()
    if val.endswith('.0'):
        val = val[:-2]
    if "e+" in val or "E+" in val:
        try:
            val = str(int(float(val)))
        except:
            pass
    val = val.replace('\u202a', '').replace('\u202c', '').replace('\u200e', '')
    return val

def set_dashboard_background():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("file://{APP_BG_PATH}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            min-height: 100vh;
        }}
        </style>
        """, unsafe_allow_html=True
    )

def set_login_background():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("file://{LOGIN_BG_PATH}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            min-height: 100vh;
        }}
        .login-card {{
            background: rgba(255,255,255,0.96);
            padding: 2.5rem 2rem 2rem 2rem;
            border-radius: 1.25rem;
            box-shadow: 0 8px 32px 0 rgba(31,38,135,0.20);
            max-width: 370px;
            margin: 7rem auto 2rem auto;
            border: 2px solid #4B8BBE;
        }}
        .login-title {{
            color: #4B8BBE;
            text-align: center;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 2rem;
            letter-spacing: 1px;
        }}
        </style>
        """, unsafe_allow_html=True
    )

def login_screen():
    set_login_background()
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🔐 Login to Shabakkat Dashboard</div>', unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if username == VALID_USERNAME and password == VALID_PASSWORD and username.endswith(".hassan"):
                st.session_state["authenticated"] = True
                st.success("✅ Login successful!")
                return
            else:
                st.error("❌ Invalid username or password, or username does not end with .hassan.")
    st.markdown('</div>', unsafe_allow_html=True)

def create_db_and_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS pcm_data ({",".join(['"'+c+'"'+' TEXT' for c in FIELDS])})""")
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS frt_data ("Ticket ID" TEXT,"Fault Recovery Time(Process TT)" TEXT,"Service Interruption Time(Process TT)" TEXT)""")
    conn.commit()
    conn.close()

def save_to_sqlite(df):
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("pcm_data", conn, if_exists="replace", index=False)
    conn.close()

def read_from_sqlite():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM pcm_data", conn)
    except Exception:
        df = pd.DataFrame(columns=FIELDS)
    conn.close()
    return df

def save_frt_to_sqlite(frt_df):
    cols = ["Ticket ID", "Fault Recovery Time(Process TT)", "Service Interruption Time(Process TT)"]
    for col in cols:
        if col not in frt_df.columns:
            frt_df[col] = ""
    frt_df = frt_df[cols]
    conn = sqlite3.connect(DB_PATH)
    frt_df.to_sql("frt_data", conn, if_exists="replace", index=False)
    conn.close()

def read_frt_from_sqlite():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM frt_data", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def extract_detail(body, keyword):
    for line in body.split("\n"):
        if line.strip().startswith(keyword):
            return line.split(":", 1)[1].strip()
    return ""

def add_cleared_time_column(df):
    if "Cleared time" not in df.columns:
        alarm_idx = df.columns.get_loc("Alarm status")
        df.insert(alarm_idx + 1, "Cleared time", "")

def add_duration_column(df):
    if DURATION_COL not in df.columns:
        cleared_idx = df.columns.get_loc("Cleared time")
        df.insert(cleared_idx + 1, DURATION_COL, "")

def update_cleared_time_column(df, tt_to_frt):
    if tt_to_frt:
        df['TT ID'] = df['TT ID'].apply(clean_tt_id)
        df.loc[:, "Cleared time"] = df["TT ID"].map(lambda x: tt_to_frt.get(x, ""))
    else:
        df.loc[:, "Cleared time"] = ""

def update_duration_column(df, tt_to_duration):
    if tt_to_duration:
        df['TT ID'] = df['TT ID'].apply(clean_tt_id)
        df.loc[:, DURATION_COL] = df["TT ID"].map(lambda x: tt_to_duration.get(x, ""))
    else:
        df.loc[:, DURATION_COL] = ""

def sync_alarm_status_with_cleared_time(df):
    df.loc[:, "Alarm status"] = df["Cleared time"].apply(
        lambda x: "Cleared" if pd.notnull(x) and str(x).strip() != "" else "Active"
    )

def enrich_with_excel_data(df, db_file_path, FIELDS):
    import openpyxl
    db_wb = openpyxl.load_workbook(db_file_path, data_only=True)
    db_ws = db_wb.active
    db_data = [
        {
            "Site ID": row[0],
            "2G Site ID": row[1],
            "3G Site ID": row[2],
            "4G Site ID": row[3],
            "5G Site ID": row[4],
            "Power Type": row[5],
            "BB Status": row[6],
            "EOL Gen": row[7],
            "Site Owner": row[8],
            "Connectivity": row[9]
        }
        for row in db_ws.iter_rows(min_row=2, values_only=True)
    ]
    enriched = []
    for _, row in df.iterrows():
        site_id = row["Site ID"]
        match = next(
            (item for item in db_data if site_id in (
                str(item["Site ID"]), str(item["2G Site ID"]), str(item["3G Site ID"]),
                str(item["4G Site ID"]), str(item["5G Site ID"])
            )), {}
        )
        enriched_row = list(row.values)
        missing_fields_count = len(FIELDS) - len(enriched_row)
        if missing_fields_count > 0:
            enriched_row += [
                match.get("Power Type", ""),
                match.get("BB Status", ""),
                match.get("EOL Gen", ""),
                match.get("Site Owner", ""),
                match.get("Connectivity", "")
            ][:missing_fields_count]
        enriched.append(enriched_row)
    enriched_df = pd.DataFrame(enriched, columns=FIELDS)
    return enriched_df

def load_emails_fast(since_time=None, max_minutes=1440):
    pythoncom.CoInitialize()
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    account = next((folder for folder in outlook.Folders if folder.Name == EMAIL_ACCOUNT), None)
    if not account:
        st.error("Email account not found.")
        return pd.DataFrame()
    folder = next((f for f in account.Folders if f.Name == MAIL_FOLDER), None)
    if not folder:
        st.error(f"Folder '{MAIL_FOLDER}' not found.")
        return pd.DataFrame()

    messages = folder.Items
    messages.Sort("[ReceivedTime]", True)
    latest_time = datetime.now() - timedelta(minutes=max_minutes)
    records = []
    for msg in messages:
        if msg.Class != 43:
            continue
        received_time = msg.ReceivedTime
        r_time_naive = received_time.replace(tzinfo=None)
        if since_time and r_time_naive <= since_time:
            break
        if r_time_naive < latest_time:
            break
        body = msg.Body
        received_str = r_time_naive.strftime("%Y-%m-%d %H:%M:%S")
        details = (
            extract_detail(body, "PCM ID:"),
            extract_detail(body, "TT ID:"), extract_detail(body, "Title:"),
            extract_detail(body, "Site ID:"),
            "Active",
            "",
            "",
            extract_detail(body, "Region:"), extract_detail(body, "Impact:"),
            extract_detail(body, "Fault First Occur Time:"), extract_detail(body, "Fault Level:"), received_str
        )
        records.append(details)
    df = pd.DataFrame(records, columns=FIELDS[:12])
    df.dropna(subset=["PCM ID"], inplace=True)
    df.drop_duplicates(subset=["PCM ID"], keep="first", inplace=True)
    if os.path.exists(DB_FILE_PATH):
        try:
            df = enrich_with_excel_data(df, DB_FILE_PATH, FIELDS)
        except Exception as e:
            st.error(f"Error loading DB file for enrichment: {e}")
    else:
        for col in FIELDS[12:]:
            df[col] = ""
    return df

def load_frt_ticket_id_to_time_and_duration(frt_source):
    try:
        if isinstance(frt_source, pd.DataFrame):
            frt_df = frt_source
        else:
            frt_df = pd.read_excel(frt_source)
        if (
            "Ticket ID" in frt_df.columns and
            "Fault Recovery Time(Process TT)" in frt_df.columns and
            "Service Interruption Time(Process TT)" in frt_df.columns
        ):
            frt_df["Ticket ID"] = frt_df["Ticket ID"].apply(clean_tt_id)
            tt_to_frt = dict(
                (clean_tt_id(k), str(v).strip() if pd.notnull(v) and v != "" else "")
                for k, v in zip(frt_df["Ticket ID"], frt_df["Fault Recovery Time(Process TT)"])
            )
            tt_to_duration = dict(
                (clean_tt_id(k), str(v).strip() if pd.notnull(v) and v != "" else "")
                for k, v in zip(frt_df["Ticket ID"], frt_df["Service Interruption Time(Process TT)"])
            )
            return tt_to_frt, tt_to_duration
    except Exception:
        pass
    return {}, {}

def dashboard():
    set_dashboard_background()
    st_autorefresh(interval=60000, key="page-refresh")
    try:
        st.image(r"D:\1519863875658.jpg", width=40)
    except Exception:
        st.markdown("<div style='height:7px'></div>", unsafe_allow_html=True)
    st.markdown(
        "<h1 style='text-align:center;color:#1765a3;font-size:1.3rem;margin-bottom:0.12rem;margin-top:0.01rem;font-family:Tahoma,sans-serif;'>Shabakkat Team Dashboard</h1>",
        unsafe_allow_html=True
    )
    now = datetime.now()
    clock_placeholder = st.empty()
    clock_placeholder.markdown(
        f"<div class='dashboard-clock'>{now.strftime('%H:%M:%S')}</div>",
        unsafe_allow_html=True,
    )

    # زر Fetch Now صغير
    st.markdown("""
    <style>
    #fetch-now-btn button {
        width: 90px !important;
        height: 32px !important;
        font-size: 1rem !important;
        border-radius: 8px !important;
        background: linear-gradient(90deg,#f4faff 0,#e2f1ff 80%);
        color: #1765a3;
        border: 1.3px solid #8ad8ff;
        font-family: 'Tahoma', Arial, sans-serif;
        font-weight: bold;
        letter-spacing: 0.5px;
    }
    #fetch-now-btn button:hover {
        background: #e6f7ff;
        color: #1765a3;
        border: 1.5px solid #1765a3;
    }
    </style>
    """, unsafe_allow_html=True)
    force_refresh = st.button("🔄 Fetch Now", key="fetch-now-btn", help="Refresh data")

    uploaded_frt = st.sidebar.file_uploader(
        "Upload FRT Excel file (optional override)", 
        type=["xlsx", "xls"]
    )
    if uploaded_frt is not None:
        frt_df = pd.read_excel(uploaded_frt)
        save_frt_to_sqlite(frt_df)
    else:
        frt_df = read_frt_from_sqlite() if os.path.exists(DB_PATH) else pd.DataFrame()
    create_db_and_table()
    if "last_received_time" not in st.session_state or force_refresh:
        st.session_state["last_received_time"] = None
    new_df = load_emails_fast(since_time=st.session_state["last_received_time"], max_minutes=1440)
    if not new_df.empty:
        st.session_state["last_received_time"] = pd.to_datetime(new_df["Received Time"]).max()
    old_df = read_from_sqlite()
    for df in [new_df, old_df]:
        if not df.empty:
            add_duration_column(df)
            if "Alarm status" not in df.columns:
                idx = df.columns.get_loc("Site ID") + 1
                df.insert(idx, "Alarm status", "Active")
            add_cleared_time_column(df)
    if not new_df.empty:
        combined_df = pd.concat([new_df, old_df], ignore_index=True)
        combined_df.drop_duplicates(subset=["PCM ID"], keep="first", inplace=True)
        add_duration_column(combined_df)
        add_cleared_time_column(combined_df)
        save_to_sqlite(combined_df)
    else:
        combined_df = old_df
        add_duration_column(combined_df)
        add_cleared_time_column(combined_df)
    if not frt_df.empty:
        tt_to_frt, tt_to_duration = load_frt_ticket_id_to_time_and_duration(frt_df)
    else:
        tt_to_frt, tt_to_duration = {}, {}
    update_cleared_time_column(combined_df, tt_to_frt)
    update_duration_column(combined_df, tt_to_duration)
    sync_alarm_status_with_cleared_time(combined_df)
    if combined_df.empty:
        st.info("No data available.")
        return

    now = datetime.now()
    combined_df['Received Time'] = pd.to_datetime(combined_df['Received Time'], errors='coerce')
    escalated_mask = (combined_df["Alarm status"] == "Active") & (combined_df['Received Time'].notnull()) & ((now - combined_df['Received Time']).dt.total_seconds() > 2*3600)
    summary = {
        "all_count": len(combined_df),
        "cleared_count": len(combined_df[combined_df["Alarm status"] == "Cleared"]),
        "active_count": len(combined_df[combined_df["Alarm status"] == "Active"]),
        "escalated_count": escalated_mask.sum(),
        "emergency_count": len(combined_df[combined_df["Fault Level"] == "Emergency"]),
        "critical_count": len(combined_df[combined_df["Fault Level"] == "Critical"]),
        "major_count": len(combined_df[combined_df["Fault Level"] == "Major"]),
        "minor_count": len(combined_df[combined_df["Fault Level"] == "Minor"]),
    }
    card_labels = [
        ("Total Faults", summary["all_count"], "#2196f3", "#e3f2fd"),
        ("Active Faults", summary["active_count"], "#1565c0", "#e6eeff"),
        ("Cleared Faults", summary["cleared_count"], "#43a047", "#e8f5e9"),
        ("Escalated Faults", summary["escalated_count"], "#e65100", "#ffecb3"),
    ]
    card_keys = ["All", "Active", "Cleared", "Escalated"]

    # كروت السمري الصغيرة مع وميض أحمر عند التغيير
    if "summary_card_prev" not in st.session_state:
        st.session_state["summary_card_prev"] = [0, 0, 0, 0]
    if "summary_card_flash_time" not in st.session_state:
        st.session_state["summary_card_flash_time"] = [0, 0, 0, 0]
    FLASH_DURATION = 2  # ثواني
    now_sec = datetime.now().timestamp()
    cols = st.columns([1, 1, 1, 1], gap="small")
    for i, (label, value, color, bg) in enumerate(card_labels):
        prev = st.session_state["summary_card_prev"][i]
        flash_time = st.session_state["summary_card_flash_time"][i]
        changed = value != prev
        if changed:
            flash_time = now_sec
        flash = flash_time and (now_sec - flash_time < FLASH_DURATION)
        card_bg = "#ffeaea" if flash else bg  # أحمر فاتح عند التغيير
        card_border = color
        with cols[i]:
            st.markdown(
                f"""
                <div style="
                    width: 170px; max-width: 200px; min-width: 120px;
                    height: 60px;
                    border-radius: 15px;
                    border: 2.5px solid {card_border};
                    background: {card_bg};
                    color: #1b2436;
                    font-size:1.08rem;
                    font-family: 'Tahoma', Arial, sans-serif;
                    font-weight: 600;
                    box-shadow: 0 2px 16px #00000018;
                    display: flex; flex-direction: column; align-items: center; justify-content: center;
                    margin: auto;
                    transition: background 0.3s;
                    ">
                    <span style="font-size:1.5rem; font-weight: bold; color: {card_border}; letter-spacing: 1px;">{value}</span>
                    <span style="font-size:1.04rem; color: #1b2436; opacity:0.86">{label}</span>
                </div>
                """, unsafe_allow_html=True
            )
        st.session_state["summary_card_prev"][i] = value
        st.session_state["summary_card_flash_time"][i] = flash_time if flash else (flash_time if changed else 0)

    with st.sidebar:
        choice = option_menu(
            "Sidebar",
            [
                "All", *FAULT_LEVELS, "Core & BSC",
                "Active", "Cleared", "Escalated", "Latis", "Regions"
            ],
            icons=[
                "list", "fire", "exclamation-circle", "bug", "info", "cpu", "globe", "moon-stars", "map"
            ],
            menu_icon="cast", default_index=0,
            styles={
                "container": {"padding": "5px", "background-color": "#f8f9fa"},
                "icon": {"color": "black", "font-size": "18px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin": "2px"},
                "nav-link-selected": {"background-color": "#1765a3", "color": "white"},
            },
        )
        if choice != st.session_state.get("side_choice", "All"):
            st.session_state["side_choice"] = choice

    selected = st.session_state.get("side_choice", "All")
    filtered_df = combined_df

    if selected == "All":
        st.subheader(f"All Faults ({len(filtered_df)})")
    elif selected == "Active":
        filtered_df = combined_df[combined_df["Alarm status"] == "Active"]
        st.subheader(f"Active Faults ({len(filtered_df)})")
    elif selected == "Cleared":
        filtered_df = combined_df[combined_df["Alarm status"] == "Cleared"]
        st.subheader(f"Cleared Faults ({len(filtered_df)})")
    elif selected == "Escalated":
        filtered_df = combined_df[escalated_mask]
        st.subheader(f"Escalated Faults ({len(filtered_df)})")
    elif selected == "Emergency":
        filtered_df = combined_df[combined_df["Fault Level"] == "Emergency"]
        st.subheader(f"Emergency Faults ({len(filtered_df)})")
    elif selected == "Critical":
        filtered_df = combined_df[combined_df["Fault Level"] == "Critical"]
        st.subheader(f"Critical Faults ({len(filtered_df)})")
    elif selected == "Major":
        filtered_df = combined_df[combined_df["Fault Level"] == "Major"]
        st.subheader(f"Major Faults ({len(filtered_df)})")
    elif selected == "Minor":
        filtered_df = combined_df[combined_df["Fault Level"] == "Minor"]
        st.subheader(f"Minor Faults ({len(filtered_df)})")
    elif selected == "Core & BSC":
        filtered_df = combined_df[combined_df["Site ID"].isin(CORE_SITE_IDS)]
        st.subheader(f"Core & BSC Sites ({len(filtered_df)})")
    elif selected == "Latis":
        filtered_df = combined_df[combined_df["Site Owner"].str.strip().str.lower() == "latis"]
        st.subheader(f"Latis Sites ({len(filtered_df)})")
    elif selected == "Regions":
        region = st.selectbox("Choose the area for filtering", REGIONS, key="region_select")
        filtered_df = combined_df[combined_df["Region"].str.strip().str.lower() == region.lower()]
        st.subheader(f"Regional results: {region} ({len(filtered_df)})")
    else:
        st.subheader(f"All Faults ({len(filtered_df)})")

    search_txt = st.text_input("Quick search (PCM ID, TT ID, Site ID, Title)", key="search_txt")
    if search_txt.strip():
        search_txt_lower = search_txt.strip().lower()
        mask = (
            filtered_df["PCM ID"].astype(str).str.lower().str.contains(search_txt_lower) |
            filtered_df["TT ID"].astype(str).str.lower().str.contains(search_txt_lower) |
            filtered_df["Site ID"].astype(str).str.lower().str.contains(search_txt_lower) |
            filtered_df["Title"].astype(str).str.lower().str.contains(search_txt_lower)
        )
        filtered_df = filtered_df[mask]

    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="Download Filtered Data (Excel)",
        data=csv,
        file_name='filtered_faults.csv',
        mime='text/csv',
        use_container_width=True,
    )

    st.dataframe(filtered_df, use_container_width=True, height=700)

def main():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]:
        dashboard()
    else:
        login_screen()

if __name__ == "__main__":
    main()