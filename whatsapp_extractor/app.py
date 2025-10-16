import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="WhatsApp Chat Extractor", layout="wide")
st.title("📱 WhatsApp Chat Extractor")

# Upload TXT file
uploaded_file = st.file_uploader("Upload WhatsApp chat TXT file", type=["txt"])

if uploaded_file:
    # Read lines
    lines = uploaded_file.read().decode("utf-8").splitlines()

    # Preview first 10 lines to check format
    st.subheader("Preview first 10 lines of TXT")
    for i, line in enumerate(lines[:10]):
        st.text(f"{i+1}: {line}")

    # Patterns: 24h and 12h formats, DD/MM/YYYY or MM/DD/YYYY
    patterns = [
        re.compile(r"^(\d{1,2}/\d{1,2}/\d{4}, \d{1,2}:\d{2}) - (.*?): (.*)$"),  # 24h DD/MM/YYYY
        re.compile(r"^(\d{1,2}/\d{1,2}/\d{4}, \d{1,2}:\d{2} (?:AM|PM)) - (.*?): (.*)$"),  # 12h DD/MM/YYYY
        re.compile(r"^(\d{1,2}-\d{1,2}-\d{4}, \d{1,2}:\d{2}) - (.*?): (.*)$"),  # 24h DD-MM-YYYY
        re.compile(r"^(\d{1,2}-\d{1,2}-\d{4}, \d{1,2}:\d{2} (?:AM|PM)) - (.*?): (.*)$"),  # 12h DD-MM-YYYY
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
            # Append multi-line messages
            data[-1][2] += "\n" + line

    if data:
        df = pd.DataFrame(data, columns=["DateTime", "Sender", "Message"])

        # Example calculation: Word count
        df["Word_Count"] = df["Message"].apply(lambda x: len(x.split()))

        st.success(f"Parsed {len(df)} messages successfully!")
        st.dataframe(df.head(20))

        # Download as Excel
        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        st.download_button(
            label="Download Excel",
            data=buffer,
            file_name="whatsapp_parsed.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.error("No messages could be parsed. Check TXT format.")
