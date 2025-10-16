import streamlit as st
import pandas as pd
import re

uploaded_file = st.file_uploader("Upload WhatsApp chat file", type=["txt"])

if uploaded_file:
    # Read all lines
    lines = uploaded_file.read().decode("utf-8").splitlines()

    data = []
    for line in lines:
        # WhatsApp format: "DD/MM/YYYY, HH:MM - Name: Message"
        match = re.match(r"^(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}) - (.*?): (.*)$", line)
        if match:
            date_time, sender, message = match.groups()
            data.append([date_time, sender, message])
        else:
            # This line might be a continuation of the previous message
            if data:
                data[-1][2] += "\n" + line  # append to last message

    df = pd.DataFrame(data, columns=["DateTime", "Sender", "Message"])
    st.success("File parsed successfully!")
    st.dataframe(df.head())

    # Example download button
    st.download_button(
        label="Download Parsed File",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name="whatsapp_parsed.csv",
        mime="text/csv"
    )
