import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import io

# পেজ কনফিগারেশন
st.set_page_config(page_title="MG Agro Pharma Inventory", layout="wide", initial_sidebar_state="expanded")

# ফন্ট ও সিএসএস
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

# টেবিল তৈরি
cursor.execute("""
CREATE TABLE IF NOT EXISTS item_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
""")

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
    bottles_produced INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS production_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    production_id INTEGER,
    raw_material_used TEXT,
    raw_quantity_used REAL,
    FOREIGN KEY(production_id) REFERENCES production(id)
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

# ডিফল্ট কাঁচামাল নিশ্চিত করা
default_items = ["Zinc", "Acid", "Calcium", "Vitamin AD3E", "Magnesium", "Cobalt"]
for d_item in default_items:
    cursor.execute("INSERT OR IGNORE INTO item_list (name) VALUES (?)", (d_item,))
conn.commit()

# হেডার
st.title("🏭 এমজি এগ্রো ফার্মা (MG Agro Pharma)")
st.caption("স্মার্ট ইনভেন্টরি, প্রোডাকশন ও সেলস ট্র্যাকিং সফটওয়্যার")
st.markdown("---")

# মেন্যু নির্বাচন
menu = st.sidebar.radio(
    "মেন্যু নির্বাচন করুন:",
    [
        "📊 লাইভ ড্যাশবোর্ড", 
        "🧪 কাঁচামাল ক্রয় এন্ট্রি", 
        "🧴 বোতল/প্যাকেট ক্রয়", 
        "⚙️ ওষুধ উৎপাদন এন্ট্রি", 
        "🚚 বিক্রয় ও চালান এন্ট্রি",
        "🗑️ রেকর্ড সংশোধন ও ডিলিট"
    ]
)

