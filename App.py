import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import io

st.set_page_config(
    page_title="MG Agro Pharma Inventory",
    layout="wide",
    initial_sidebar_state="expanded"
)

# চমৎকার বাংলা ফন্ট ও স্টাইল (আইকন অক্ষুণ্ন রেখে)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&display=swap');
    
    html, body, h1, h2, h3, h4, p, label, input, button, select, textarea, .stMarkdown, .stMetric {
        font-family: 'Hind Siliguri', sans-serif !important;
    }
    
    [data-testid="stIconMaterial"], .material-symbols-rounded, .material-icons {
        font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    }

    .stMetric {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .stButton > button {
        background-color: #102A72;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 8px 24px;
        transition: 0.3s;
    }
    .stButton > button:hover {
        background-color: #0b1e52;
        color: #F4B41A;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- লগইন ভেরিফিকেশন সিস্টেম -----------------
USERS = {
    "admin": "mg1234",
    "manager": "agro2026"
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""

def login_form():
    st.title("🏭 এমজি এগ্রো ফার্মা (MG Agro Pharma)")
    st.caption("স্মার্ট ইনভেন্টরি, প্রোডাকশন ও সেলস ট্র্যাকিং সফটওয়্যার")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.subheader("🔐 সফটওয়্যারে প্রবেশ করুন")
        username_input = st.text_input("ইউজারনেম (Username):")
        password_input = st.text_input("পাসওয়ার্ড (Password):", type="password")
        
        if st.button("লগইন করুন"):
            if username_input in USERS and USERS[username_input] == password_input:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username_input
                st.success("লগইন সফল হয়েছে!")
                st.rerun()
            else:
                st.error("ভুল ইউজারনেম অথবা পাসওয়ার্ড! আবার চেষ্টা করুন।")

if not st.session_state["logged_in"]:
    login_form()
    st.stop()

# ----------------- মূল সফটওয়্যার (লগইন সফল হওয়ার পর) -----------------
st.sidebar.write(f"👤 লগইন আছেন: **{st.session_state['username']}**")
if st.sidebar.button("🚪 লগআউট (Logout)"):
    st
