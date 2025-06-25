import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

st.set_page_config(page_title="Shabakkat Team Dashboard", layout="wide")

# الأعمدة المطلوبة
FIELDS = [
    "PCM ID", "TT ID", "Title", "Site ID", "Alarm status", "Cleared time", "Duration", "Region", "Impact",
    "Fault First Occur Time", "Fault Level", "Received Time",
    "Power Type", "BB Status", "EOL Gen", "Site Owner", "Connectivity"
]
FAULT_LEVELS = ["Emergency", "Critical", "Major", "Minor"]
REGIONS = ["Region_1", "Region_2", "Region_3", "Region_4", "Region_5", "Region_6"]

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

def main():
    st.title("Shabakkat Team Dashboard")

    st.markdown(
        """
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
        """, unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader("ارفع ملف Excel للـ PCM (يجب أن يحتوي الأعمدة المطلوبة)", type=["xlsx", "xls"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        # تأكد من وجود الأعمدة المطلوبة كلها
        for col in FIELDS:
            if col not in df.columns:
                df[col] = ""
        df = df[FIELDS]

        with st.sidebar:
            choice = option_menu(
                "Sidebar",
                ["All", *FAULT_LEVELS, "Active", "Cleared", "Regions"],
                icons=["list", "fire", "exclamation-circle", "bug", "info", "moon-stars", "globe", "check", "map"],
                menu_icon="cast", default_index=0,
                styles={
                    "container": {"padding": "5px", "background-color": "#f8f9fa"},
                    "icon": {"color": "black", "font-size": "18px"},
                    "nav-link": {"font-size": "16px", "text-align": "left", "margin": "2px"},
                    "nav-link-selected": {"background-color": "#1765a3", "color": "white"},
                },
            )

        filtered_df = df

        if choice == "All":
            st.subheader(f"All Faults ({len(filtered_df)})")
        elif choice == "Active":
            filtered_df = df[df["Alarm status"] == "Active"]
            st.subheader(f"Active Faults ({len(filtered_df)})")
        elif choice == "Cleared":
            filtered_df = df[df["Alarm status"] == "Cleared"]
            st.subheader(f"Cleared Faults ({len(filtered_df)})")
        elif choice in FAULT_LEVELS:
            filtered_df = df[df["Fault Level"] == choice]
            st.subheader(f"{choice} Faults ({len(filtered_df)})")
        elif choice == "Regions":
            region = st.selectbox("اختر المنطقة", REGIONS, key="region_select")
            filtered_df = df[df["Region"].str.strip().str.lower() == region.lower()]
            st.subheader(f"Regional results: {region} ({len(filtered_df)})")
        else:
            st.subheader(f"All Faults ({len(filtered_df)})")

        search_txt = st.text_input("بحث سريع (PCM ID, TT ID, Site ID, Title)", key="search_txt")
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
            label="تحميل النتائج كملف Excel",
            data=csv,
            file_name='filtered_faults.csv',
            mime='text/csv',
            use_container_width=True,
        )

        st.dataframe(filtered_df, use_container_width=True, height=700)
    else:
        st.info("يرجى رفع ملف البيانات (Excel) لعرض لوحة البيانات.")

if __name__ == "__main__":
    main()