# ----------------- ১. লাইভ ড্যাশবোর্ড -----------------
if menu == "📊 লাইভ ড্যাশবোর্ড":
    st.header("📈 রিয়েল-টাইম স্টক ও ব্যালেন্স রিপোর্ট")
    
    df_raw = pd.read_sql("SELECT * FROM raw_materials", conn)
    df_pack = pd.read_sql("SELECT * FROM packaging", conn)
    df_prod = pd.read_sql("SELECT * FROM production", conn)
    df_used = pd.read_sql("SELECT * FROM production_materials", conn)
    df_sales = pd.read_sql("SELECT * FROM sales", conn)
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_raw_cost = df_raw["total_cost"].sum() if not df_raw.empty else 0
    total_pack_cost = df_pack["total_cost"].sum() if not df_pack.empty else 0
    total_sales = df_sales["total_bill"].sum() if not df_sales.empty else 0
    total_due = df_sales["due_amount"].sum() if not df_sales.empty else 0
    
    col1.metric("মোট কাঁচামাল ক্রয়", f"৳ {total_raw_cost:,.2f}")
    col2.metric("মোট প্যাকেজিং খরচ", f"৳ {total_pack_cost:,.2f}")
    col3.metric("মোট বিক্রয় বিল", f"৳ {total_sales:,.2f}")
    col4.metric("মার্কেটে মোট বাকি (Due)", f"৳ {total_due:,.2f}")
    
    st.markdown("---")
    
    # এক্সেল ডাউনলোড বাটন
    st.subheader("📥 এক্সেল রিপোর্ট ডাউনলোড")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_raw.to_excel(writer, sheet_name='Raw Materials', index=False)
        df_pack.to_excel(writer, sheet_name='Packaging', index=False)
        df_prod.to_excel(writer, sheet_name='Production', index=False)
        df_used.to_excel(writer, sheet_name='Used Materials', index=False)
        df_sales.to_excel(writer, sheet_name='Sales', index=False)
    processed_data = output.getvalue()
    
    st.download_button(
        label="📊 সম্পূর্ণ ইনভেন্টরি রিপোর্ট ডাউনলোড করুন (Excel)",
        data=processed_data,
        file_name=f"MG_Agro_Pharma_Report_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.markdown("---")
    
    # তৈরি পণ্যের স্টক
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

    # বোতল ও প্যাকেটের মজুদ
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

    # সেলসম্যান ও কাস্টমারভিত্তিক হিসাব
    st.markdown("---")
    st.subheader("👥 সেলসম্যান ও কাস্টমারভিত্তিক বিক্রয় ও বাকির হিসাব")
    
    if not df_sales.empty:
        sm_summary = df_sales.groupby("salesman_id").agg({
            "total_bill": "sum",
            "cash_received": "sum",
            "due_amount": "sum"
        }).reset_index()
        
        sm_summary.rename(columns={
            "salesman_id": "সেলসম্যান আইডি",
            "total_bill": "মোট বিক্রি (৳)",
            "cash_received": "নগদ আদায় (৳)",
            "due_amount": "মোট বাকি (৳)"
        }, inplace=True)
        
        st.write("📌 **সকল সেলসম্যানের সারসংক্ষেপ (Summary):**")
        st.dataframe(sm_summary, use_container_width=True)
        
        st.write("🔍 **নির্দিষ্ট সেলসম্যান অনুযায়ী কাস্টমার খতিয়ান:**")
        selected_sm = st.selectbox("কোন সেলসম্যানের কাস্টমার লিস্ট দেখতে চান?", sm_summary["সেলসম্যান আইডি"].unique())
        
        cust_df = df_sales[df_sales["salesman_id"] == selected_sm].groupby(["customer_name"]).agg({
            "total_bill": "sum",
            "cash_received": "sum",
            "due_amount": "sum"
        }).reset_index()
        
        cust_df.rename(columns={
            "customer_name": "কাস্টমার / ডিলারের নাম",
            "total_bill": "মোট ক্রয় বিল (৳)",
            "cash_received": "পরিশোধিত টাকা (৳)",
            "due_amount": "বাকি টাকা (৳)"
        }, inplace=True)
        
        st.dataframe(cust_df, use_container_width=True)
    else:
        st.info("এখনো কোনো বিক্রয় রেকর্ড এন্ট্রি করা হয়নি।")

# ----------------- ২. কাঁচামাল ক্রয় এন্ট্রি -----------------
elif menu == "🧪 কাঁচামাল ক্রয় এন্ট্রি":
    st.header("🧪 কাঁচামাল ক্রয় ইনপুট")
    
    with st.expander("➕ তালিকায় সম্পূর্ণ নতুন কোনো কাঁচামাল যুক্ত করতে এখানে ক্লিক করুন"):
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
elif menu == "🧴 বোতল/প্যাকেট ক্রয়":
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

# ----------------- ৪. ওষুধ উৎপাদন এন্ট্রি (মাল্টি-কাঁচামাল সাপোর্ট) -----------------
elif menu == "⚙️ ওষুধ উৎপাদন এন্ট্রি":
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
            cursor.execute("""
            INSERT INTO production (date, product_name, size, bottles_produced)
            VALUES (?, ?, ?, ?)
            """, (str(entry_date), product_name, size, bottles_produced))
            prod_id = cursor.lastrowid
            
            for mat_name, mat_qty in used_materials_data:
                if mat_qty > 0:
                    cursor.execute("""
                    INSERT INTO production_materials (production_id, raw_material_used, raw_quantity_used)
                    VALUES (?, ?, ?)
                    """, (prod_id, mat_name, mat_qty))
            
            conn.commit()
            st.success(f"{product_name} ({size}) - {bottles_produced} বোতল সফলভাবে উৎপাদিত হয়েছে এবং সমস্ত কাঁচামাল স্টক থেকে মাইনাস হয়েছে!")

# ----------------- ৫. বিক্রয় ও ডেলিভারি এন্ট্রি -----------------
elif menu == "🚚 বিক্রয় ও চালান এন্ট্রি":
    st.header("🚚 বিক্রয় ও সেলসম্যান হিসাব")
    
    salesmen = [f"SM{str(i).zfill(2)}" for i in range(1, 11)]
    product_list = [
        "MG -Cal", "MG -liver sol", "MG -Sol -E", "MG -PH", "MG -FERO VET", 
        "MG -Enzyme", "MG -AD3E", "MG -ZINC VET", "MG -Multi plus", "MG -COF NIL", 
        "MG-DB", "MG-VIT-C", "MG-RUMEN", "MG-Milk & Milk"
    ]
    
    with st.form("sales_form", clear_on_submit=True):
        entry_date = st.date_input("বিক্রয়ের তারিখ", date.today())
        salesman = st.selectbox("সেলসম্যান আইডি", salesmen)
        customer = st.text_input("কাস্টমার / ডিলারের নাম")
        prod = st.selectbox("পণ্য নির্বাচন করুন", product_list)
        size = st.selectbox("প্যাক সাইজ", ["10ml", "15ml", "20ml", "50ml", "100ml", "125ml", "200ml", "250ml", "500ml", "1000ml", "100gm", "1kg"])
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

# ----------------- ৬. রেকর্ড সংশোধন ও ডিলিট -----------------
elif menu == "🗑️ রেকর্ড সংশোধন ও ডিলিট":
    st.header("🗑️ রেকর্ড সংশোধন ও মুছে ফেলা")
    
    target_table = st.selectbox("কোন সেকশনের ডাটা দেখতে বা ডিলিট করতে চান?", [
        "কাঁচামাল ক্রয় (raw_materials)",
        "বোতল/প্যাকেট ক্রয় (packaging)",
        "ওষুধ উৎপাদন (production)",
        "ব্যবহৃত কাঁচামাল (production_materials)",
        "বিক্রয় রেকর্ড (sales)"
    ])
    
    table_map = {
        "কাঁচামাল ক্রয় (raw_materials)": "raw_materials",
        "বোতল/প্যাকেট ক্রয় (packaging)": "packaging",
        "ওষুধ উৎপাদন (production)": "production",
        "ব্যবহৃত কাঁচামাল (production_materials)": "production_materials",
        "বিক্রয় রেকর্ড (sales)": "sales"
    }
    
    selected_db_table = table_map[target_table]
    df_current = pd.read_sql(f"SELECT * FROM {selected_db_table}", conn)
    
    if not df_current.empty:
        st.write("বর্তমান এন্ট্রিগুলোর তালিকা (আইডি নম্বরসহ):")
        st.dataframe(df_current, use_container_width=True)
        
        del_id = st.number_input("যে এন্ট্রিটি মুছে ফেলতে চান তার ID নম্বর লিখুন:", min_value=1, step=1)
        if st.button("🚨 রেকর্ডটি স্থায়ীভাবে মুছে ফেলুন"):
            cursor.execute(f"DELETE FROM {selected_db_table} WHERE id = ?", (del_id,))
            conn.commit()
            st.warning(f"আইডি {del_id} সফলভাবে মুছে ফেলা হয়েছে! ড্যাশবোর্ডে গিয়ে রিফ্রেশ করুন।")
            st.rerun()
    else:
        st.info("এই সেকশনে বর্তমানে কোনো ডাটা নেই।")
