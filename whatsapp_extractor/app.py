# ------------------ _signal wrapper (your code) ------------------
import _signal
from _signal import *
from enum import IntEnum as _IntEnum

_globals = globals()

_IntEnum._convert_(
        'Signals', __name__,
        lambda name:
            name.isupper()
            and (name.startswith('SIG') and not name.startswith('SIG_'))
            or name.startswith('CTRL_'))

_IntEnum._convert_(
        'Handlers', __name__,
        lambda name: name in ('SIG_DFL', 'SIG_IGN'))

if 'pthread_sigmask' in _globals:
    _IntEnum._convert_(
            'Sigmasks', __name__,
            lambda name: name in ('SIG_BLOCK', 'SIG_UNBLOCK', 'SIG_SETMASK'))


def _int_to_enum(value, enum_klass):
    try:
        return enum_klass(value)
    except ValueError:
        return value


def _enum_to_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return value


def _wraps(wrapped):
    def decorator(wrapper):
        wrapper.__doc__ = wrapped.__doc__
        return wrapper
    return decorator


@_wraps(_signal.signal)
def signal(signalnum, handler):
    handler = _signal.signal(_enum_to_int(signalnum), _enum_to_int(handler))
    return _int_to_enum(handler, Handlers)


@_wraps(_signal.getsignal)
def getsignal(signalnum):
    handler = _signal.getsignal(signalnum)
    return _int_to_enum(handler, Handlers)


if 'pthread_sigmask' in _globals:
    @_wraps(_signal.pthread_sigmask)
    def pthread_sigmask(how, mask):
        sigs_set = _signal.pthread_sigmask(how, mask)
        return set(_int_to_enum(x, Signals) for x in sigs_set)


if 'sigpending' in _globals:
    @_wraps(_signal.sigpending)
    def sigpending():
        return {_int_to_enum(x, Signals) for x in _signal.sigpending()}


if 'sigwait' in _globals:
    @_wraps(_signal.sigwait)
    def sigwait(sigset):
        retsig = _signal.sigwait(sigset)
        return _int_to_enum(retsig, Signals)


if 'valid_signals' in _globals:
    @_wraps(_signal.valid_signals)
    def valid_signals():
        return {_int_to_enum(x, Signals) for x in _signal.valid_signals()}


del _globals, _wraps

# ------------------ STREAMLIT APP ------------------
import streamlit as st
import pandas as pd
import zipfile
import re
from io import BytesIO

st.set_page_config(page_title="WhatsApp Extractor", layout="wide")
st.title("📱 WhatsApp Chat Extractor")

# Upload ZIP file
uploaded_zip = st.file_uploader("Upload WhatsApp chat ZIP file", type=["zip"])

if uploaded_zip:
    try:
        with zipfile.ZipFile(uploaded_zip) as z:
            st.write("Files in ZIP:", z.namelist())

            txt_files = [f for f in z.namelist() if f.endswith(".txt")]
            if not txt_files:
                st.error("No TXT chat file found in ZIP!")
            else:
                chat_file_name = txt_files[0]  # take first TXT file
                chat_bytes = z.read(chat_file_name)
                lines = chat_bytes.decode("utf-8").splitlines()

                # Regex parser for WhatsApp messages
                pattern = re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}(?: AM| PM)?) - (.*?): (.*)$")
                data = []

                for line in lines:
                    match = pattern.match(line)
                    if match:
                        date_time, sender, message = match.groups()
                        data.append([date_time, sender, message])
                    else:
                        if data:
                            data[-1][2] += "\n" + line  # append multiline messages

                if data:
                    df = pd.DataFrame(data, columns=["DateTime", "Sender", "Message"])
                    st.success(f"Parsed {len(df)} messages successfully!")
                    st.dataframe(df.head())

                    # Add example calculation: number of words
                    df["Word_Count"] = df["Message"].apply(lambda x: len(x.split()))

                    # Download Excel
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

    except Exception as e:
        st.error(f"Error reading ZIP file: {e}")
