import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# পেজ কনফিগারেশন
st.set_page_config(page_title="MG Agro Pharma Inventory", layout="wide")

# ডাটাবেস ইনিশিয়ালাইজেশন
conn = sqlite3.connect("mg_agro_pharma.db", check_same_thread=False)
cursor = conn.cursor()

# টেবিল তৈরি
cursor.execute("""
CREATE TABLE IF NOT EXISTS raw_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    item_name TEXT,
    unit TEXT,
    quantity REAL,
    cost_per_unit REAL,
    total_cost REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS packaging (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    bottle_size TEXT,
    quantity INTEGER,
    unit_price REAL,
    total_cost REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS production (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    product_name TEXT,
    size TEXT,
    bottles_produced INTEGER,
    raw_material_used TEXT,
    raw_quantity_used REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    salesman_id TEXT,
    customer_name TEXT,
    product_name TEXT,
    size TEXT,
    quantity INTEGER,
    total_bill REAL,
    cash_received REAL,
    due_amount REAL
)
""")
conn.commit()

# হেডার
st.title("🏭 এমজি এগ্রো ফার্মা (MG Agro Pharma)")
st.subheader("স্বয়ংক্রিয় ইনভেন্টরি ও সেলস ম্যানেজমেন্ট সিস্টেম")
st.markdown("---")

# মেন্যু নির্বাচন
menu = st.sidebar.radio(
    "মেন্যু নির্বাচন করুন:",
    ["📊 লাইভ ড্যাশবোর্ড", "🧪 কাঁচামাল ক্রয় এন্ট্রি", "🧴 বোতল/প্যাকেট ক্রয়", "⚙️ ওষুধ উৎপাদন এন্ট্রি", "🚚 বিক্রয় ও চালান এন্ট্রি"]
)

# ----------------- ১. লাইভ ড্যাশবোর্ড -----------------
if menu == "📊 লাইভ ড্যাশবোর্ড":
    st.header("📈 রিয়েল-টাইম স্টক ও ব্যালেন্স রিপোর্ট")
    
    # ডেটা লোড
    df_raw = pd.read_sql("SELECT * FROM raw_materials", conn)
    df_pack = pd.read_sql("SELECT * FROM packaging", conn)
    df_prod = pd.read_sql("SELECT * FROM production", conn)
    df_sales = pd.read_sql("SELECT * FROM sales", conn)
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_raw_cost = df_raw["total_cost"].sum() if not df_raw.empty else 0
    total_pack_cost = df_pack["total_cost"].sum() if not df_pack.empty else 0
    total_sales = df_sales["total_bill"].sum() if not df_sales.empty else 0
    total_due = df_sales["due_amount"].sum() if not df_sales.empty else 0
    
    col1.metric("মোট কাঁচামাল ক্রয়", f"৳ {total_raw_cost:,.2f}")
    col2.metric("মোট প্যাকেজিং খরচ", f"৳ {total_pack_cost:,.2f}")
    col3.metric("মোট বিক্রয় বিল", f"৳ {total_sales:,.2f}")
    col4.metric("মার্কেটে মোট বাকি (Due)", f"৳ {total_due:,.2f}", delta_color="inverse")
    
    st.markdown("---")
    
    # ফিনিশড প্রডাক্ট স্টক
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

    # কাঁচামালের বর্তমান স্টক
    st.subheader("🧪 কাঁচামালের বর্তমান মজুদ (Raw Material Stock)")
    if not df_raw.empty:
        raw_in = df_raw.groupby(["item_name", "unit"])["quantity"].sum().reset_index()
        if not df_prod.empty:
            raw_out = df_prod.groupby("raw_material_used")["raw_quantity_used"].sum().reset_index()
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

