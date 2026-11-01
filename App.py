import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta
import io

st.set_page_config(
    page_title="MG Agro Pharma Inventory",
    layout="wide",
    initial_sidebar_state="expanded"
)

# চমৎকার বাংলা ফন্ট ও স্টাইল
st.markdown('''
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
    
    @media print {
        header, .stSidebar, [data-testid="stSidebar"], .st-emotion-cache-18ni7ap {
            display: none !important;
        }
        .stApp {
            background-color: white !important;
        }
        #invoice-print-area {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            border: none !important;
            box-shadow: none !important;
        }
        button {
            display: none !important;
        }
    }
</style>
''', unsafe_allow_html=True)

# ----------------- রোল-ভিত্তিক লগইন সিস্টেম -----------------
USERS = {
    "admin": {"pass": "mg1234", "role": "admin", "name": "অ্যাডমিন"},
    "manager": {"pass": "agro2026", "role": "manager", "name": "ম্যানেজার"},
    "salesman1": {"pass": "sm1234", "role": "salesman", "name": "সেলসম্যান ০১"}
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""
    st.session_state["user_name"] = ""

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
            if username_input in USERS and USERS[username_input]["pass"] == password_input:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username_input
                st.session_state["role"] = USERS[username_input]["role"]
                st.session_state["user_name"] = USERS[username_input]["name"]
                st.success("লগইন সফল হয়েছে!")
                st.rerun()
            else:
                st.error("ভুল ইউজারনেম অথবা পাসওয়ার্ড! আবার চেষ্টা করুন।")

if not st.session_state["logged_in"]:
    login_form()
    st.stop()

# ----------------- মূল সফটওয়্যার (লগইন সফল হওয়ার পর) -----------------
st.sidebar.write(f"👤 লগইন আছেন: **{st.session_state['user_name']}** ({st.session_state['role'].capitalize()})")
if st.sidebar.button("🚪 লগআউট (Logout)"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""
    st.session_state["user_name"] = ""
    st.rerun()

st.sidebar.markdown("---")

conn = sqlite3.connect("mg_agro_pharma.db", check_same_thread=False)
cursor = conn.cursor()

# ডাটাবেস টেবিল তৈরি
cursor.execute("CREATE TABLE IF NOT EXISTS item_list (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS raw_materials (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, item_name TEXT, unit TEXT, quantity REAL, cost_per_unit REAL, total_cost REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS packaging (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, bottle_size TEXT, quantity INTEGER, unit_price REAL, total_cost REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS production (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, product_name TEXT, size TEXT, bottles_produced INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS production_materials (id INTEGER PRIMARY KEY AUTOINCREMENT, production_id INTEGER, raw_material_used TEXT, raw_quantity_used REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, salesman_id TEXT, customer_name TEXT, product_name TEXT, size TEXT, quantity INTEGER, total_bill REAL, cash_received REAL, due_amount REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS due_collections (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, salesman_id TEXT, customer_name TEXT, collected_amount REAL, note TEXT)")
conn.commit()

default_items = ["Zinc", "Acid", "Calcium", "Vitamin AD3E", "Magnesium", "Cobalt"]
for d_item in default_items:
    cursor.execute("INSERT OR IGNORE INTO item_list (name) VALUES (?)", (d_item,))
conn.commit()

st.title("🏭 এমজি এগ্রো ফার্মা (MG Agro Pharma)")
st.caption("স্মার্ট ইনভেন্টরি, প্রোডাকশন ও সেলস ট্র্যাকিং সফটওয়্যার")
st.markdown("---")

# রোল-ভিত্তিক মেন্যু তালিকা
all_menus = [
    "📊 লাইভ ড্যাশবোর্ড", 
    "🧪 কাঁচামাল ক্রয় এন্ট্রি", 
    "🧴 বোতল/প্যাকেট ক্রয়", 
    "⚙️ ওষুধ উৎপাদন এন্ট্রি", 
    "🚚 বিক্রয় ও চালান এন্ট্রি",
    "💵 বাকি টাকা আদায় (Due Receive)",
    "🗑️ রেকর্ড সংশোধন ও ডিলিট"
]

if st.session_state["role"] == "salesman":
    menu_list = ["🚚 বিক্রয় ও চালান এন্ট্রি", "💵 বাকি টাকা আদায় (Due Receive)"]
else:
    menu_list = all_menus

selected_menu = st.sidebar.radio("মেন্যু নির্বাচন করুন:", menu_list)
# get absolute index
menu_index = all_menus.index(selected_menu)

# ----------------- ০. লাইভ ড্যাশবোর্ড -----------------
if menu_index == 0:
    st.header("📈 রিয়েল-টাইম স্টক ও ব্যালেন্স রিপোর্ট")
    
    # তারিখ ফিল্টার
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("শুরুর তারিখ", date.today().replace(day=1))
    with col_d2:
        end_date = st.date_input("শেষ তারিখ", date.today())
        
    st.markdown("---")
    
    # ডেটা রিড
    df_raw = pd.read_sql("SELECT * FROM raw_materials", conn)
    df_pack = pd.read_sql("SELECT * FROM packaging", conn)
    df_prod = pd.read_sql("SELECT * FROM production", conn)
    df_used = pd.read_sql("SELECT * FROM production_materials", conn)
    df_sales = pd.read_sql("SELECT * FROM sales", conn)
    df_due_col = pd.read_sql("SELECT * FROM due_collections", conn)
    
    # তারিখ অনুযায়ী ফিল্টার করা ডেটা (হিসাবের জন্য)
    # ডেটা টাইপ রূপান্তর নিশ্চিত করা
    if not df_raw.empty: df_raw['date'] = pd.to_datetime(df_raw['date']).dt.date
    if not df_pack.empty: df_pack['date'] = pd.to_datetime(df_pack['date']).dt.date
    if not df_prod.empty: df_prod['date'] = pd.to_datetime(df_prod['date']).dt.date
    if not df_sales.empty: df_sales['date'] = pd.to_datetime(df_sales['date']).dt.date
    if not df_due_col.empty: df_due_col['date'] = pd.to_datetime(df_due_col['date']).dt.date
    
    # Filter function
    def filter_by_date(df):
        if df.empty: return df
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        return df.loc[mask]

    f_raw = filter_by_date(df_raw)
    f_pack = filter_by_date(df_pack)
    f_sales = filter_by_date(df_sales)
    f_due_col = filter_by_date(df_due_col)
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_raw_cost = float(f_raw["total_cost"].sum()) if not f_raw.empty else 0.0
    total_pack_cost = float(f_pack["total_cost"].sum()) if not f_pack.empty else 0.0
    total_sales = float(f_sales["total_bill"].sum()) if not f_sales.empty else 0.0
    
    # বাকি টাকার হিসাব (সব সময়ের ভিত্তিতে)
    initial_due = float(df_sales["due_amount"].sum()) if not df_sales.empty else 0.0
    total_collected = float(df_due_col["collected_amount"].sum()) if not df_due_col.empty else 0.0
    net_remaining_due = initial_due - total_collected
    
    col1.metric(f"মোট কাঁচামাল ক্রয় (ফিল্টারড)", f"৳ {total_raw_cost:,.2f}")
    col2.metric(f"মোট প্যাকেজিং খরচ (ফিল্টারড)", f"৳ {total_pack_cost:,.2f}")
    col3.metric(f"মোট বিক্রয় বিল (ফিল্টারড)", f"৳ {total_sales:,.2f}")
    col4.metric("মার্কেটে বর্তমান আসল বাকি (মোট)", f"৳ {net_remaining_due:,.2f}")
    
    st.markdown("---")
    
    # ---------------- লো-স্টক অ্যালার্ট সিস্টেম ----------------
    st.subheader("🚨 লো-স্টক অ্যালার্ট (Low Stock Warning)")
    alerts = []
    
    # Raw Material Stock
    raw_stock_df = pd.DataFrame()
    if not df_raw.empty:
        raw_in = df_raw.groupby(["item_name", "unit"])["quantity"].sum().reset_index()
        if not df_used.empty:
            raw_out = df_used.groupby("raw_material_used")["raw_quantity_used"].sum().reset_index()
            raw_stock_df = pd.merge(raw_in, raw_out, left_on="item_name", right_on="raw_material_used", how="left").fillna(0)
            raw_stock_df["current_stock"] = raw_stock_df["quantity"] - raw_stock_df["raw_quantity_used"]
        else:
            raw_stock_df = raw_in.copy()
            raw_stock_df["current_stock"] = raw_stock_df["quantity"]
            
        for _, row in raw_stock_df.iterrows():
            if row["current_stock"] <= 5.0: # 5 kg/ltr warning limit
                alerts.append(f"⚠️ কাঁচামাল **{row['item_name']}** এর স্টক কমে **{row['current_stock']} {row['unit']}** এ নেমেছে!")
                
    # Finished Goods Stock
    stock_df = pd.DataFrame()
    if not df_prod.empty:
        prod_summary = df_prod.groupby(["product_name", "size"])["bottles_produced"].sum().reset_index()
        if not df_sales.empty:
            sales_summary = df_sales.groupby(["product_name", "size"])["quantity"].sum().reset_index()
            stock_df = pd.merge(prod_summary, sales_summary, on=["product_name", "size"], how="left").fillna(0)
            stock_df["current_stock"] = stock_df["bottles_produced"] - stock_df["quantity"]
        else:
            stock_df = prod_summary.copy()
            stock_df["current_stock"] = stock_df["bottles_produced"]
            
        for _, row in stock_df.iterrows():
            if row["current_stock"] <= 50: # 50 bottles warning limit
                alerts.append(f"⚠️ তৈরি ঔষধ **{row['product_name']} ({row['size']})** এর স্টক কমে মাত্র **{row['current_stock']} পিস** আছে!")
                
    if alerts:
        for alert in alerts:
            st.error(alert)
    else:
        st.success("✅ সমস্ত কাঁচামাল এবং তৈরি ঔষধের স্টক পর্যাপ্ত পরিমাণে রয়েছে।")
        
    st.markdown("---")

    st.subheader("📦 তৈরি ওষুধের বর্তমান মজুদ (Finished Goods Stock)")
    if not stock_df.empty:
        display_stock = stock_df.copy()
        display_stock.rename(columns={"product_name": "ওষুধের নাম", "size": "সাইজ", "bottles_produced": "মোট উৎপাদন", "quantity": "মোট বিক্রয়", "current_stock": "বর্তমান স্টক (বোতল)"}, inplace=True)
        cols_prod = ["ওষুধের নাম", "সাইজ", "মোট উৎপাদন", "মোট বিক্রয়", "বর্তমান স্টক (বোতল)"]
        st.dataframe(display_stock[cols_prod], use_container_width=True)
    else:
        st.info("এখনো কোনো উৎপাদন রেকর্ড নেই।")

    st.subheader("🧪 কাঁচামালের বর্তমান মজুদ (Raw Material Stock)")
    if not raw_stock_df.empty:
        display_raw = raw_stock_df.copy()
        display_raw.rename(columns={"item_name": "কাঁচামালের নাম", "unit": "একক", "quantity": "মোট ক্রয়", "raw_quantity_used": "মোট ব্যবহার", "current_stock": "অবশিষ্ট স্টক"}, inplace=True)
        cols_raw = ["কাঁচামালের নাম", "একক", "মোট ক্রয়", "মোট ব্যবহার", "অবশিষ্ট স্টক"]
        st.dataframe(display_raw[cols_raw], use_container_width=True)
    else:
        st.info("এখনো কোনো কাঁচামাল ক্রয় এন্ট্রি নেই।")

    st.markdown("---")
    st.subheader("👥 কাস্টমারভিত্তিক বিক্রয়, আদায় ও বাকি খতিয়ান (সর্বকালের)")
    
    if not df_sales.empty:
        cust_sales = df_sales.groupby("customer_name").agg({
            "total_bill": "sum",
            "cash_received": "sum",
            "due_amount": "sum"
        }).reset_index()
        
        if not df_due_col.empty:
            cust_rec = df_due_col.groupby("customer_name")["collected_amount"].sum().reset_index()
            cust_df = pd.merge(cust_sales, cust_rec, on="customer_name", how="left").fillna(0)
        else:
            cust_df = cust_sales.copy()
            cust_df["collected_amount"] = 0
            
        cust_df["পরিশোধিত মোট টাকা (৳)"] = cust_df["cash_received"] + cust_df["collected_amount"]
        cust_df["বর্তমান বকেয়া টাকা (৳)"] = cust_df["due_amount"] - cust_df["collected_amount"]
        
        cust_df.rename(columns={
            "customer_name": "কাস্টমার / ডিলারের নাম",
            "total_bill": "মোট ক্রয় বিল (৳)"
        }, inplace=True)
        
        cols_cust = ["কাস্টমার / ডিলারের নাম", "মোট ক্রয় বিল (৳)", "পরিশোধিত মোট টাকা (৳)", "বর্তমান বকেয়া টাকা (৳)"]
        st.dataframe(cust_df[cols_cust], use_container_width=True)
    else:
        st.info("এখনো কোনো বিক্রয় রেকর্ড এন্ট্রি করা হয়নি।")

# ----------------- ১. কাঁচামাল ক্রয় এন্ট্রি -----------------
elif menu_index == 1:
    st.header("🧪 কাঁচামাল ক্রয় ইনপুট")
    
    if st.checkbox("➕ তালিকায় সম্পূর্ণ নতুন কোনো কাঁচামাল যুক্ত করতে টিক দিন"):
        new_item_to_add = st.text_input("নতুন কাঁচামালের নাম লিখুন:")
        if st.button("তালিকায় যুক্ত করুন"):
            val_to_add = new_item_to_add.strip()
            if val_to_add:
                cursor.execute("INSERT OR IGNORE INTO item_list (name) VALUES (?)", (val_to_add,))
                conn.commit()
                st.success(f"'{val_to_add}' তালিকায় নিশ্চিত করা হয়েছে!")
                st.rerun()
            else:
                st.error("দয়া করে কাঁচামালের নাম লিখুন।")

    st.markdown("---")
    st.subheader("ক্রয় ভাউচার এন্ট্রি")
    
    db_items = pd.read_sql("SELECT name FROM item_list ORDER BY name ASC", conn)["name"].tolist()

    with st.form("raw_purchase_form", clear_on_submit=True):
        entry_date = st.date_input("ক্রয়ের তারিখ", date.today())
        item_name = st.selectbox("কাঁচামাল নির্বাচন করুন", db_items)
        unit = st.selectbox("পরিমাপের একক", ["Kg", "Ltr", "Gram", "MG"])
        qty = st.number_input("পরিমাণ (Quantity)", min_value=0.0, step=0.1)
        cost_unit = st.number_input("প্রতি এককের দর (Rate/Unit)", min_value=0.0, step=1.0)
        
        submitted = st.form_submit_button("স্টকে যোগ করুন")
        if submitted and qty > 0:
            total = qty * cost_unit
            cursor.execute("INSERT INTO raw_materials (date, item_name, unit, quantity, cost_per_unit, total_cost) VALUES (?, ?, ?, ?, ?, ?)",
                           (str(entry_date), item_name, unit, qty, cost_unit, total))
            conn.commit()
            st.success(f"সফলভাবে {qty} {unit} {item_name} স্টকে যুক্ত হয়েছে! মোট খরচ: ৳ {total:,.2f}")

# ----------------- ২. বোতল/প্যাকেট ক্রয় -----------------
elif menu_index == 2:
    st.header("🧴 খালি বোতল / প্যাকেট ক্রয় ইনপুট")
    with st.form("pack_form", clear_on_submit=True):
        entry_date = st.date_input("ক্রয়ের তারিখ", date.today())
        bottle_size = st.selectbox("বোতলের সাইজ", ["10ml", "15ml", "20ml", "50ml", "100ml", "125ml", "200ml", "250ml", "500ml", "1000ml", "100gm", "1kg", "অন্যান্য"])
        qty = st.number_input("বোতলের সংখ্যা (পিস)", min_value=0, step=1)
        price_unit = st.number_input("প্রতি পিস বোতলের দাম", min_value=0.0, step=0.1)
        
        submitted = st.form_submit_button("বোতল স্টকে যোগ করুন")
        if submitted and qty > 0:
            total = qty * price_unit
            cursor.execute("INSERT INTO packaging (date, bottle_size, quantity, unit_price, total_cost) VALUES (?, ?, ?, ?, ?)",
                           (str(entry_date), bottle_size, qty, price_unit, total))
            conn.commit()
            st.success(f"সফলভাবে {qty} পিস {bottle_size} বোতল স্টকে যোগ হয়েছে! মোট খরচ: ৳ {total:,.2f}")

# ----------------- ৩. ওষুধ উৎপাদন এন্ট্রি -----------------
elif menu_index == 3:
    st.header("⚙️ ওষুধ উৎপাদন (Production) ইনপুট")
    st.caption("ওষুধ উৎপাদনের এন্ট্রি দিলে ব্যবহৃত সমস্ত কাঁচামাল এবং বোতল স্টক থেকে স্বয়ংক্রিয়ভাবে মাইনাস হয়ে যাবে।")
    
    product_list = [
        "MG -Cal", "MG -liver sol", "MG -Sol -E", "MG -PH", "MG -FERO VET", 
        "MG -Enzyme", "MG -AD3E", "MG -ZINC VET", "MG -Multi plus", "MG -COF NIL", 
        "MG-DB", "MG-VIT-C", "MG-RUMEN", "MG-Milk & Milk"
    ]
    
    raw_materials_available = pd.read_sql("SELECT name FROM item_list ORDER BY name ASC", conn)["name"].tolist()
    
    num_materials = st.number_input("এই ব্যাচে মোট কয়টি কাঁচামাল ব্যবহার হয়েছে?", min_value=1, max_value=20, value=2, step=1)
    
    with st.form("prod_multi_form", clear_on_submit=True):
        entry_date = st.date_input("উৎপাদনের তারিখ", date.today())
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            product_name = st.selectbox("ওষুধের নাম", product_list)
        with col_p2:
            size = st.selectbox("বোতলের সাইজ", ["10ml", "15ml", "20ml", "50ml", "100ml", "125ml", "200ml", "250ml", "500ml", "1000ml", "100gm", "1kg"])
        with col_p3:
            bottles_produced = st.number_input("কত বোতল/প্যাকেট তৈরি হলো?", min_value=1, step=1)
        
        st.markdown("##### 🧪 ব্যবহৃত কাঁচামাল ও পরিমাণের তালিকা:")
        
        used_materials_data = []
        for i in range(num_materials):
            c1, c2 = st.columns(2)
            with c1:
                mat = st.selectbox(f"কাঁচামাল #{i+1}", raw_materials_available, key=f"mat_{i}")
            with c2:
                q = st.number_input(f"পরিমাণ (Kg/Ltr) #{i+1}", min_value=0.0, step=0.01, key=f"qty_{i}")
            used_materials_data.append((mat, q))
        
        submitted = st.form_submit_button("উৎপাদন সম্পন্ন করুন")
        if submitted:
            cursor.execute("INSERT INTO production (date, product_name, size, bottles_produced) VALUES (?, ?, ?, ?)",
                           (str(entry_date), product_name, size, bottles_produced))
            prod_id = cursor.lastrowid
            
            for mat_name, mat_qty in used_materials_data:
                if mat_qty > 0:
                    cursor.execute("INSERT INTO production_materials (production_id, raw_material_used, raw_quantity_used) VALUES (?, ?, ?)",
                                   (prod_id, mat_name, mat_qty))
            
            conn.commit()
            st.success(f"{product_name} ({size}) - {bottles_produced} বোতল সফলভাবে উৎপাদিত হয়েছে এবং সমস্ত কাঁচামাল স্টক থেকে মাইনাস হয়েছে!")

# ----------------- ৪. বিক্রয় ও চালান এন্ট্রি -----------------
elif menu_index == 4:
    st.header("🚚 বিক্রয় ও চালান (Voucher) তৈরি")
    
    salesmen = [f"SM{str(i).zfill(2)}" for i in range(1, 11)]
    product_list = [
        "MG -Cal", "MG -liver sol", "MG -Sol -E", "MG -PH", "MG -FERO VET", 
        "MG -Enzyme", "MG -AD3E", "MG -ZINC VET", "MG -Multi plus", "MG -COF NIL", 
        "MG-DB", "MG-VIT-C", "MG-RUMEN", "MG-Milk & Milk"
    ]
    
    num_items = st.number_input("এই ভাউচারে কয়টি ভিন্ন ঔষধ বিক্রি করবেন?", min_value=1, max_value=15, value=1, step=1)
    
    with st.form("sales_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            entry_date = st.date_input("বিক্রয়ের তারিখ", date.today())
            salesman = st.selectbox("সেলসম্যান আইডি", salesmen)
        with col2:
            customer = st.text_input("কাস্টমার / ডিলারের নাম")
            cash_received = st.number_input("সর্বমোট নগদ আদায় (Cash Received)", min_value=0.0, step=1.0)
            
        st.markdown("#### 🛒 বিক্রিত ঔষধের তালিকা:")
        
        items_data = []
        for i in range(num_items):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            with c1:
                p_name = st.selectbox(f"পণ্য #{i+1}", product_list, key=f"p_{i}")
            with c2:
                p_size = st.selectbox(f"সাইজ #{i+1}", ["10ml", "15ml", "20ml", "50ml", "100ml", "125ml", "200ml", "250ml", "500ml", "1000ml", "100gm", "1kg"], key=f"s_{i}")
            with c3:
                p_qty = st.number_input(f"সংখ্যা (পিস) #{i+1}", min_value=1, step=1, key=f"q_{i}")
            with c4:
                p_rate = st.number_input(f"রেট (TP) #{i+1}", min_value=0.0, step=1.0, key=f"r_{i}")
            items_data.append({"name": p_name, "size": p_size, "qty": p_qty, "rate": p_rate})
            
        submitted = st.form_submit_button("ভাউচার তৈরি করুন ও সেভ করুন")
        
        if submitted and customer.strip() != "":
            grand_total = sum(item["qty"] * item["rate"] for item in items_data)
            total_due = grand_total - cash_received
            
            for idx, item in enumerate(items_data):
                item_bill = item["qty"] * item["rate"]
                if idx == 0:
                    row_cash = cash_received
                    row_due = total_due
                else:
                    row_cash = 0.0
                    row_due = 0.0
                    
                cursor.execute("INSERT INTO sales (date, salesman_id, customer_name, product_name, size, quantity, total_bill, cash_received, due_amount) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                               (str(entry_date), salesman, customer.strip(), item["name"], item["size"], item["qty"], item_bill, row_cash, row_due))
            conn.commit()
            
            st.success("✅ বিক্রয় সফলভাবে ডাটাবেসে সেভ হয়েছে!")
            
            st.markdown("### 🧾 ইনভয়েস / ভাউচার")
            voucher_html = ""
            voucher_html += "<div id='invoice-print-area' style='border: 2px dashed #102A72; padding: 20px; border-radius: 10px; max-width: 600px; margin: 0 auto; background-color: #f8fafc; color: #000; font-family: inherit;'>"
            voucher_html += "<h2 style='text-align: center; color: #102A72; margin-bottom: 5px;'>এমজি এগ্রো ফার্মা</h2>"
            voucher_html += "<p style='text-align: center; margin-top: 0; color: #64748B;'>বিক্রয় চালান (Invoice)</p>"
            voucher_html += "<hr style='border-top: 1px solid #ccc;'>"
            voucher_html += f"<p><strong>তারিখ:</strong> {entry_date}</p>"
            voucher_html += f"<p><strong>কাস্টমার:</strong> {customer.strip()} | <strong>সেলসম্যান:</strong> {salesman}</p>"
            voucher_html += "<table style='width: 100%; border-collapse: collapse; margin-top: 15px;'>"
            voucher_html += "<tr style='background-color: #e2e8f0; color: #000;'>"
            voucher_html += "<th style='padding: 8px; border: 1px solid #ccc; text-align: left;'>পণ্য ও সাইজ</th>"
            voucher_html += "<th style='padding: 8px; border: 1px solid #ccc; text-align: center;'>পরিমাণ</th>"
            voucher_html += "<th style='padding: 8px; border: 1px solid #ccc; text-align: right;'>রেট</th>"
            voucher_html += "<th style='padding: 8px; border: 1px solid #ccc; text-align: right;'>মোট মূল্য</th>"
            voucher_html += "</tr>"
            
            for item in items_data:
                item_total = item['qty'] * item['rate']
                voucher_html += "<tr>"
                voucher_html += f"<td style='padding: 8px; border: 1px solid #ccc;'>{item['name']} ({item['size']})</td>"
                voucher_html += f"<td style='padding: 8px; border: 1px solid #ccc; text-align: center;'>{item['qty']}</td>"
                voucher_html += f"<td style='padding: 8px; border: 1px solid #ccc; text-align: right;'>৳ {item['rate']:,.2f}</td>"
                voucher_html += f"<td style='padding: 8px; border: 1px solid #ccc; text-align: right;'>৳ {item_total:,.2f}</td>"
                voucher_html += "</tr>"
                
            voucher_html += "</table>"
            voucher_html += "<hr style='border-top: 1px solid #ccc; margin-top: 20px;'>"
            voucher_html += f"<p style='text-align: right; margin: 5px 0;'><strong>সর্বমোট বিল:</strong> ৳ {grand_total:,.2f}</p>"
            voucher_html += f"<p style='text-align: right; margin: 5px 0; color: green;'><strong>नগদ জমা:</strong> ৳ {cash_received:,.2f}</p>"
            voucher_html += f"<p style='text-align: right; margin: 5px 0; color: red;'><strong>বর্তমান বাকি:</strong> ৳ {total_due:,.2f}</p>"
            voucher_html += "<p style='text-align: center; margin-top: 30px; font-size: 12px; color: #64748B;'>ধন্যবাদ! আবার আসবেন।</p>"
            voucher_html += "<div style='text-align: center; margin-top: 20px;'>"
            voucher_html += "<button onclick='window.print()' style='background-color: #102A72; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 5px; cursor: pointer; font-family: inherit;'>🖨️ ইনভয়েস প্রিন্ট করুন</button>"
            voucher_html += "</div></div>"
            st.markdown(voucher_html, unsafe_allow_html=True)

# ----------------- ৫. বাকি টাকা আদায় (Due Receive) -----------------
elif menu_index == 5:
    st.header("💵 পূর্বের বাকি টাকা আদায় এন্ট্রি")
    st.caption("সেলসম্যান যখন কোনো কাস্টমার বা ডিলারের কাছ থেকে পূর্বে বাকি থাকা টাকা সংগ্রহ করবেন, তখন এই এন্ট্রি দিন।")
    
    salesmen_list = [f"SM{str(i).zfill(2)}" for i in range(1, 11)]
    df_sales_record = pd.read_sql("SELECT DISTINCT salesman_id, customer_name FROM sales", conn)
    
    with st.form("due_form", clear_on_submit=True):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            sel_salesman = st.selectbox("সেলসম্যান আইডি নির্বাচন করুন", salesmen_list)
        with col_d2:
            if not df_sales_record.empty and sel_salesman in df_sales_record["salesman_id"].values:
                avail_custs = df_sales_record[df_sales_record["salesman_id"] == sel_salesman]["customer_name"].unique().tolist()
                sel_customer = st.selectbox("কাস্টমার নির্বাচন করুন", avail_custs)
            else:
                sel_customer = st.text_input("কাস্টমার / ডিলারের নাম লিখুন:")
                
        col_date = st.date_input("টাকা আদায়ের তারিখ", date.today())
        collected_amount = st.number_input("আদায়কৃত টাকার পরিমাণ (৳)", min_value=1.0, step=100.0)
        note = st.text_input("মন্তব্য / নোট (যেমন: ক্যাশ, ব্যাংক বা মানি রিসিট নং)")
        
        sub_due = st.form_submit_button("টাকা জমা সম্পন্ন করুন")
        if sub_due and sel_customer.strip() != "":
            cursor.execute("INSERT INTO due_collections (date, salesman_id, customer_name, collected_amount, note) VALUES (?, ?, ?, ?, ?)",
                           (str(col_date), sel_salesman, sel_customer.strip(), collected_amount, note))
            conn.commit()
            st.success(f"সফলভাবে ৳ {collected_amount:,.2f} আদায় সম্পন্ন হয়েছে এবং কাস্টমারের বকেয়া থেকে বাদ দেওয়া হয়েছে!")
            st.rerun()

# ----------------- ৬. রেকর্ড সংশোধন ও ডিলিট -----------------
elif menu_index == 6:
    st.header("🗑️ রেকর্ড সংশোধন ও মুছে ফেলা (Edit / Delete)")
    
    target_table = st.selectbox("কোন সেকশনের ডাটা দেখতে বা সংশোধন করতে চান?", [
        "কাঁচামাল ক্রয় (raw_materials)",
        "বোতল/প্যাকেট ক্রয় (packaging)",
        "ওষুধ উৎপাদন (production)",
        "বিক্রয় রেকর্ড (sales)",
        "বাকি আদায় রেকর্ড (due_collections)"
    ])
    
    table_map = {
        "কাঁচামাল ক্রয় (raw_materials)": "raw_materials",
        "বোতল/প্যাকেট ক্রয় (packaging)": "packaging",
        "ওষুধ উৎপাদন (production)": "production",
        "বিক্রয় রেকর্ড (sales)": "sales",
        "বাকি আদায় রেকর্ড (due_collections)": "due_collections"
    }
    
    selected_db_table = table_map[target_table]
    df_current = pd.read_sql(f"SELECT * FROM {selected_db_table}", conn)
    
    if not df_current.empty:
        st.write("বর্তমান এন্ট্রিগুলোর তালিকা (আইডি নম্বরসহ):")
        st.dataframe(df_current, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🛠️ একশন নির্বাচন করুন")
        action = st.radio("আপনি কি করতে চান?", ["ডিলিট (Delete) করুন", "সংশোধন (Edit) করুন"], horizontal=True)
        
        target_id = st.number_input("যে এন্ট্রিটি পরিবর্তন বা মুছে ফেলতে চান তার ID নম্বর লিখুন:", min_value=1, step=1)
        
        # Check if ID exists
        row_exists = not df_current[df_current['id'] == target_id].empty
        
        if action == "ডিলিট (Delete) করুন":
            if st.button("🚨 রেকর্ডটি স্থায়ীভাবে মুছে ফেলুন"):
                if row_exists:
                    cursor.execute(f"DELETE FROM {selected_db_table} WHERE id = ?", (target_id,))
                    conn.commit()
                    st.warning(f"আইডি {target_id} সফলভাবে মুছে ফেলা হয়েছে!")
                    st.rerun()
                else:
                    st.error("এই আইডির কোনো ডেটা পাওয়া যায়নি!")
                    
        elif action == "সংশোধন (Edit) করুন":
            if row_exists:
                st.info("নিচের ফিল্ডগুলো এডিট করে আপডেট বাটনে ক্লিক করুন:")
                row_data = df_current[df_current['id'] == target_id].iloc[0]
                
                # Exclude ID from editing
                editable_cols = [col for col in df_current.columns if col != 'id']
                
                with st.form("edit_form"):
                    new_values = {}
                    for col in editable_cols:
                        old_val = row_data[col]
                        # Create dynamic input based on data type
                        if pd.isna(old_val):
                            old_val = ""
                        
                        if isinstance(old_val, (int, float, int)):
                            new_values[col] = st.number_input(f"{col}", value=float(old_val))
                        else:
                            new_values[col] = st.text_input(f"{col}", value=str(old_val))
                            
                    if st.form_submit_button("✅ আপডেট করুন"):
                        # Generate SQL update query dynamically
                        set_clause = ", ".join([f"{col} = ?" for col in editable_cols])
                        values_tuple = tuple(new_values[col] for col in editable_cols) + (target_id,)
                        
                        query = f"UPDATE {selected_db_table} SET {set_clause} WHERE id = ?"
                        cursor.execute(query, values_tuple)
                        conn.commit()
                        st.success(f"আইডি {target_id} সফলভাবে আপডেট করা হয়েছে!")
                        st.rerun()
            else:
                st.warning("সঠিক আইডি নম্বর দিন।")
    else:
        st.info("এই সেকশনে বর্তমানে কোনো ডাটা নেই।")
