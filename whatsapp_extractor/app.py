import streamlit as st
import pandas as pd

uploaded_file = st.file_uploader("Upload your WhatsApp file", type=["txt", "csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".txt"):
            # Most WhatsApp chats are like "DD/MM/YYYY, HH:MM - Name: Message"
            df = pd.read_csv(uploaded_file, sep=" - ", header=None, engine='python', names=["DateTime", "Message"])
        else:
            st.error("Unsupported file type")
            st.stop()
        st.success("File loaded successfully!")
        st.dataframe(df.head())
    except pd.errors.ParserError as e:
        st.error(f"Pandas ParserError: {e}")