# ----------------- ২. কাঁচামাল ক্রয় এন্ট্রি -----------------
elif menu == "🧪 কাঁচামাল ক্রয় এন্ট্রি":
    st.header("🧪 নতুন কাঁচামাল ক্রয় ইনপুট")
    with st.form("raw_form", clear_on_submit=True):
        entry_date = st.date_input("ক্রয়ের তারিখ", date.today())
        item_name = st.selectbox("কাঁচামালের নাম", ["Zinc", "Acid", "Calcium", "Vitamin AD3E", "অন্যান্য"])
        if item_name == "অন্যান্য":
            item_name = st.text_input("নতুন কাঁচামালের নাম লিখুন:")
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
elif menu == "🧴 বোতল/প্যাকেট ক্রয়":
    st.header("🧴 খালি বোতল / প্যাকেট ক্রয় ইনপুট")
    with st.form("pack_form", clear_on_submit=True):
        entry_date = st.date_input("ক্রয়ের তারিখ", date.today())
        bottle_size = st.selectbox("বোতলের সাইজ", ["10ml", "15ml", "20ml", "50ml", "100ml", "125ml", "200 ml", "250 ml", "500 ml", "1000 ml", "অন্যান্য"])
        if bottle_size == "অন্যান্য":
            bottle_size = st.text_input("সাইজ লিখুন:")
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
elif menu == "⚙️ ওষুধ উৎপাদন এন্ট্রি":
    st.header("⚙️ ওষুধ উৎপাদন (Production) ইনপুট")
    st.caption("ওষুধ উৎপাদনের এন্ট্রি দিলে স্বয়ংক্রিয়ভাবে কাঁচামাল ও বোতল স্টক থেকে কমে যাবে।")
    
    product_list = [
        "MG -Cal", "MG -liver sol", "MG -Sol -E", "MG -PH", "MG -FERO VET", 
        "MG -Enzyme", "MG -AD3E", "MG -ZINC VET", "MG -Multi plus", "MG -COF NIL", 
        "MG-DB", "MG-VIT-C", "MG-RUMEN", "MG-Milk & Milk"
    ]
    
    with st.form("prod_form", clear_on_submit=True):
        entry_date = st.date_input("উৎপাদনের তারিখ", date.today())
        product_name = st.selectbox("ওষুধের নাম", product_list)
        size = st.selectbox("বোতলের সাইজ", ["100ml", "200 ml", "500 ml", "1000 ml", "100gm", "1kg"])
        bottles_produced = st.number_input("কত বোতল/প্যাকেট তৈরি হলো?", min_value=1, step=1)
        
        st.markdown("##### ব্যবহৃত কাঁচামাল:")
        raw_used = st.selectbox("কোন কাঁচামাল ব্যবহার হয়েছে?", ["Zinc", "Acid", "Calcium", "Vitamin AD3E", "অন্যান্য"])
        raw_qty = st.number_input("ব্যবহৃত কাঁচামালের পরিমাণ (Kg/Ltr)", min_value=0.0, step=0.1)
        
        submitted = st.form_submit_button("উৎপাদন সম্পন্ন করুন")
        if submitted:
            cursor.execute("""
            INSERT INTO production (date, product_name, size, bottles_produced, raw_material_used, raw_quantity_used)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (str(entry_date), product_name, size, bottles_produced, raw_used, raw_qty))
            conn.commit()
            st.success(f"{product_name} ({size}) - {bottles_produced} বোতল উৎপাদিত হয়েছে এবং ইনভেন্টরিতে যোগ হয়েছে!")

# ----------------- ৫. বিক্রয় ও ডেলিভারি এন্ট্রি -----------------
elif menu == "🚚 বিক্রয় ও চালান এন্ট্রি":
    st.header("🚚 বিক্রয় ও সেলসম্যান হিসাব")
    
    salesmen = [f"SM{str(i).zfill(2)}" for i in range(1, 11)]
    product_list = ["MG -Cal", "MG -liver sol", "MG -Sol -E", "MG -PH", "MG -FERO VET", "MG -Enzyme", "MG -ZINC VET"]
    
    with st.form("sales_form", clear_on_submit=True):
        entry_date = st.date_input("বিক্রয়ের তারিখ", date.today())
        salesman = st.selectbox("সেলসম্যান আইডি", salesmen)
        customer = st.text_input("কাস্টমার / ডিলারের নাম")
        prod = st.selectbox("পণ্য নির্বাচন করুন", product_list)
        size = st.selectbox("প্যাক সাইজ", ["100ml", "200 ml", "500 ml", "1000 ml"])
        qty = st.number_input("বিক্রিত সংখ্যা (পিস)", min_value=1, step=1)
        tp_value = st.number_input("রেট / মূল্য (TP Value)", min_value=0.0, step=1.0)
        
        cash_received = st.number_input("নগদ আদায় (Cash Received)", min_value=0.0, step=1.0)
        
        submitted = st.form_submit_button("বিক্রয় সাবমিট করুন")
        if submitted and customer:
            total_bill = qty * tp_value
            due = total_bill - cash_received
            cursor.execute("""
            INSERT INTO sales (date, salesman_id, customer_name, product_name, size, quantity, total_bill, cash_received, due_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(entry_date), salesman, customer, prod, size, qty, total_bill, cash_received, due))
            conn.commit()
            st.success(f"বিক্রয় সফল! মোট বিল: ৳ {total_bill:,.2f} | নগদ: ৳ {cash_received:,.2f} | বাকি: ৳ {due:,.2f}")