import streamlit as st
import pandas as pd
import sqlite3
import datetime
import hashlib
import uuid
import matplotlib.pyplot as plt
import io
import base64
from datetime import timedelta
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# Database Setup
def init_db():
    conn = sqlite3.connect('treasury.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS main_account (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT DEFAULT 'Main Account',
        balance REAL NOT NULL DEFAULT 0.0,
        created_at TEXT NOT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        department_id TEXT,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS departments (
        id TEXT PRIMARY KEY NOT NULL UNIQUE,
        name TEXT NOT NULL UNIQUE,
        balance REAL DEFAULT 0,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY NOT NULL,
        ref_number TEXT UNIQUE NOT NULL,
        transaction_date TEXT NOT NULL,
        value_date TEXT,
        narration TEXT,
        debit_amount REAL,
        credit_amount REAL,
        tax_percentage REAL,
        tax_amount REAL,
        statement_id TEXT,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        type TEXT,
        credit_type TEXT,
        debit_type TEXT,
        account_name TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS statements (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        upload_date TEXT NOT NULL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS investments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ref_number TEXT UNIQUE NOT NULL,
        amount REAL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        transaction_ref TEXT,
        department_id TEXT,
        account_name TEXT,
        period INTEGER,
        value_date TEXT,
        interest_rate REAL,
        maturity_date TEXT,
        interest REAL,
        withholding_tax REAL,
        maturity_amount REAL,
        allocation_id TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS allocations (
        id TEXT PRIMARY KEY,
        treasury_ref TEXT NOT NULL,
        department_id TEXT,
        amount REAL NOT NULL,
        statement_id TEXT,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        transaction_type TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS taxes_tariffs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        rate REAL NOT NULL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS bank_tariff_guides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bank_name TEXT NOT NULL,
        document_name TEXT NOT NULL,
        document_data BLOB NOT NULL,
        upload_date TEXT NOT NULL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )''')

    # Initialize main account if not exists
    c.execute("SELECT COUNT(*) FROM main_account")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO main_account (name, balance, created_at) VALUES (?, ?, ?)",
                  ('Main Account', 0, datetime.datetime.now().isoformat()))

    # Create default admin user if not exists
    c.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password, role, department_id, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                  ('admin', hashlib.sha256('admin123'.encode('utf-8')).hexdigest(), 'admin', None, 'system', datetime.datetime.now().isoformat()))

    # Create Treasury Department if not exists
    c.execute("SELECT COUNT(*) FROM departments WHERE name = 'Treasury'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO departments (id, name, balance, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
                  (str(uuid.uuid4())[:8], 'Treasury', 0, 'system', datetime.datetime.now().isoformat()))

    conn.commit()
    conn.close()

# Authentication
def check_credentials(username, password):
    conn = sqlite3.connect('treasury.db')
    c = conn.cursor()
    c.execute("SELECT role, department_id FROM users WHERE username = ? AND password = ?",
              (username, hashlib.sha256(password.encode('utf-8')).hexdigest()))
    result = c.fetchone()
    conn.close()
    return result if result else None

# CSS Styling
def load_css():
    st.markdown("""
    <style>
    :root {
        --primary-color: #003366;
        --secondary-color: #D4AF37;
        --accent-color: #0077B6;
        --background-color: #f8f9fa;
        --text-color: #333333;
        --light-gray: #e9ecef;
    }
    
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        text-align: center;
        border-left: 4px solid var(--primary-color);
    }
    
    .metric-title {
        font-size: 14px;
        color: #555;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: var(--primary-color);
    }
    
    .section-header {
        color: var(--primary-color);
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 15px;
        border-bottom: 2px solid var(--secondary-color);
        padding-bottom: 6px;
    }
    
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        background-color: white;
        border-top: 5px solid var(--primary-color);
    }
    
    .login-title {
        color: var(--primary-color);
        text-align: center;
        margin-bottom: 30px;
    }
    
    .login-button {
        background-color: var(--primary-color) !important;
        color: white !important;
        border: none !important;
        width: 100%;
    }
    
    .required-field::after {
        content: " *";
        color: red;
    }
    
    .sidebar .sidebar-content {
        background-color: var(--primary-color);
        color: white;
    }
    
    .st-bb {
        background-color: transparent;
    }
    
    .st-at {
        background-color: white;
    }
    
    [data-testid="stSidebar"] {
        background-color: var(--primary-color);
    }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

def show_login_page():
    st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #003366 0%, #0077B6 100%);
        height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .login-container {
        background: white;
        border-radius: 10px;
        padding: 30px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        width: 400px;
    }
    
    .login-header {
        color: #003366;
        text-align: center;
        margin-bottom: 30px;
    }
    
    .login-header h1 {
        font-weight: 700;
        margin-bottom: 10px;
    }
    
    .login-header img {
        width: 80px;
        margin-bottom: 15px;
    }
    
    .stButton>button {
        background-color: #003366 !important;
        color: white !important;
        border: none !important;
        width: 100%;
        padding: 10px;
        border-radius: 5px;
        font-weight: 500;
    }
    
    .stButton>button:hover {
        background-color: #004080 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container():
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.markdown("""
            <div class="login-header">
                <h1>Corporate Treasury System</h1>
                <p>Please login to continue</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Username", key="username_input")
                password = st.text_input("Password", type="password", key="password_input")
                
                if st.form_submit_button("Login", use_container_width=True):
                    result = check_credentials(username, password)
                    if result:
                        st.session_state.logged_in = True
                        st.session_state.role = result[0]
                        st.session_state.department_id = result[1]
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
            
            st.markdown('</div>', unsafe_allow_html=True)

def show_dashboard(conn):
    st.markdown('<div class="section-header">Dashboard Overview</div>', unsafe_allow_html=True)
    
    try:
        c = conn.cursor()
        
        # Main metrics
        c.execute("SELECT balance FROM main_account LIMIT 1")
        main_balance_result = c.fetchone()
        main_balance = main_balance_result[0] if main_balance_result else 0.0
        
        c.execute("SELECT balance FROM departments WHERE name = 'Treasury' LIMIT 1")
        treasury_result = c.fetchone()
        treasury_balance = treasury_result[0] if treasury_result else 0.0
        
        c.execute("SELECT COUNT(*) FROM departments")
        department_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM transactions")
        transaction_count = c.fetchone()[0]
        
        # Department data
        department_df = pd.read_sql("SELECT name, balance FROM departments WHERE balance IS NOT NULL", conn)
        
        # Investment data
        active_investments = pd.read_sql("""
        SELECT d.name AS department, COUNT(i.id) AS count
        FROM investments i
        JOIN departments d ON i.department_id = d.id
        WHERE i.status = 'confirmed' AND i.maturity_date >= date('now')
        GROUP BY d.name
        """, conn)
        
        # Account distribution
        account_dist = pd.read_sql("""
        SELECT account_name, COUNT(*) as count
        FROM transactions
        WHERE account_name IN ('CBZ Account One', 'CBZ Account Two', 'ZB Account One', 'ZB Account Two')
        GROUP BY account_name
        """, conn)
        
        # ===== TOP ROW - 4 METRICS =====
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Main Account</div>
                <div class="metric-value">${main_balance:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Treasury Account</div>
                <div class="metric-value">${treasury_balance:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Departments</div>
                <div class="metric-value">{department_count}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Transactions</div>
                <div class="metric-value">{transaction_count}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # ===== SECOND ROW - GRAPH + PIE CHART =====
        col5, col6 = st.columns([2, 1])
        
        with col5:
            st.markdown('<div class="section-header">Department Balances</div>', unsafe_allow_html=True)
            if not department_df.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=department_df['name'],
                    y=department_df['balance'],
                    marker_color='#003366'
                ))
                fig.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    xaxis_title="Department",
                    yaxis_title="Amount ($)",
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No department data available")
        
        with col6:
            st.markdown('<div class="section-header">Department Allocation</div>', unsafe_allow_html=True)
            if not department_df.empty:
                fig = go.Figure()
                fig.add_trace(go.Pie(
                    labels=department_df['name'],
                    values=department_df['balance'],
                    marker_colors=['#003366', '#D4AF37', '#0077B6', '#2A9D8F'],
                    hole=0.4
                ))
                fig.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No department data available")
        
        # ===== THIRD ROW - GRAPH + PIE CHART =====
        col7, col8 = st.columns([2, 1])
        
        with col7:
            st.markdown('<div class="section-header">Active Investments by Department</div>', unsafe_allow_html=True)
            if not active_investments.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=active_investments['department'],
                    y=active_investments['count'],
                    marker_color='#D4AF37'
                ))
                fig.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    xaxis_title="Department",
                    yaxis_title="Number of Investments",
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No active investments found")
        
        with col8:
            st.markdown('<div class="section-header">Account Distribution</div>', unsafe_allow_html=True)
            if not account_dist.empty:
                fig = go.Figure()
                fig.add_trace(go.Pie(
                    labels=account_dist['account_name'],
                    values=account_dist['count'],
                    marker_colors=['#003366', '#D4AF37', '#0077B6', '#2A9D8F'],
                    hole=0.4
                ))
                fig.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No transaction data available")
    
    except Exception as e:
        st.error(f"Error loading dashboard data: {str(e)}")

def validate_date(date_text):
    """Validate if the date string is in YYYY-MM-DD format."""
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except Exception:
        return False

def generate_transaction_template():
    output = io.StringIO()
    df = pd.DataFrame([{
        'transaction_date': '2024-01-01',
        'value_date': '2024-01-01',
        'narration': 'Sample Transaction',
        'ref_number': 'ABC12345',
        'debit_amount': 0.0,
        'credit_amount': 100.0,
        'tax_percentage': 0.0,
        'tax_amount': 0.0
    }])
    df.to_csv(output, index=False)
    return output.getvalue()

def generate_statement_csv(start_date, end_date):
    conn = sqlite3.connect('treasury.db')
    query = """
    SELECT transaction_date, value_date, narration, ref_number,
           debit_amount, credit_amount, tax_percentage, tax_amount, account_name
    FROM transactions
    WHERE transaction_date BETWEEN ? AND ?
    ORDER BY transaction_date ASC
    """
    df = pd.read_sql(query, conn, params=(start_date.isoformat(), end_date.isoformat()))
    conn.close()
    
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()

def main():
    init_db()
    load_css()
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.department_id = None
    
    if not st.session_state.logged_in:
        show_login_page()
        return
    
    conn = sqlite3.connect('treasury.db')
    c = conn.cursor()
    
    # Define account options at the start of main function
    account_options = [
        "CBZ Account One",
        "CBZ Account Two",
        "ZB Account One",
        "ZB Account Two"
    ]
    
    with st.sidebar:
        st.markdown("""
        <style>
        .sidebar-title {
            color: white;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .sidebar-option {
            color: white;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .sidebar-option:hover {
            background-color: rgba(255,255,255,0.1);
        }
        
        .sidebar-option.active {
            background-color: #D4AF37;
            color: #003366;
            font-weight: bold;
        }
        
        .logout-btn {
            margin-top: 30px;
            background-color: #D4AF37 !important;
            color: #003366 !important;
            font-weight: bold !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-title">Treasury System</div>', unsafe_allow_html=True)
        
        if st.session_state.role == "admin":
            selected = option_menu(
                menu_title=None,
                options=["Dashboard", "Transactions", "Allocations", "Statements",
                         "Investments", "Reconciliation", "Tariff & Tax", "User Management"],
                icons=["speedometer", "cash-stack", "arrow-left-right", "file-earmark-text",
                       "graph-up-arrow", "check-circle", "percent", "people"],
                menu_icon="cast",
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "#003366"},
                    "icon": {"color": "white", "font-size": "16px"},
                    "nav-link": {
                        "font-size": "16px",
                        "text-align": "left",
                        "margin": "5px 0",
                        "color": "white",
                        "border-radius": "5px",
                        "padding": "10px",
                    },
                    "nav-link-selected": {"background-color": "#D4AF37", "color": "#003366"},
                }
            )
        else:
            selected = option_menu(
                menu_title=None,
                options=["Dashboard", "Statements", "Investments", "Allocations"],
                icons=["speedometer", "file-earmark-text", "graph-up-arrow", "arrow-left-right"],
                menu_icon="cast",
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "#003366"},
                    "icon": {"color": "white", "font-size": "16px"},
                    "nav-link": {
                        "font-size": "16px",
                        "text-align": "left",
                        "margin": "5px 0",
                        "color": "white",
                        "border-radius": "5px",
                        "padding": "10px",
                    },
                    "nav-link-selected": {"background-color": "#D4AF37", "color": "#003366"},
                }
            )
        
        if st.button("Logout", key="logout_btn", use_container_width=True, type="primary"):
            st.session_state.logged_in = False
            st.session_state.role = None
            st.session_state.department_id = None
            st.rerun()
    
    if selected == "Dashboard":
        show_dashboard(conn)
    
    elif selected == "Transactions" and st.session_state.role == "admin":
        st.markdown('<div class="section-header">Add New Transaction</div>', unsafe_allow_html=True)
        
        with st.form("transaction_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="required-field">Transaction Date</div>', unsafe_allow_html=True)
                transaction_date = st.date_input("Transaction Date", label_visibility="collapsed")
                
                st.markdown('<div class="required-field">Narration</div>', unsafe_allow_html=True)
                narration = st.text_input("Narration", placeholder="Enter transaction description", label_visibility="collapsed")
            
            with col2:
                st.markdown('<div class="required-field">Account Name</div>', unsafe_allow_html=True)
                account_name = st.selectbox("Account Name", options=account_options, label_visibility="collapsed")
            
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown('<div class="required-field">Debit Amount ($)</div>', unsafe_allow_html=True)
                debit_amount = st.number_input("Debit Amount ($)", min_value=0.0, value=0.0, label_visibility="collapsed")
            
            with col4:
                st.markdown('<div class="required-field">Credit Amount ($)</div>', unsafe_allow_html=True)
                credit_amount = st.number_input("Credit Amount ($)", min_value=0.0, value=0.0, label_visibility="collapsed")
            
            tax_percentage = st.number_input("Tax Percentage (%)", min_value=0.0, max_value=100.0, value=0.0)
            investment_transaction = st.checkbox("Investment Transaction")
            
            tax_amount = 0.0
            net_amount = 0.0
            
            if debit_amount > 0:
                tax_amount = debit_amount * (tax_percentage / 100)
                net_amount = debit_amount
            elif credit_amount > 0:
                tax_amount = credit_amount * (tax_percentage / 100)
                net_amount = credit_amount - tax_amount
            
            if tax_percentage > 0:
                st.markdown(f"**Tax Amount ($):** {tax_amount:,.2f}")
                st.markdown(f"**Net Amount ($):** {net_amount:,.2f}")
            
            if st.form_submit_button("Add Transaction"):
                if debit_amount > 0 and credit_amount > 0:
                    st.error("Cannot have both debit and credit amounts")
                elif debit_amount == 0 and credit_amount == 0:
                    st.error("Must enter either debit or credit amount")
                else:
                    transaction_type = "Debit" if debit_amount > 0 else "Credit"
                    amount = debit_amount if debit_amount > 0 else credit_amount
                    
                    debit_type = "Investment" if investment_transaction and transaction_type == "Debit" else "Other" if transaction_type == "Debit" else None
                    credit_type = "Credit Investments" if investment_transaction and transaction_type == "Credit" else "Other" if transaction_type == "Credit" else None
                    
                    ref_number = str(uuid.uuid4())[:8]
                    value_date = transaction_date
                    transaction_id = str(uuid.uuid4())[:8]
                    
                    c.execute("SELECT balance FROM main_account LIMIT 1")
                    main_balance = c.fetchone()[0] or 0.0
                    
                    total_debit = debit_amount + tax_amount if transaction_type == "Debit" else 0.0
                    
                    if transaction_type == "Debit" and main_balance < total_debit:
                        st.error(f"Insufficient Main Account balance for debit transaction (${total_debit:,.2f} required).")
                    else:
                        try:
                            with conn:
                                # Insert transaction with all 16 columns
                                c.execute("""
                                INSERT INTO transactions (
                                    id, ref_number, transaction_date, value_date, narration,
                                    debit_amount, credit_amount, tax_percentage, tax_amount,
                                    type, debit_type, credit_type, created_by, created_at, account_name
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    transaction_id,  # id
                                    ref_number,  # ref_number
                                    transaction_date.isoformat(),  # transaction_date
                                    value_date.isoformat(),  # value_date
                                    narration,  # narration
                                    debit_amount,  # debit_amount
                                    credit_amount,  # credit_amount
                                    tax_percentage,  # tax_percentage
                                    tax_amount,  # tax_amount
                                    transaction_type,  # type
                                    debit_type,  # debit_type
                                    credit_type,  # credit_type
                                    st.session_state.role,  # created_by
                                    datetime.datetime.now().isoformat(),  # created_at
                                    account_name  # account_name
                                ))
                                
                                if transaction_type == "Debit":
                                    c.execute("UPDATE main_account SET balance = balance - ?", (total_debit,))
                                else:
                                    c.execute("UPDATE main_account SET balance = balance + ?", (net_amount,))
                                
                                allocation_id = str(uuid.uuid4())[:8]
                                allocation_amount = net_amount if transaction_type == "Credit" else debit_amount
                                
                                c.execute("""
                                INSERT INTO allocations (
                                    id, treasury_ref, amount, created_by, created_at, transaction_type
                                ) VALUES (?, ?, ?, ?, ?, ?)
                                """, (
                                    allocation_id, ref_number, allocation_amount, st.session_state.role,
                                    datetime.datetime.now().isoformat(), transaction_type
                                ))
                                
                                if investment_transaction:
                                    c.execute("""
                                    INSERT INTO investments (
                                        ref_number, amount, created_by, created_at, status, transaction_ref, allocation_id
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        ref_number, allocation_amount, st.session_state.role,
                                        datetime.datetime.now().isoformat(), 'pending', ref_number, allocation_id
                                    ))
                                
                                st.success("Transaction added successfully! Investment transactions must be allocated in the Investments section.")
                                
                                c.execute("SELECT balance FROM main_account LIMIT 1")
                                new_main_balance = c.fetchone()[0]
                                st.info(f"Updated Main Account Balance: ${new_main_balance:,.2f}")
                        
                        except Exception as e:
                            st.error(f"Error processing transaction: {str(e)}")
                            conn.rollback()
        
        st.markdown('<div class="section-header">Recent Transactions</div>', unsafe_allow_html=True)
        recent_transactions = pd.read_sql("""
        SELECT t.ref_number, t.transaction_date, t.account_name,
               t.narration, t.debit_amount, t.credit_amount, t.tax_percentage, t.tax_amount
        FROM transactions t
        ORDER BY t.transaction_date DESC
        LIMIT 20
        """, conn)
        
        if not recent_transactions.empty:
            st.dataframe(recent_transactions)
        else:
            st.info("No recent transactions found")
        
        st.markdown('<div class="section-header">Bulk Transaction Upload</div>', unsafe_allow_html=True)
        st.markdown("""
        **Expected CSV Format**<br>
        Columns: transaction_date, value_date, narration, ref_number, debit_amount, credit_amount, tax_percentage, tax_amount<br>
        Dates should be in YYYY-MM-DD format
        """, unsafe_allow_html=True)
        
        st.download_button(
            label="Download CSV Template",
            data=generate_transaction_template(),
            file_name="transaction_template.csv",
            mime="text/csv"
        )
        
        with st.form("bulk_upload_form"):
            uploaded_file = st.file_uploader("Upload Transactions CSV", type=['csv'])
            account_name = st.selectbox("Account Name", options=account_options)
            
            if st.form_submit_button("Upload Transactions"):
                if uploaded_file is not None:
                    try:
                        df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
                        
                        required_columns = ['transaction_date', 'value_date', 'narration', 'ref_number',
                                           'debit_amount', 'credit_amount', 'tax_percentage', 'tax_amount']
                        
                        # Check if all required columns are present
                        missing_columns = [col for col in required_columns if col not in df.columns]
                        if missing_columns:
                            st.error(f"CSV is missing required columns: {', '.join(missing_columns)}")
                        else:
                            # Validate data
                            for index, row in df.iterrows():
                                if not validate_date(row['transaction_date']) or not validate_date(row['value_date']):
                                    st.error(f"Invalid date format in row {index + 2} with ref_number {row['ref_number']}. Use YYYY-MM-DD.")
                                    return
                                
                                if row['debit_amount'] < 0 or row['credit_amount'] < 0:
                                    st.error(f"Negative amounts not allowed in row {index + 2} with ref_number {row['ref_number']}.")
                                    return
                                
                                if row['debit_amount'] > 0 and row['credit_amount'] > 0:
                                    st.error(f"Cannot have both debit and credit amounts in row {index + 2} with ref_number {row['ref_number']}.")
                                    return
                                
                                if row['tax_percentage'] < 0 or row['tax_percentage'] > 100:
                                    st.error(f"Invalid tax percentage in row {index + 2} with ref_number {row['ref_number']}.")
                                    return
                                
                                # Ensure all required CSV values are not NaN
                                for col in required_columns:
                                    if pd.isna(row[col]):
                                        st.error(f"Missing or invalid value for {col} in row {index + 2} with ref_number {row['ref_number']}.")
                                        return
                            
                            # Check main account balance
                            c.execute("SELECT balance FROM main_account LIMIT 1")
                            main_balance = c.fetchone()[0] or 0.0
                            
                            total_debit = sum(row['debit_amount'] + row['tax_amount'] for _, row in df.iterrows() if row['debit_amount'] > 0)
                            total_credit = sum(row['credit_amount'] - row['tax_amount'] for _, row in df.iterrows() if row['credit_amount'] > 0)
                            net_balance_change = total_credit - total_debit
                            
                            if main_balance + net_balance_change < 0:
                                st.error(f"Insufficient Main Account balance for debit transactions (${total_debit:,.2f} required).")
                            else:
                                try:
                                    with conn:
                                        statement_id = str(uuid.uuid4())[:8]
                                        
                                        c.execute("""
                                        INSERT INTO statements (
                                            id, filename, upload_date, created_by, created_at
                                        ) VALUES (?, ?, ?, ?, ?)
                                        """, (
                                            statement_id, uploaded_file.name, datetime.datetime.now().isoformat(),
                                            st.session_state.role, datetime.datetime.now().isoformat()
                                        ))
                                        
                                        for index, row in df.iterrows():
                                            transaction_id = str(uuid.uuid4())[:8]
                                            transaction_type = "Debit" if row['debit_amount'] > 0 else "Credit"
                                            debit_type = "Other" if transaction_type == "Debit" else None
                                            credit_type = "Other" if transaction_type == "Credit" else None
                                            
                                            allocation_amount = row['debit_amount'] if transaction_type == "Debit" else row['credit_amount'] - row['tax_amount']
                                            
                                            # Validate values, allowing None for credit_type (Debit) or debit_type (Credit)
                                            values = (
                                                transaction_id, row['ref_number'], row['transaction_date'],
                                                row['value_date'], row['narration'], row['debit_amount'],
                                                row['credit_amount'], row['tax_percentage'], row['tax_amount'],
                                                transaction_type, debit_type, credit_type, st.session_state.role,
                                                datetime.datetime.now().isoformat(), account_name, statement_id
                                            )
                                            # Check for None in critical columns only
                                            critical_columns = ['id', 'ref_number', 'transaction_date', 'created_by', 'created_at', 'account_name', 'statement_id']
                                            for i, col in enumerate(['id', 'ref_number', 'transaction_date', 'value_date', 'narration', 
                                                                    'debit_amount', 'credit_amount', 'tax_percentage', 'tax_amount', 
                                                                    'type', 'debit_type', 'credit_type', 'created_by', 'created_at', 
                                                                    'account_name', 'statement_id']):
                                                if col in critical_columns and values[i] is None:
                                                    st.error(f"Missing critical value for {col} in row {index + 2} with ref_number {row['ref_number']}: {values}")
                                                    return
                                            # Allow debit_type to be None for Credit transactions, and credit_type to be None for Debit transactions
                                            if transaction_type == "Debit" and values[11] is not None:  # credit_type
                                                st.error(f"Credit type must be None for Debit transaction in row {index + 2} with ref_number {row['ref_number']}: {values}")
                                                return
                                            if transaction_type == "Credit" and values[10] is not None:  # debit_type
                                                st.error(f"Debit type must be None for Credit transaction in row {index + 2} with ref_number {row['ref_number']}: {values}")
                                                return
                                            
                                            c.execute("""
                                            INSERT INTO transactions (
                                                id, ref_number, transaction_date, value_date, narration,
                                                debit_amount, credit_amount, tax_percentage, tax_amount,
                                                type, debit_type, credit_type, created_by, created_at,
                                                account_name, statement_id
                                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                            """, values)
                                            
                                            # Insert allocation with department_id NULL
                                            allocation_id = str(uuid.uuid4())[:8]
                                            c.execute("""
                                            INSERT INTO allocations (
                                                id, treasury_ref, department_id, amount, created_by, created_at, transaction_type, statement_id
                                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                            """, (
                                                allocation_id, row['ref_number'], None, allocation_amount,
                                                st.session_state.role, datetime.datetime.now().isoformat(), transaction_type, statement_id
                                            ))
                                            
                                            # Update main account balance
                                            if transaction_type == "Debit":
                                                c.execute("UPDATE main_account SET balance = balance - ?",
                                                         (row['debit_amount'] + row['tax_amount'],))
                                            else:
                                                c.execute("UPDATE main_account SET balance = balance + ?",
                                                         (row['credit_amount'] - row['tax_amount'],))
                                        
                                        c.execute("SELECT balance FROM main_account LIMIT 1")
                                        new_main_balance = c.fetchone()[0]
                                        
                                        st.success(f"Transactions uploaded successfully! Statement ID: {statement_id}")
                                        st.info(f"Transactions are pending allocation in the Allocations section. Updated Main Account Balance: ${new_main_balance:,.2f}")
                                        
                                        # Display uploaded transactions
                                        st.markdown('<div class="section-header">Uploaded Transactions</div>', unsafe_allow_html=True)
                                        st.dataframe(df)
                                
                                except Exception as e:
                                    st.error(f"Error processing transactions: {str(e)}")
                                    conn.rollback()
                    except Exception as e:
                        st.error(f"Error reading CSV: {str(e)}")
                else:
                    st.error("Please upload a CSV file.")
    
    elif selected == "Statements":
        st.markdown('<div class="section-header">Statement Management</div>', unsafe_allow_html=True)
        
        if st.session_state.role == "admin":
            st.markdown('<div class="section-header">Download Statements</div>', unsafe_allow_html=True)
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
            
            if st.button("Generate Statement"):
                if start_date <= end_date:
                    csv_data = generate_statement_csv(start_date, end_date)
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"statement_{start_date}_to_{end_date}.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("Start date must be before or equal to end date.")
            
            st.markdown('<div class="section-header">Uploaded Statements</div>', unsafe_allow_html=True)
            df = pd.read_sql("SELECT id, filename, upload_date FROM statements ORDER BY upload_date DESC", conn)
            
            if not df.empty:
                st.dataframe(df)
            else:
                st.info("No statements uploaded.")
    
    elif selected == "Allocations" and st.session_state.role == "admin":
        st.markdown('<div class="section-header">Allocation Management</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">Pending Allocations</div>', unsafe_allow_html=True)
        pending_allocations = pd.read_sql("""
        SELECT a.id, a.treasury_ref, a.amount, a.transaction_type, t.debit_type
        FROM allocations a
        JOIN transactions t ON a.treasury_ref = t.ref_number
        WHERE a.department_id IS NULL
        AND (a.transaction_type = 'Credit' OR 
             (a.transaction_type = 'Debit' AND t.debit_type != 'Investment'))
        AND t.credit_type != 'Credit Investments'
        ORDER BY a.created_at DESC
        """, conn)
        
        if not pending_allocations.empty:
            st.markdown('<div class="section-header">Pending Allocations Table</div>', unsafe_allow_html=True)
            pending_df = pd.read_sql("""
            SELECT a.treasury_ref, a.amount, a.transaction_type, t.transaction_date,
                   t.narration, t.account_name, t.tax_percentage, t.tax_amount
            FROM allocations a
            JOIN transactions t ON a.treasury_ref = t.ref_number
            WHERE a.department_id IS NULL
            AND (a.transaction_type = 'Credit' OR 
                 (a.transaction_type = 'Debit' AND t.debit_type != 'Investment'))
            AND t.credit_type != 'Credit Investments'
            ORDER BY t.transaction_date DESC
            """, conn)
            st.dataframe(pending_df)
            
            with st.form("allocate_pending", clear_on_submit=True):
                selected_ref = st.selectbox("Select Ref Number", pending_allocations['treasury_ref'])
                alloc_record = pending_allocations[pending_allocations['treasury_ref'] == selected_ref].iloc[0]
                alloc_id = alloc_record['id']
                amount = float(alloc_record['amount'])
                transaction_type = alloc_record['transaction_type']
                
                st.markdown(f"**Amount to Allocate: ${amount:,.2f} ({transaction_type})**", unsafe_allow_html=True)
                
                departments = pd.read_sql("SELECT id, name FROM departments", conn)
                allocations = {}
                
                for _, dept in departments.iterrows():
                    allocations[dept['id']] = st.number_input(
                        f"Allocation for {dept['name']}",
                        min_value=0.0,
                        max_value=float(amount),
                        value=0.0,
                        step=0.01
                    )
                
                submit_button = st.form_submit_button("Allocate", use_container_width=True)
                
                if submit_button:
                    total_allocated = sum(allocations.values())
                    
                    if abs(total_allocated - amount) > 0.01:
                        st.error(f"Total amount allocated (${total_allocated:,.2f}) must equal the transaction amount (${amount:,.2f})")
                    else:
                        try:
                            with conn:
                                # Process each department allocation
                                for dept_id, alloc_amount in allocations.items():
                                    if alloc_amount > 0:
                                        if transaction_type == "Debit":
                                            c.execute("SELECT balance FROM departments WHERE id = ?", (dept_id,))
                                            dept_balance = c.fetchone()[0] or 0.0
                                            
                                            if dept_balance < alloc_amount:
                                                c.execute("SELECT name FROM departments WHERE id = ?", (dept_id,))
                                                dept_name = c.fetchone()[0]
                                                st.error(f"Insufficient balance in {dept_name} for debit allocation of ${alloc_amount:,.2f}.")
                                                conn.rollback()
                                                st.stop()
                                        
                                        new_alloc_id = str(uuid.uuid4())[:8]
                                        c.execute("""
                                        INSERT INTO allocations (
                                            id, treasury_ref, department_id, amount,
                                            created_by, created_at, transaction_type
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                                        """, (
                                            new_alloc_id, selected_ref, dept_id,
                                            alloc_amount, st.session_state.role,
                                            datetime.datetime.now().isoformat(), transaction_type
                                        ))
                                        
                                        if transaction_type == "Credit":
                                            c.execute("UPDATE departments SET balance = balance + ? WHERE id = ?",
                                                     (alloc_amount, dept_id))
                                        elif transaction_type == "Debit":
                                            c.execute("UPDATE departments SET balance = balance - ? WHERE id = ?",
                                                     (alloc_amount, dept_id))
                                
                                # Remove the original unallocated record
                                c.execute("DELETE FROM allocations WHERE id = ?", (alloc_id,))
                                conn.commit()
                                st.success("Allocation completed successfully!")
                                st.session_state.allocated = True  # Set a flag
                        
                        except Exception as e:
                            st.error(f"Error processing allocation: {str(e)}")
                            conn.rollback()
                
                # This will force a rerun if allocation was successful
                if st.session_state.get('allocated', False):
                    st.session_state.allocated = False
                    st.rerun()
        else:
            st.info("No pending allocations found")
        
        st.markdown('<div class="section-header">Recent Allocations</div>', unsafe_allow_html=True)
        df = pd.read_sql("""
        SELECT a.treasury_ref, a.department_id, a.amount, a.transaction_type,
               a.created_at, d.name AS department_name
        FROM allocations a
        LEFT JOIN departments d ON a.department_id = d.id
        WHERE a.created_at >= date('now', '-30 days') AND a.department_id IS NOT NULL
        ORDER BY a.created_at DESC
        """, conn)
        
        if not df.empty:
            st.markdown('<div class="card">Recent Allocations</div>', unsafe_allow_html=True)
            st.dataframe(df)
        else:
            st.info("No recent allocations found")
        
        st.markdown('<div class="section-header">Your Department Allocations</div>', unsafe_allow_html=True)
        dept_allocations = pd.read_sql("""
        SELECT a.treasury_ref, a.amount, a.transaction_type, t.transaction_date,
               t.narration, t.account_name, t.tax_percentage, t.tax_amount
        FROM allocations a
        JOIN transactions t ON a.treasury_ref = t.ref_number
        WHERE a.department_id = ?
        ORDER BY t.transaction_date DESC
        """, conn, params=(st.session_state.department_id,))
        
        if not dept_allocations.empty:
            st.dataframe(dept_allocations)
        else:
            st.warning("No allocations found for your department.")
    
    elif selected == "Investments" and st.session_state.role == "admin":
        st.markdown('<div class="section-header">Investment Management</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">Pending Investment Allocations</div>', unsafe_allow_html=True)
        pending_investment_allocations = pd.read_sql("""
        SELECT a.id, a.treasury_ref, a.amount, a.transaction_type, t.debit_type, t.credit_type,
               t.transaction_date, t.narration, t.account_name, t.tax_percentage, t.tax_amount
        FROM allocations a
        JOIN transactions t ON a.treasury_ref = t.ref_number
        JOIN investments i ON a.treasury_ref = i.ref_number
        WHERE a.department_id IS NULL
        AND (t.debit_type = 'Investment' OR t.credit_type = 'Credit Investments')
        ORDER BY t.transaction_date DESC
        """, conn)
        
        if not pending_investment_allocations.empty:
            st.dataframe(pending_investment_allocations)
            
            with st.form("allocate_investment"):
                selected_ref = st.selectbox("Select Investment Allocation", pending_investment_allocations['treasury_ref'])
                
                alloc_id = pending_investment_allocations[
                    pending_investment_allocations['treasury_ref'] == selected_ref
                ]['id'].iloc[0]
                
                amount = pending_investment_allocations[
                    pending_investment_allocations['treasury_ref'] == selected_ref
                ]['amount'].iloc[0]
                
                transaction_type = pending_investment_allocations[
                    pending_investment_allocations['treasury_ref'] == selected_ref
                ]['transaction_type'].iloc[0]
                
                st.markdown(f"**Amount to Allocate: ${amount:,.2f} ({transaction_type})**", unsafe_allow_html=True)
                
                departments = pd.read_sql("SELECT id, name FROM departments", conn)
                allocations = {}
                
                for _, dept in departments.iterrows():
                    allocations[dept['id']] = st.number_input(f"Allocation for {dept['name']}", min_value=0.0, value=0.0)
                
                if st.form_submit_button("Allocate Investment"):
                    total_allocated = sum(allocations.values())
                    
                    if total_allocated != amount:
                        st.error("Total allocated amount must equal the transaction amount.")
                    else:
                        if transaction_type == "Debit":
                            for dept_id, alloc_amount in allocations.items():
                                if alloc_amount > 0:
                                    c.execute("SELECT balance FROM departments WHERE id = ?", (dept_id,))
                                    dept_balance = c.fetchone()[0] or 0.0
                                    
                                    if dept_balance < alloc_amount:
                                        c.execute("SELECT name FROM departments WHERE id = ?", (dept_id,))
                                        dept_name = c.fetchone()[0]
                                        st.error(f"Insufficient balance in {dept_name} for debit allocation of ${alloc_amount:,.2f}.")
                                        return
                        
                        try:
                            with conn:
                                representative_dept_id = None
                                
                                for dept_id, alloc_amount in allocations.items():
                                    if alloc_amount > 0:
                                        if not representative_dept_id:
                                            representative_dept_id = dept_id
                                        
                                        c.execute("""
                                        INSERT INTO allocations (
                                            id, treasury_ref, department_id, amount, created_by, created_at, transaction_type
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                                        """, (
                                            str(uuid.uuid4())[:8], selected_ref, dept_id,
                                            alloc_amount, st.session_state.role,
                                            datetime.datetime.now().isoformat(), transaction_type
                                        ))
                                        
                                        if transaction_type == "Credit":
                                            c.execute("UPDATE departments SET balance = balance + ? WHERE id = ?", (alloc_amount, dept_id))
                                        elif transaction_type == "Debit":
                                            c.execute("UPDATE departments SET balance = balance - ? WHERE id = ?", (alloc_amount, dept_id))
                                
                                if representative_dept_id:
                                    c.execute("UPDATE investments SET department_id = ? WHERE ref_number = ?",
                                             (representative_dept_id, selected_ref))
                                
                                c.execute("DELETE FROM allocations WHERE id = ?", (alloc_id,))
                                st.success("Investment allocation completed successfully!")
                                
                                c.execute("SELECT balance FROM main_account LIMIT 1")
                                new_main_balance = c.fetchone()[0]
                                
                                dept_balances = []
                                for dept_id in allocations:
                                    if allocations[dept_id] > 0:
                                        c.execute("SELECT name, balance FROM departments WHERE id = ?", (dept_id,))
                                        dept_result = c.fetchone()
                                        dept_balances.append(f"{dept_result[0]}: ${dept_result[1]:,.2f}")
                                
                                st.info(f"Updated Balances:\n- Main Account: ${new_main_balance:,.2f}\n- " + "\n- ".join(dept_balances))
                        
                        except Exception as e:
                            st.error(f"Error processing allocation: {str(e)}")
                            conn.rollback()
        else:
            st.info("No pending investment allocations.")
        
        st.markdown('<div class="section-header">Confirm Investments</div>', unsafe_allow_html=True)
        pending_investments = pd.read_sql("""
        SELECT i.ref_number, i.amount, i.created_at, t.narration, t.transaction_date, i.department_id
        FROM investments i
        JOIN transactions t ON i.ref_number = t.ref_number
        WHERE i.status = 'pending' AND i.department_id IS NOT NULL
        ORDER BY i.created_at DESC
        """, conn)
        
        deal_note_data = None
        
        if not pending_investments.empty:
            st.dataframe(pending_investments)
            
            with st.form("confirm_investment"):
                selected_ref = st.selectbox("Select Investment", pending_investments['ref_number'])
                
                if not pending_investments[pending_investments['ref_number'] == selected_ref].empty:
                    amount = pending_investments.loc[pending_investments['ref_number'] == selected_ref]['amount'].iloc[0]
                    value_date = pending_investments.loc[pending_investments['ref_number'] == selected_ref]['transaction_date'].iloc[0]
                    default_narration = pending_investments.loc[pending_investments['ref_number'] == selected_ref]['narration'].iloc[0]
                    
                    account_name = st.selectbox("Account Name", options=account_options)
                    nominal_value = st.number_input("Nominal Value ($)", min_value=0.0, value=float(amount), disabled=True)
                    period = st.number_input("Tenure (days)", min_value=1, value=30)
                    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=0.0)
                    
                    interest = (amount * interest_rate * period) / (100 * 365)
                    withholding_tax = interest * 0.2
                    st.markdown(f"**Withholding Tax (20% of Interest):** ${withholding_tax:,.2f}")
                    
                    if st.form_submit_button("Confirm Investment"):
                        maturity_date = datetime.datetime.strptime(value_date, '%Y-%m-%d') + timedelta(days=period)
                        maturity_value = amount + interest
                        net_interest = interest - withholding_tax
                        tax_maturity_value = amount + net_interest
                        after_tax_yield = (net_interest / amount) * (365 / period) * 100 if period > 0 and amount > 0 else 0.0
                        profit_loss = tax_maturity_value - amount
                        
                        try:
                            with conn:
                                c.execute("""
                                UPDATE investments
                                SET account_name = ?, period = ?, value_date = ?,
                                    interest_rate = ?, maturity_date = ?, interest = ?,
                                    withholding_tax = ?, maturity_amount = ?, status = 'confirmed'
                                WHERE ref_number = ?
                                """, (
                                    account_name, period, value_date,
                                    interest_rate, maturity_date.isoformat(), interest,
                                    withholding_tax, tax_maturity_value, selected_ref
                                ))
                                
                                st.success("Investment confirmed successfully!")
                                
                                # Store deal note data for download button outside the form
                                deal_note_data = f"""
                                Deal Note
                                
                                Reference Number: {selected_ref}
                                Account Name: {account_name}
                                Nominal Value: ${amount:,.2f}
                                Tenure: {period} days
                                Value Date: {value_date}
                                Interest Rate: {interest_rate:.2f}%
                                Maturity Date: {maturity_date}
                                Interest: ${interest:,.2f}
                                Withholding Tax: ${withholding_tax:,.2f}
                                Maturity Value: ${maturity_value:,.2f}
                                Net Interest: ${net_interest:,.2f}
                                Tax Maturity Value: ${tax_maturity_value:,.2f}
                                After-Tax Yield: {after_tax_yield:.2f}%
                                Profit/Loss: ${profit_loss:,.2f}
                                """
                        except Exception as e:
                            st.error(f"Error confirming investment: {str(e)}")
                            conn.rollback()
                else:
                    st.error("Selected reference number not found.")
            
            # Download button moved outside the form
            if deal_note_data:
                st.download_button(
                    label="Download Deal Note",
                    data=deal_note_data,
                    file_name=f"deal_note_{selected_ref}.txt",
                    mime="text/plain"
                )
        else:
            st.info("No pending investments to confirm.")
        
        st.markdown('<div class="section-header">Pending Investments</div>', unsafe_allow_html=True)
        pending_unallocated = pd.read_sql("""
        SELECT i.ref_number, i.amount, i.created_at, t.narration, t.transaction_date
        FROM investments i
        JOIN transactions t ON i.ref_number = t.ref_number
        WHERE i.status = 'pending' AND i.department_id IS NULL
        ORDER BY i.created_at DESC
        """, conn)
        
        if not pending_unallocated.empty:
            st.dataframe(pending_unallocated)
        else:
            st.info("No unallocated pending investments found.")
        
        st.markdown('<div class="section-header">Active Investments</div>', unsafe_allow_html=True)
        active_investments = pd.read_sql("""
        SELECT i.ref_number, d.name AS department_name, i.account_name, i.period,
               i.value_date, i.maturity_date, i.amount AS amount_invested,
               (i.amount + i.interest) AS maturity_value, i.withholding_tax,
               (i.interest - i.withholding_tax) AS net_interest, i.maturity_amount AS tax_maturity_value,
               ((i.interest - i.withholding_tax) / i.amount * 365 / i.period * 100) AS after_tax_yield,
               (i.maturity_amount - i.amount) AS profit_loss
        FROM investments i
        JOIN departments d ON i.department_id = d.id
        WHERE i.status = 'confirmed' AND i.maturity_date >= ?
        ORDER BY i.value_date DESC
        """, conn, params=(datetime.datetime.now().isoformat(),))
        
        if not active_investments.empty:
            st.dataframe(active_investments)
            
            csv_data = active_investments.to_csv(index=False)
            st.download_button(
                label="Download Active Investments",
                data=csv_data,
                file_name="active_investments.csv",
                mime="text/csv"
            )
        else:
            st.info("No active investments.")
    
    elif selected == "Investments" and st.session_state.role != "admin":
        st.markdown('<div class="section-header">Investments</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">Add Investments</div>', unsafe_allow_html=True)
        with st.form("dept_investment_form"):
            account_name = st.selectbox("Account Name", options=account_options)
            currency = st.selectbox("Currency", ["USD", "EUR", "GBP"])
            period = st.number_input("Period (days)", min_value=1, value=30)
            value_date = st.date_input("Value Date")
            interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=0.0)
            amount = st.number_input("Investment Amount ($)", min_value=0.0, value=0.0)
            tax_percentage = st.number_input("Tax Percentage (%)", min_value=0.0, max_value=100.0, value=0.0)
            
            tax_amount = amount * (tax_percentage / 100)
            if tax_percentage > 0:
                st.markdown(f"**Tax Amount:** ${tax_amount:,.2f}")
                st.markdown(f"**Net Amount:** ${amount:,.2f}")
            
            if st.form_submit_button("Submit"):
                c = conn.cursor()
                c.execute("SELECT balance FROM main_account LIMIT 1")
                main_balance = c.fetchone()[0] or 0.0
                
                c.execute("SELECT balance FROM departments WHERE id = ?", (st.session_state.department_id,))
                dept_balance = c.fetchone()[0] or 0.0
                
                total_amount = amount + tax_amount
                
                if main_balance < total_amount:
                    st.error(f"Insufficient Main Account balance for investment (${total_amount:,.2f} required).")
                elif dept_balance < amount:
                    c.execute("SELECT name FROM departments WHERE id = ?", (st.session_state.department_id,))
                    dept_name = c.fetchone()[0]
                    st.error(f"Insufficient balance in {dept_name} for investment (${amount:,.2f} required).")
                else:
                    ref_number = str(uuid.uuid4())[:8]
                    maturity_date = value_date + timedelta(days=period)
                    interest = (amount * interest_rate * period) / (100 * 365)
                    withholding_tax = interest * 0.2
                    maturity_amount = amount + interest - withholding_tax
                    allocation_id = str(uuid.uuid4())[:8]
                    
                    try:
                        with conn:
                            # Insert investment with user's department_id
                            c.execute("""
                            INSERT INTO investments (
                                ref_number, transaction_ref, account_name, currency, period,
                                amount, value_date, interest_rate, maturity_date, interest,
                                withholding_tax, maturity_amount, created_by, created_at,
                                status, allocation_id, department_id
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                ref_number, ref_number, account_name, currency, period,
                                amount, value_date.isoformat(), interest_rate, maturity_date.isoformat(),
                                interest, withholding_tax, maturity_amount,
                                st.session_state.role, datetime.datetime.now().isoformat(),
                                'pending', allocation_id, st.session_state.department_id
                            ))
                            
                            # Insert allocation with department_id NULL for pending allocation
                            c.execute("""
                            INSERT INTO allocations (
                                id, treasury_ref, amount, created_by, created_at, transaction_type
                            ) VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                allocation_id, ref_number, amount, st.session_state.role,
                                datetime.datetime.now().isoformat(), 'Debit'
                            ))
                            
                            # Deduct from main account and department
                            c.execute("UPDATE main_account SET balance = balance - ?", (total_amount,))
                            c.execute("UPDATE departments SET balance = balance - ? WHERE id = ?",
                                     (amount, st.session_state.department_id))
                            
                            # Insert transaction for audit trail
                            transaction_id = str(uuid.uuid4())[:8]
                            c.execute("""
                            INSERT INTO transactions (
                                id, ref_number, transaction_date, value_date, narration,
                                debit_amount, credit_amount, tax_percentage, tax_amount,
                                type, debit_type, created_by, created_at, account_name
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                transaction_id, ref_number, value_date.isoformat(), value_date.isoformat(),
                                f"Investment: {account_name}", amount, 0.0, tax_percentage, tax_amount,
                                'Debit', 'Investment', st.session_state.role,
                                datetime.datetime.now().isoformat(), account_name
                            ))
                            
                            st.success("Investment submitted successfully! Awaiting allocation by admin.")
                            
                            deal_note = f"""
                            Deal Note
                            
                            Account Name: {account_name}
                            Reference Number: {ref_number}
                            Date of Investment: {value_date}
                            Currency: {currency}
                            Period: {period} days
                            Value Date: {value_date}
                            Interest Rate: {interest_rate:.2f}%
                            Maturity Date: {maturity_date}
                            Investment Amount: ${amount:,.2f}
                            Tax Percentage: ${tax_percentage:.2f}
                            Tax Amount: ${tax_amount:,.2f}
                            Interest: ${interest:,.2f}
                            Withholding Tax: ${withholding_tax:,.2f}
                            Maturity Amount: ${maturity_amount:,.2f}
                            """
                            
                            st.download_button(
                                label="Download Deal Note",
                                data=deal_note,
                                file_name=f"deal_note_{ref_number}.txt",
                                mime="text/plain"
                            )
                    except Exception as e:
                        st.error(f"Error processing investment: {str(e)}")
                        conn.rollback()
        
        st.markdown('<div class="section-header">View Active Investments</div>', unsafe_allow_html=True)
        if st.button("View Active Investments"):
            c.execute("""
            SELECT ref_number, account_name, currency, amount, value_date, period, maturity_date
            FROM investments
            WHERE department_id = ? AND status = 'confirmed' AND maturity_date >= ?
            ORDER BY value_date DESC
            """, (st.session_state.department_id, datetime.datetime.now().isoformat()))
            
            investments = c.fetchall()
            if investments:
                df = pd.DataFrame(investments,
                                columns=['Ref', 'Account', 'Currency', 'Amount', 'Value Date', 'Period', 'Maturity'])
                st.markdown(f'<div class="card">Total: {len(investments)}</div>', unsafe_allow_html=True)
                st.dataframe(df)
            else:
                st.info("No active investments.")
        
        st.markdown('<div class="section-header">Investment History</div>', unsafe_allow_html=True)
        c.execute("""
        SELECT ref_number, account_name, currency, amount, period, value_date, maturity_date
        FROM investments
        WHERE department_id = ? AND status = 'confirmed'
        ORDER BY value_date DESC
        """, (st.session_state.department_id,))
        
        history = c.fetchall()
        if history:
            df = pd.DataFrame(history,
                            columns=['Ref', 'Account', 'Currency', 'Amount', 'Period', 'Value Date', 'Maturity'])
            st.dataframe(df)
        else:
            st.info("No investment history.")
    
    elif selected == "Reconciliation" and st.session_state.role == "admin":
        st.markdown('<div class="section-header">Reconciliation</div>', unsafe_allow_html=True)
        
        with st.form("reconciliation_form"):
            accounts = ['Main Account']
            departments = pd.read_sql("SELECT name FROM departments", conn)
            accounts.extend(dept for dept in departments['name'])
            selected_account = st.selectbox("Select Account", accounts)
            
            statements = pd.read_sql("SELECT id, filename, upload_date FROM statements ORDER BY upload_date DESC", conn)
            statement_id = None
            
            if not statements.empty:
                statement_options = statements.apply(lambda x: f"{x['filename']} (Uploaded: {x['upload_date']})", axis=1)
                selected_statement = st.selectbox("Select Statement", statement_options)
                statement_id = statements.iloc[statement_options[statement_options == selected_statement].index[0]]['id']
            
            if st.form_submit_button("Reconcile"):
                if statement_id:
                    transactions = pd.read_sql("""
                    SELECT ref_number, transaction_date, narration, debit_amount, credit_amount,
                           tax_percentage, tax_amount, account_name
                    FROM transactions
                    WHERE statement_id = ? AND account_name = ?
                    ORDER BY transaction_date DESC
                    """, conn, params=(statement_id, selected_account if selected_account != 'Main Account' else account_options[0]))
                    
                    if not transactions.empty:
                        tax_rates = pd.read_sql("SELECT description, rate FROM taxes_tariffs", conn)
                        discrepancies = []
                        
                        for _, trans in transactions.iterrows():
                            amount = trans['debit_amount'] if trans['debit_amount'] > 0 else trans['credit_amount']
                            expected_tax = 0.0
                            tax_applied = "Transaction Tax"
                            
                            # Check tax based on tax_percentage
                            if trans['tax_percentage'] > 0:
                                expected_tax = amount * (trans['tax_percentage'] / 100)
                            
                            # Override with taxes_tariffs if narration matches
                            for _, tax in tax_rates.iterrows():
                                if tax['description'].lower() in trans['narration'].lower():
                                    expected_tax = amount * (tax['rate'] / 100)
                                    tax_applied = tax['description']
                                    break
                            
                            tax_diff = trans['tax_amount'] - expected_tax
                            
                            # Additional validations
                            is_invalid = False
                            error_reason = []
                            
                            if abs(tax_diff) > 0.01:
                                error_reason.append("Tax mismatch")
                            
                            if trans['debit_amount'] > 0 and trans['credit_amount'] > 0:
                                error_reason.append("Both debit and credit amounts")
                                is_invalid = True
                            
                            if trans['debit_amount'] == 0 and trans['credit_amount'] == 0:
                                error_reason.append("No debit or credit amount")
                                is_invalid = True
                            
                            if not trans['narration'].strip():
                                error_reason.append("Empty narration")
                                is_invalid = True
                            
                            if is_invalid or abs(tax_diff) > 0.01:
                                discrepancies.append({
                                    'ref': trans['ref_number'],
                                    'date': trans['transaction_date'],
                                    'narration': trans['narration'],
                                    'debit': trans['debit_amount'],
                                    'credit': trans['credit_amount'],
                                    'actual_tax': trans['tax_amount'],
                                    'expected_tax': expected_tax,
                                    'tax_diff': tax_diff,
                                    'tax_applied': tax_applied,
                                    'error_reason': '; '.join(error_reason)
                                })
                        
                        if discrepancies:
                            df = pd.DataFrame(discrepancies)
                            st.warning(f"Found {len(discrepancies)} discrepancies for {selected_account}")
                            st.dataframe(df)
                            
                            csv_data = df.to_csv(index=False)
                            st.download_button(
                                label="Download Discrepancy Report",
                                data=csv_data,
                                file_name=f"reconciliation_discrepancies_{statement_id}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.success(f"No discrepancies found for {selected_account} in the selected statement.")
                    else:
                        st.warning("No transactions found for the selected statement and account.")
                else:
                    st.error("No statements available for reconciliation.")
    
    elif selected == "Tariff & Tax" and st.session_state.role == "admin":
        st.markdown('<div class="section-header">Tariff Management</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">Bank Tariffs</div>', unsafe_allow_html=True)
        with st.expander("Upload Tariff Guide"):
            with st.form("tariff_form"):
                bank_name = st.text_input("Bank Name")
                uploaded_file = st.file_uploader("Upload (PDF)", type=['pdf'])
                
                if st.form_submit_button("Upload"):
                    if bank_name and uploaded_file:
                        try:
                            file_data = uploaded_file.read()
                            c.execute("""
                            INSERT INTO bank_tariff_guides (
                                bank_name, document_name, document_data, upload_date, created_by, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                bank_name, uploaded_file.name, file_data,
                                datetime.datetime.now().isoformat(), st.session_state.role,
                                datetime.datetime.now().isoformat()
                            ))
                            conn.commit()
                            st.success("Tariff uploaded!")
                        except Exception as e:
                            st.error(f"Error uploading: {str(e)}")
                    else:
                        st.warning("Provide bank name and file.")
        
        st.markdown('<div class="section-header">Available Tariffs</div>', unsafe_allow_html=True)
        tariffs = pd.read_sql("""
        SELECT id, bank_name, document_name, upload_date
        FROM bank_tariff_guides
        ORDER BY upload_date DESC
        """, conn)
        
        if not tariffs.empty:
            for _, row in tariffs.iterrows():
                with st.container():
                    col1, col2 = st.columns([3,1])
                    with col1:
                        st.markdown(f"**{row['bank_name']}** - {row['document_name']} ({row['upload_date']})")
                    with col2:
                        doc_data = c.execute("SELECT document_data FROM bank_tariff_guides WHERE id = ?", (row['id'],)).fetchone()[0]
                        st.download_button(
                            label="Download",
                            data=doc_data,
                            file_name=row['document_name'],
                            mime="application/pdf"
                        )
        else:
            st.info("No tariffs available.")
        
        st.markdown('<div class="section-header">Manage Taxes</div>', unsafe_allow_html=True)
        with st.form("tax_form"):
            desc = st.text_input("Description")
            rate = st.number_input("Rate (%)", min_value=0.0, max_value=100.0)
            
            if st.form_submit_button("Add"):
                if not desc.strip():
                    st.error("Description required.")
                else:
                    try:
                        c.execute("""
                        INSERT INTO taxes_tariffs (
                            description, rate, created_by, created_at
                        ) VALUES (?, ?, ?, ?)
                        """, (
                            desc, rate, st.session_state.role, datetime.datetime.now().isoformat()
                        ))
                        conn.commit()
                        st.success("Tax added!")
                    except Exception as e:
                        st.error(f"Error adding: {str(e)}")
        
        st.markdown('<div class="section-header">Current Taxes</div>', unsafe_allow_html=True)
        taxes = pd.read_sql("""
        SELECT description, rate, created_at
        FROM taxes_tariffs
        ORDER BY created_at DESC
        """, conn)
        
        if not taxes.empty:
            st.dataframe(taxes)
        else:
            st.info("No taxes defined.")
        
        st.markdown('<div class="section-header">Verify Taxes</div>', unsafe_allow_html=True)
        statements = pd.read_sql("""
        SELECT id, filename, upload_date
        FROM statements
        ORDER BY upload_date DESC
        LIMIT 1
        """, conn)
        
        if not statements.empty:
            statement_id = statements['id'].iloc[0]
            filename = statements['filename'].iloc[0]
            upload_date = statements['upload_date'].iloc[0]
            
            st.markdown(f"**Verifying Latest Statement: {filename} (Uploaded: {upload_date})**", unsafe_allow_html=True)
            
            transactions = pd.read_sql("""
            SELECT ref_number, transaction_date, narration,
                   debit_amount, credit_amount, tax_percentage, tax_amount
            FROM transactions
            WHERE statement_id = ?
            ORDER BY transaction_date DESC
            """, conn, params=(statement_id,))
            
            if not transactions.empty:
                tax_rates = pd.read_sql("SELECT description, rate FROM taxes_tariffs", conn)
                
                transactions['expected_tax'] = 0.0
                transactions['tax_diff'] = 0.0
                transactions['tax_applied'] = ""
                
                for idx, row in transactions.iterrows():
                    amount = row['debit_amount'] if row['debit_amount'] > 0 else row['credit_amount']
                    matched = False
                    
                    for _, tax in tax_rates.iterrows():
                        if tax['description'].lower() in row['narration'].lower():
                            expected_tax = amount * (tax['rate'] / 100)
                            transactions.at[idx, 'expected_tax'] = expected_tax
                            transactions.at[idx, 'tax_diff'] = row['tax_amount'] - expected_tax
                            transactions.at[idx, 'tax_applied'] = tax['description']
                            matched = True
                            break
                    
                    if not matched and row['tax_percentage'] > 0:
                        expected_tax = amount * (row['tax_percentage'] / 100)
                        transactions.at[idx, 'expected_tax'] = expected_tax
                        transactions.at[idx, 'tax_diff'] = row['tax_amount'] - expected_tax
                        transactions.at[idx, 'tax_applied'] = "Transaction Tax"
                
                tolerance = 0.01
                discrepancies = transactions[abs(transactions['tax_diff']) > tolerance]
                
                if not discrepancies.empty:
                    st.warning(f"Found {len(discrepancies)} tax discrepancies in '{filename}'")
                    st.dataframe(discrepancies[[
                        'ref_number', 'transaction_date', 'narration',
                        'debit_amount', 'credit_amount', 'tax_amount',
                        'expected_tax', 'tax_diff', 'tax_applied'
                    ]])
                    
                    csv = discrepancies[[
                        'ref_number', 'transaction_date', 'narration',
                        'debit_amount', 'credit_amount', 'tax_amount',
                        'expected_tax', 'tax_diff'
                    ]].to_csv(index=False)
                    
                    st.download_button(
                        label="Download Discrepancy Report",
                        data=csv,
                        file_name=f"tax_discrepancies_{filename.replace(' ', '_')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.success("All taxes in the statement are correct!")
            else:
                st.warning("No transactions found in the statement.")
        else:
            st.info("No statements available.")
    
    elif selected == "User Management" and st.session_state.role == "admin":
        st.markdown('<div class="section-header">User Management</div>', unsafe_allow_html=True)
        
        with st.form("add_dept"):
            dept_name = st.text_input("Department Name")
            
            if st.form_submit_button("Add"):
                if not dept_name.strip():
                    st.error("Name required.")
                else:
                    try:
                        c.execute("""
                        INSERT INTO departments (
                            id, name, balance, created_by, created_at
                        ) VALUES (?, ?, ?, ?, ?)
                        """, (
                            str(uuid.uuid4())[:8], dept_name, '0.0',
                            st.session_state.role, datetime.datetime.now().isoformat()
                        ))
                        conn.commit()
                        st.success("Department added!")
                    except sqlite3.IntegrityError as e:
                        st.error(f"Error: {str(e)}")
        
        with st.form("add_user"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            depts = pd.read_sql("SELECT id, name FROM departments WHERE name IS NOT NULL ORDER BY name", conn)
            dept_id = st.selectbox("Department", depts.set_index('id')['name'])
            
            role = st.selectbox("Role", ["user", "admin"])
            
            if st.form_submit_button("Add"):
                if not username.strip() or not password.strip():
                    st.error("Username and password required.")
                else:
                    try:
                        c.execute("""
                        INSERT INTO users (
                            username, password, role, department_id, created_by, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            username, hashlib.sha256(password.encode('utf-8')).hexdigest(),
                            role, dept_id, st.session_state.role,
                            datetime.datetime.now().isoformat()
                        ))
                        conn.commit()
                        st.success("User added!")
                    except sqlite3.IntegrityError as e:
                        st.error(f"Error: {str(e)}")
    
    conn.close()

if __name__ == "__main__":
    main()