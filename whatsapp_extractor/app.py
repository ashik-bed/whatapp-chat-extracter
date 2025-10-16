import streamlit as st
import pandas as pd
import zipfile
from io import BytesIO
import re

uploaded_file = st.file_uploader("Upload WhatsApp chat ZIP file", type=["zip"])

if uploaded_file:
    # Open the zip file
    with zipfile.ZipFile(uploaded_file) as z:
        # List files inside the zip
        st.write("Files in ZIP:", z.namelist())

        # Usually WhatsApp chat is the TXT file
        txt_files = [f for f in z.namelist() if f.endswith(".txt")]
        if not txt_files:
            st.error("No TXT chat file found in ZIP!")
        else:
            chat_file_name = txt_files[0]  # Take the first TXT
            st.write("Parsing chat file:", chat_file_name)
            chat_bytes = z.read(chat_file_name)
            lines = chat_bytes.decode("utf-8").splitlines()

            # Now parse lines like before
            data = []
            pattern = re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}(?: AM| PM)?) - (.*?): (.*)$")

            for line in lines:
                match = pattern.match(line)
                if match:
                    date_time, sender, message = match.groups()
                    data.append([date_time, sender, message])
                else:
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
                st.error("No messages could be parsed. Check the format inside TXT file.")
