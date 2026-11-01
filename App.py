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

st.markdown("""
<style>
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

# লগইন ভেরিফিকেশন সিস্টেম
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

# মূল সফটওয়্যার
st.sidebar.write(f"👤 লগইন আছেন: **{st.session_state['username']}**")
if st.sidebar.button("🚪 লগআউট (Logout)"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.rerun()

st.sidebar.markdown("---")

conn = sqlite3.connect("mg_agro_pharma.db", check_same_thread=False)
cursor = conn.cursor()

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
    
    total_raw_cost = 0.0
    if not df_raw.empty:
        total_raw_cost = float(df_raw["total_cost"].sum())
        
    total_pack_cost = 0.0
    if not df_pack.empty:
        total_pack_cost = float(df_pack["total_cost"].sum())
        
    total_sales = 0.0
    if not df_sales.empty:
        total_sales = float(df_sales["total_bill"].sum())
        
    initial_due = 0.0
    if not df_sales.empty:
        initial_due = float(df_sales["due_amount"].sum())
        
    total_collected = 0.0
    if not df_due_col.empty:
        total_collected = float(df_due_col["collected_amount"].sum())
        
    net_remaining_due = initial_due - total_collected
    
    col1.metric("মোট কাঁচামাল ক্রয়", f"৳ {total_raw_cost:,.2f}")
    col2.metric("মোট প্যাকেজিং খরচ", f"৳ {total_pack_cost:,.2f}")
    col3.metric("মোট বিক্রয় বিল", f"৳ {total_sales:,.2f}")
    col4.metric("মার্কেটে বর্তমান আসল বাকি (Due)", f"৳ {net_remaining_due:,.2f}")
    
    st.markdown("---")
    
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_raw.to_excel(writer, sheet_name='Raw Materials', index=False)
            df_pack.to_excel(writer, sheet_name='Packaging', index=False)
            df_prod.to_excel(writer, sheet_name='Production', index=False)
            df_used.to_excel(writer, sheet_name='Used Materials', index=False)
            df_sales.to_excel(writer, sheet_name='Sales', index=False)
            df_due_col.to_excel(writer, sheet_name='Due Collections', index=False)
        processed_data = output.getvalue()
        
        st.download_button(
            label="📥 সম্পূর্ণ ইনভেন্টরি ও কালেকশন রিপোর্ট ডাউনলোড করুন (Excel)",
            data=processed_data,
            file_name=f"MG_Agro_Pharma_Report_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception:
        pass

    st.markdown("---")
    
    st.subheader("📦 তৈরি ওষুধের বর্তমান মজুদ (Finished Goods Stock)")
    if not df_prod.empty:
        prod_summary = df_prod.groupby(["product_name", "size"])["bottles_produced"].sum().reset_index()
        if not df_sales.empty:
            sales_summary = df_sales.groupby(["product_name", "size"])["quantity"].sum().reset_index()
            stock_df = pd.merge(prod_summary, sales_summary, on=["product_name", "size"], how="left").fillna(0)
            stock_df["বর্তমান স্টক (বোতল)"] = stock_df["bottles_produced"] - stock_df["quantity"]
        else:
            stock_df = prod_summary
            stock_df["বর্তমান স্টক (বোতল)"] = stock_df["bottles_produced"]
            stock_df["quantity"] = 0
            
        stock_df.rename(columns={"product_name": "ওষুধের নাম", "size": "সাইজ", "bottles_produced": "মোট উৎপাদন", "quantity": "মোট বিক্রয়"}, inplace=True)
        st.dataframe(stock_df[["ওষুধের নাম", "সাইজ", "মোট উৎপাদন", "মোট বিক্রয়", "বর্তমান স্টক (বোতল)"]], use_container_width=True)
    else:
        st.info("এখনো কোনো উৎপাদন রেকর্ড নেই।")

    st.subheader("🧪 কাঁচামালের বর্তমান মজুদ (Raw Material Stock)")
    if not df_raw.empty:
        raw_in = df_raw.groupby(["item_name", "unit"])["quantity"].sum().reset_index()
        if not df_used.empty:
            raw_out = df_used.groupby("raw_material_used")["raw_quantity_used"].sum().reset_index()
            raw_stock = pd.merge(raw_in, raw_out, left_on="item_name", right_on="raw_material_used", how="left").fillna(0)
            raw_stock["অবশিষ্ট স্টক"] = raw_stock["quantity"] - raw_stock["raw_quantity_used"]
        else:
            raw_stock = raw_in
            raw_stock["raw_quantity_used"] = 0
            raw_stock["অবশিষ্ট স্টক"] = raw_stock["quantity"]
            
        raw_stock.rename(columns={"item_name": "কাঁচামালের নাম", "unit": "একক", "quantity": "মোট ক্রয়", "raw_quantity_used": "মোট ব্যবহার"}, inplace=True)
        st.dataframe(raw_stock[["কাঁচামালের নাম", "একক", "মোট ক্রয়", "মোট ব্যবহার", "অবশিষ্ট স্টক"]], use_container_width=True)
    else:
        st.info("এখনো কোনো কাঁচামাল ক্রয় এন্ট্রি নেই।")

    st.subheader("🧴 খালি বোতল ও প্যাকেটের বর্তমান মজুদ (Packaging Stock)")
    if not df_pack.empty:
        pack_in = df_pack.groupby("bottle_size")["quantity"].sum().reset_index()
        if not df_prod.empty:
            pack_out = df_prod.groupby("size")["bottles_produced"].sum().reset_index()
            pack_stock = pd.merge(pack_in, pack_out, left_on="bottle_size", right_on="size", how="left").fillna(0)
            pack_stock["অবশিষ্ট স্টক (পিস)"] = pack_stock["quantity"] - pack_stock["bottles_produced"]
        else:
            pack_stock = pack_in
            pack_stock["bottles_produced"] = 0
            pack_stock["অবশিষ্ট স্টক (পিস)"] = pack_stock["quantity"]
            
        pack_stock.rename(columns={"bottle_size": "বোতল/প্যাকেট সাইজ", "quantity": "মোট ক্রয় (পিস)", "bottles_produced": "উৎপাদনে ব্যবহৃত (পিস)"}, inplace=True)
        st.dataframe(pack_stock[["বোতল/প্যাকেট সাইজ", "মোট ক্রয় (পিস)", "উৎপাদনে ব্যবহৃত (পিস)", "অবশিষ্ট স্টক (পিস)"]], use_container_width=True)
    else:
        st.info("এখনো কোনো বোতল/প্যাকেট ক্রয় এন্ট্রি নেই।")

    st.markdown("---")
    st.subheader("👥 সেলসম্যান ও কাস্টমারভিত্তিক বিক্রয়, আদায় ও বাকি খতিয়ান")
    
    if not df_sales.empty:
        sm_sales = df_sales.groupby("salesman_id").agg({
            "total_bill": "sum",
            "cash_received": "sum",
            "due_amount": "sum"
        }).reset_index()
        
        if not df_due_col.empty:
            sm_rec = df_due_col.groupby("salesman_id")["collected_amount"].sum().reset_index()
            sm_summary = pd.merge(sm_sales, sm_rec, on="salesman_id", how="left").fillna(0)
        else:
            sm_summary = sm_sales
            sm_summary["collected_amount"] = 0
            
        sm_summary["মোট নগদ আদায় (৳)"] = sm_summary["cash_received"] + sm_summary["collected_amount"]
        sm_summary["বর্তমান আসল বাকি (৳)"] = sm_summary["due_amount"] - sm_summary["collected_amount"]
        
        sm_summary.rename(columns={
            "salesman_id": "সেলসম্যান আইডি",
            "total_bill": "মোট বিক্রি (৳)",
            "cash_received": "বিক্রিতে নগদ (৳)",
            "collected_amount": "পরে আদায়কৃত বাকি (৳)"
        }, inplace=True)
        
        st.write("📌 **সকল সেলসম্যানের সারসংক্ষেপ:**")
        st.dataframe(sm_summary[["সেলসম্যান আইডি", "মোট বিক্রি (৳)", "বিক্রিতে নগদ (৳)", "পরে আদায়কৃত বাকি (৳)", "মোট নগদ আদায় (৳)", "বর্তমান আসল বাকি (৳)"]], use_container_width=True)
        
        st.write("🔍 **নির্দিষ্ট সেলসম্যানের কাস্টমারভিত্তিক বাকি তালিকা:**")
        selected_sm = st.selectbox("কোন সেলসম্যানের কাস্টমার লিস্ট দেখতে চান?", sm_summary["সেলসম্যান আইডি"].unique())
        
        cust_sales = df_sales[df_sales["salesman_id"] == selected_sm].groupby("customer_name").agg({
            "total_bill": "sum",
            "cash_received": "sum",
            "due_amount": "sum"
        }).reset_index()
        
        if not df_due_col.empty:
            cust_rec = df_due_col[df_due_col["salesman_id"] == selected_sm].groupby("customer_name")["collected_amount"].sum().reset_index()
            cust_df = pd.merge(cust_sales, cust_rec, on="customer_name", how="left").fillna(0)
        else:
            cust_df = cust_sales
            cust_df["collected_amount"] = 0
            
        cust_df["পরিশোধিত মোট টাকা (৳)"] = cust_df["cash_received"] + cust_df["collected_amount"]
        cust_df["বর্তমান বকেয়া টাকা (৳)"] = cust_df["due_amount"] - cust_df["collected_amount"]
        
        cust_df.rename(columns={
            "customer_name": "কাস্টমার / ডিলারের নাম",
            "total_bill": "মোট ক্রয় বিল (৳)"
        }, inplace=True)
        
        st.dataframe(cust_df[["কাস্টমার / ডিলারের নাম", "মোট ক্রয় বিল (৳)", "পরিশোধিত মোট টাকা (৳)", "বর্তমান বকেয়া টাকা (৳)"]], use_container_width=True)
    else:
        st.info("এখনো কোনো বিক্রয় রেকর্ড এন্ট্রি করা হয়নি।")

# ----------------- ২. কাঁচামাল ক্রয় এন্ট্রি -----------------
elif selected_key == "raw_purchase":
    st.header("🧪 কাঁচামাল ক্রয় ইনপুট")
    
    if st.checkbox("➕ তালিকায় সম্পূর্ণ নতুন কোনো কাঁচামাল যুক্ত করতে টিক দিন"):
        new_item_to_add = st.text_input("নতুন কাঁচামালের নাম লিখুন:")
        if st.button("তালিকায় যুক্ত করুন"):
            if new_item_to_add.strip() != "":
                try:
                    cursor.execute("INSERT INTO item_list (name) VALUES (?)", (new_item_to_add.strip(),))
                    conn.commit()
                    st.success(f"'{new_item_to_add}' সফলভাবে ড্রপডাউনে যুক্ত হয়েছে!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.warning("এই নামটি ইতিমধ্যে তালিকায় রয়েছে।")
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

# ----------------- ৩. বোতল/প্যাকেট ক্রয় -----------------
elif selected_key == "packaging_purchase":
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

# ----------------- ৪. ওষুধ উৎপাদন এন্ট্রি -----------------
elif selected_key == "production":
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
