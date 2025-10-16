import streamlit as st
import pandas as pd
import zipfile
import re
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="WhatsApp Chat Extractor", layout="wide")
st.title("📱 WhatsApp Chat Extractor with Date Filter")

# Upload ZIP
uploaded_zip = st.file_uploader("Upload WhatsApp chat ZIP file", type=["zip"])

if uploaded_zip:
    try:
        with zipfile.ZipFile(uploaded_zip) as z:
            txt_files = [f for f in z.namelist() if f.endswith(".txt")]
            if not txt_files:
                st.error("No TXT file found in ZIP!")
            else:
                chat_file_name = txt_files[0]
                chat_bytes = z.read(chat_file_name)
                lines = chat_bytes.decode("utf-8", errors="ignore").splitlines()

                # ------------------ robust parser ------------------
                # Common WhatsApp patterns
                patterns = [
                    r"^(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}) - (.*?): (.*)$",           # 24h, DD/MM/YYYY
                    r"^(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2} (?:AM|PM)) - (.*?): (.*)$", # 12h, DD/MM/YYYY
                    r"^(\d{1,2}-\d{1,2}-\d{2,4}, \d{1,2}:\d{2}) - (.*?): (.*)$",           # 24h, DD-MM-YYYY
                    r"^(\d{1,2}-\d{1,2}-\d{2,4}, \d{1,2}:\d{2} (?:AM|PM)) - (.*?): (.*)$"  # 12h, DD-MM-YYYY
                ]
                compiled_patterns = [re.compile(p) for p in patterns]

                data = []
                for line in lines:
                    matched = False
                    for pattern in compiled_patterns:
                        match = pattern.match(line)
                        if match:
                            date_time, sender, message = match.groups()
                            data.append([date_time.strip(), sender.strip(), message.strip()])
                            matched = True
                            break
                    if not matched and data:
                        # Multiline message continuation
                        data[-1][2] += "\n" + line.strip()

                if data:
                    df = pd.DataFrame(data, columns=["DateTime", "Sender", "Message"])

                    # ------------------ parse DateTime column ------------------
                    def parse_datetime(dt_str):
                        formats = ["%d/%m/%Y, %H:%M", "%d/%m/%Y, %I:%M %p",
                                   "%d-%m-%Y, %H:%M", "%d-%m-%Y, %I:%M %p"]
                        for fmt in formats:
                            try:
                                return datetime.strptime(dt_str, fmt)
                            except:
                                continue
                        return None

                    df["DateTime"] = df["DateTime"].apply(parse_datetime)
                    df = df.dropna(subset=["DateTime"])  # remove rows with invalid datetime

                    st.success(f"Parsed {len(df)} messages successfully!")

                    # ------------------ Date filter ------------------
                    st.sidebar.subheader("Filter by Date")
                    min_date = df["DateTime"].min().date()
                    max_date = df["DateTime"].max().date()
                    from_date = st.sidebar.date_input("From", min_value=min_date, max_value=max_date, value=min_date)
                    to_date = st.sidebar.date_input("To", min_value=min_date, max_value=max_date, value=max_date)

                    filtered_df = df[(df["DateTime"].dt.date >= from_date) & (df["DateTime"].dt.date <= to_date)]
                    st.dataframe(filtered_df)

                    # ------------------ Download filtered Excel ------------------
                    buffer = BytesIO()
                    filtered_df.to_excel(buffer, index=False)
                    st.download_button(
                        label="Download Filtered Chat as Excel",
                        data=buffer,
                        file_name="whatsapp_filtered.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error("No messages could be parsed. Check TXT format.")

    except Exception as e:
        st.error(f"Error reading ZIP file: {e}")
