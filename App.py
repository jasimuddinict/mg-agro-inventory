import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import io

# পেজ কনফিগারেশন
st.set_page_config(page_title="MG Agro Pharma Inventory", layout="wide", initial_sidebar_state="expanded")

# ফন্ট ও স্টাইল
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"], div, p, span, h1, h2, h3, h4, label, input, button, select {
        font-family: 'Hind Siliguri', sans-serif !important;
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

# ডাটাবেস ইনিশিয়ালাইজেশন
conn = sqlite3.connect("mg_agro_pharma.db", check_same_thread=False)
cursor = conn.cursor()

# প্রয়োজনীয় টেবিল তৈরি
cursor.execute("CREATE TABLE IF NOT EXISTS item_list (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS raw_materials (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, item_name TEXT, unit TEXT, quantity REAL, cost_per_unit REAL, total_cost REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS packaging (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, bottle_size TEXT, quantity INTEGER, unit_price REAL, total_cost REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS production (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, product_name TEXT, size TEXT, bottles_produced INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS production_materials (id INTEGER PRIMARY KEY AUTOINCREMENT, production_id INTEGER, raw_material_used TEXT, raw_quantity_used REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, salesman_id TEXT, customer_name TEXT, product_name TEXT, size TEXT, quantity INTEGER, total_bill REAL, cash_received REAL, due_amount REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS due_collections (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, salesman_id TEXT, customer_name TEXT, collected_amount REAL, note TEXT)")
conn.commit()

# ডিফল্ট কাঁচামাল নিশ্চিত করা
default_items = ["Zinc", "Acid", "Calcium", "Vitamin AD3E", "Magnesium", "Cobalt"]
for d_item in default_items:
    cursor.execute("INSERT OR IGNORE INTO item_list (name) VALUES (?)", (d_item,))
conn.commit()

# হেডার
st.title("🏭 এমজি এগ্রো ফার্মা (MG Agro Pharma)")
st.caption("স্মার্ট ইনভেন্টরি, প্রোডাকশন ও সেলস ট্র্যাকিং সফটওয়্যার")
st.markdown("---")

# মেনু তালিকা
menu_options = {
    "dashboard": "📊 লাইভ ড্যাশবোর্ড",
    "raw_purchase": "🧪 কাঁচামাল ক্রয় এন্ট্রি",
    "packaging_purchase": "🧴 বোতল/প্যাকেট ক্রয়",
    "production": "⚙️ ওষুধ উৎপাদন এন্ট্রি",
    "sales": "🚚 বিক্রয় ও চালান এন্ট্রি",
    "due_collection": "💵 বাকি টাকা আদায় (Due Receive)",
    "records": "🗑️ রেকর্ড সংশোধন ও ডিলিট"
}

selected_key = st.sidebar.radio(
    "মেন্যু নির্বাচন করুন:",
    options=list(menu_options.keys()),
    format_func=lambda x: menu_options[x]
)

# ----------------- ১. লাইভ ড্যাশবোর্ড -----------------
if selected_key == "dashboard":
    st.header("📈 রিয়েল-টাইম স্টক ও ব্যালেন্স রিপোর্ট")
    
    df_raw = pd.read_sql("SELECT * FROM raw_materials", conn)
    df_pack = pd.read_sql("SELECT * FROM packaging", conn)
    df_prod = pd.read_sql("SELECT * FROM production", conn)
    df_used = pd.read_sql("SELECT * FROM production_materials", conn)
    df_sales = pd.read_sql("SELECT * FROM sales", conn)
    df_due_col = pd.read_sql("SELECT * FROM due_collections", conn)
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_raw_cost = float(df_raw["total_cost"].sum()) if not df_raw.empty else 0.0
    total_pack_cost = float(df_pack["total_cost"].sum()) if not df_pack.empty else 0.0
    total_sales = float(df_sales["total_bill"].sum()) if not df_sales.empty else 0.0
    
    initial_due = float(df_sales["due_amount"].sum()) if not df_sales.empty else 0.0
    total_collected =
