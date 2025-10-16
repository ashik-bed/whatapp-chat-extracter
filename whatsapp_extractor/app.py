import streamlit as st
import pandas as pd
import zipfile
import re
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="WhatsApp Chat Extractor", layout="wide")
st.title("📱 WhatsApp Chat Extractor with Date Filter")

# Upload WhatsApp ZIP
uploaded_zip = st.file_uploader("Upload WhatsApp chat ZIP file", type=["zip"])

if uploaded_zip:
    try:
        with zipfile.ZipFile(uploaded_zip) as z:
            # List files inside ZIP
            txt_files = [f for f in z.namelist() if f.endswith(".txt")]
            if not txt_files:
                st.error("No TXT file found in ZIP!")
            else:
                chat_file_name = txt_files[0]
                chat_bytes = z.read(chat_file_name)
                lines = chat_bytes.decode("utf-8").splitlines()

                # Flexible regex parser
                patterns = [
                    re.compile(r"^(\d{1,2}/\d{1,2}/\d{4}, \d{1,2}:\d{2}) - (.*?): (.*)$"),
                    re.compile(r"^(\d{1,2}/\d{1,2}/\d{4}, \d{1,2}:\d{2} (?:AM|PM)) - (.*?): (.*)$"),
                    re.compile(r"^(\d{1,2}-\d{1,2}-\d{4}, \d{1,2}:\d{2}) - (.*?): (.*)$"),
                    re.compile(r"^(\d{1,2}-\d{1,2}-\d{4}, \d{1,2}:\d{2} (?:AM|PM)) - (.*?): (.*)$"),
                ]

                data = []
                for line in lines:
                    matched = False
                    for pattern in patterns:
                        match = pattern.match(line)
                        if match:
                            date_time, sender, message = match.groups()
                            data.append([date_time, sender, message])
                            matched = True
                            break
                    if not matched and data:
                        data[-1][2] += "\n" + line  # append multiline messages

                if data:
                    df = pd.DataFrame(data, columns=["DateTime", "Sender", "Message"])

                    # Convert DateTime column to datetime type
                    def parse_datetime(dt_str):
                        for fmt in ("%d/%m/%Y, %H:%M", "%d/%m/%Y, %I:%M %p", "%d-%m-%Y, %H:%M", "%d-%m-%Y, %I:%M %p"):
                            try:
                                return datetime.strptime(dt_str, fmt)
                            except:
                                continue
                        return None

                    df["DateTime"] = df["DateTime"].apply(parse_datetime)
                    df = df.dropna(subset=["DateTime"])  # drop rows where datetime couldn't be parsed

                    st.success(f"Parsed {len(df)} messages successfully!")

                    # ---------------- Filter by date ----------------
                    st.sidebar.subheader("Filter by Date")
                    min_date = df["DateTime"].min().date()
                    max_date = df["DateTime"].max().date()
                    from_date = st.sidebar.date_input("From", min_value=min_date, max_value=max_date, value=min_date)
                    to_date = st.sidebar.date_input("To", min_value=min_date, max_value=max_date, value=max_date)

                    filtered_df = df[(df["DateTime"].dt.date >= from_date) & (df["DateTime"].dt.date <= to_date)]
                    st.dataframe(filtered_df)

                    # ---------------- Download filtered Excel ----------------
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
