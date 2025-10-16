import streamlit as st
import pandas as pd
from io import BytesIO

st.title("WhatsApp Extractor")

# Upload file
uploaded_file = st.file_uploader("Upload your WhatsApp chat file", type=["txt", "csv", "xlsx"])

if uploaded_file:
    # Read file into DataFrame
    if uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file, sep="\t", header=None)

    st.dataframe(df.head())

    # Process your DataFrame here
    # For example, add a new column
    df["Processed"] = True

    # Download button
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    st.download_button(
        label="Download Processed File",
        data=buffer,
        file_name="processed_whatsapp.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
