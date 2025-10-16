import streamlit as st
import pandas as pd
import re

uploaded_file = st.file_uploader("Upload WhatsApp chat file", type=["txt"])

if uploaded_file:
    lines = uploaded_file.read().decode("utf-8").splitlines()
    data = []

    # Regex to match lines starting with date/time
    # Supports DD/MM/YYYY, MM/DD/YYYY, 24h or 12h formats
    pattern = re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}(?: AM| PM)?) - (.*?): (.*)$")

    for line in lines:
        match = pattern.match(line)
        if match:
            date_time, sender, message = match.groups()
            data.append([date_time, sender, message])
        else:
            # Line continuation: append to last message
            if data:
                data[-1][2] += "\n" + line

    if data:
        df = pd.DataFrame(data, columns=["DateTime", "Sender", "Message"])
        st.success(f"Parsed {len(df)} messages successfully!")
        st.dataframe(df.head())

        # Download button
        st.download_button(
            label="Download Parsed File",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="whatsapp_parsed.csv",
            mime="text/csv"
        )
    else:
        st.error("No messages could be parsed. Check the format of your WhatsApp file.")
