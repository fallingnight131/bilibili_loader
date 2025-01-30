import streamlit as st

def init():
    if "url" not in st.session_state:
        st.session_state.url = ""
    if "is_parsing" not in st.session_state:
        st.session_state.is_parsing = False
    if "is_downloaded" not in st.session_state:
        st.session_state.is_downloaded = False

def set_url(url):
    st.session_state.url = url

def start_parsing():
    st.session_state.is_parsing = True
    st.session_state.is_downloaded = False

def reset():
    st.session_state.url = ""
    st.session_state.is_parsing = False
    st.session_state.is_downloaded = False
    st.rerun()

def is_parsing():
    return st.session_state.is_parsing

def is_downloaded():
    return st.session_state.is_downloaded

def get_url():
    return st.session_state.url
