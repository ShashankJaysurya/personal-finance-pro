from pathlib import Path
import sqlite3
from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------
# PERSONAL FINANCE PRO - SAFE SQLITE CONFIGURATION
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "expenses.db"

st.set_page_config(
    page_title="Personal Finance Pro",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Do not silently create a new empty database. This protects
# the user's existing records if the expected DB is missing.
if not DB_PATH.exists():
    st.error(
        f"Existing database not found at: {DB_PATH}\n\n"
        "Stop here. Do not create a new database. Check that "
        "your original data/expenses.db file is in the project folder."
    )
    st.stop()


def get_connection():
    return sqlite3.connect(str(DB_PATH), timeout=10)


def check_database():
    """Validate the existing table without recreating it."""
    with get_connection() as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "expenses" not in tables:
            raise RuntimeError(
                "The existing database does not contain an 'expenses' table. "
                "No tables or records have been changed."
            )

        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(expenses)").fetchall()
        }
        required = {"id", "amount", "category", "description", "date"}
        missing = required - columns
        if missing:
            raise RuntimeError(
                "The expenses table is missing expected columns: "
                + ", ".join(sorted(missing))
            )

        # This is a new supporting table. It does not alter expense records.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount >= 0),
                UNIQUE(month, category)
            )
        """)
        conn.commit()


def load_expenses():
    with get_connection() as conn:
        data = pd.read_sql_query(
            """
            SELECT id, amount, category, description, date
            FROM expenses
            ORDER BY date DESC, id DESC
            """,
            conn,
        )
    if not data.empty:
        data["amount"] = pd.to_numeric(data["amount"], errors="coerce")
        data["date"] = pd.to_datetime(data["date"], errors="coerce")
        data["category"] = data["category"].fillna("Uncategorized").astype(str)
        data["description"] = data["description"].fillna("").astype(str)
        data = data.dropna(subset=["amount", "date"])
    return data


def money(value):
    return f"₹{float(value):,.2f}"


def add_expense(amount, category, description, expense_date):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO expenses (amount, category, description, date)
            VALUES (?, ?, ?, ?)
            """,
            (
                float(amount),
                category.strip(),
                description.strip(),
                expense_date.isoformat(),
            ),
        )
        conn.commit()


def delete_expense(expense_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (int(expense_id),))
        conn.commit()


def update_expense(expense_id, amount, category, description, expense_date):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE expenses
            SET amount = ?, category = ?, description = ?, date = ?
            WHERE id = ?
            """,
            (float(amount), category.strip(), description.strip(), expense_date.isoformat(), int(expense_id)),
        )
        conn.commit()


def load_budgets(month):
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT category, amount FROM budgets WHERE month = ? ORDER BY category",
            conn,
            params=(month,),
        )


def save_budget(month, category, amount):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO budgets (month, category, amount)
            VALUES (?, ?, ?)
            ON CONFLICT(month, category)
            DO UPDATE SET amount = excluded.amount
            """,
            (month, category.strip(), float(amount)),
        )
        conn.commit()


def remove_budget(month, category):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM budgets WHERE month = ? AND category = ?",
            (month, category),
        )
        conn.commit()


# ---------------------------------------------------------
# PREMIUM DARK THEME
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

    :root {
        --bg: #080D18;
        --panel: #111827;
        --panel-2: #151F30;
        --line: rgba(148,163,184,.14);
        --muted: #91A0B7;
        --text: #F3F6FC;
        --green: #35D39A;
        --blue: #6EA8FE;
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 12% 0%, rgba(35,90,120,.17), transparent 35%),
            linear-gradient(135deg, #080D18 0%, #0B1220 55%, #0A1020 100%);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: rgba(8,13,24,.82);
    }

    [data-testid="stSidebar"] {
        background: #0B1220;
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
    }

    h1, h2, h3 {
        font-family: 'Manrope', sans-serif !important;
        color: var(--text) !important;
        letter-spacing: -.035em;
    }

    p, label, .stMarkdown, [data-testid="stCaptionContainer"] {
        color: #B7C2D4;
    }

    .brand-mark {
        font-family: 'Manrope', sans-serif;
        font-size: 1.12rem;
        font-weight: 800;
        color: #F7FAFF;
        letter-spacing: -.03em;
        padding: .35rem 0 1.15rem 0;
    }

    .brand-mark span {
        color: var(--green);
    }

    .eyebrow {
        color: var(--green);
        font-size: .72rem;
        text-transform: uppercase;
        letter-spacing: .16em;
        font-weight: 700;
        margin-bottom: .35rem;
    }

    .hero-title {
        font-family: 'Manrope', sans-serif;
        font-size: 2.15rem;
        line-height: 1.15;
        font-weight: 800;
        color: #F7FAFF;
        letter-spacing: -.055em;
        margin: 0;
    }

    .hero-subtitle {
        color: #91A0B7;
        margin-top: .45rem;
        font-size: .95rem;
    }

    .metric-card {
        background: linear-gradient(145deg, rgba(22,34,53,.98), rgba(15,24,39,.98));
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 1.1rem 1.2rem;
        min-height: 132px;
        box-shadow: 0 12px 30px rgba(0,0,0,.12);
    }

    .metric-label {
        color: #91A0B7;
        font-size: .82rem;
        font-weight: 600;
    }

    .metric-value {
        color: #F7FAFF;
        font-family: 'Manrope', sans-serif;
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: -.045em;
        margin-top: .45rem;
    }

    .metric-note {
        color: var(--green);
        font-size: .75rem;
        margin-top: .3rem;
    }

    .section-heading {
        font-family: 'Manrope', sans-serif;
        font-size: 1.12rem;
        font-weight: 750;
        color: #F3F6FC;
        margin: .5rem 0 .8rem 0;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        overflow: hidden;
    }

    .stButton > button, .stDownloadButton > button {
        border-radius: 10px;
        border: 1px solid rgba(53,211,154,.35);
        background: rgba(53,211,154,.12);
        color: #DDFCEF;
        font-weight: 700;
        min-height: 2.6rem;
    }

    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: var(--green);
        background: rgba(53,211,154,.2);
        color: white;
    }

    /* High-contrast, accessible form controls */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input,
    [data-testid="stTextArea"] textarea {
        background: #F4F7FB !important;
        color: #101827 !important;
        -webkit-text-fill-color: #101827 !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        caret-color: #059669 !important;
    }

    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {
        color: #64748B !important;
        -webkit-text-fill-color: #64748B !important;
        opacity: 1 !important;
    }

    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
        background: #F4F7FB !important;
        color: #101827 !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
    }

    [data-testid="stSelectbox"] *,
    [data-testid="stMultiSelect"] * {
        color: #101827 !important;
    }

    [data-testid="stNumberInput"] button,
    [data-testid="stDateInput"] button {
        background: #E2E8F0 !important;
        color: #101827 !important;
    }

    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus,
    [data-testid="stDateInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border: 2px solid #10B981 !important;
        box-shadow: 0 0 0 2px rgba(16,185,129,.15) !important;
    }

    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] label {
        color: #E8EEF8 !important;
        font-weight: 650 !important;
    }

    [data-testid="stMetric"] {
        background: transparent;
    }

    hr {
        border-color: var(--line);
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
    }

    #MainMenu, footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# LOAD AND VALIDATE DATA
# ---------------------------------------------------------
try:
    check_database()
    df = load_expenses()
except Exception as error:
    st.error(f"Database check failed: {error}")
    st.warning(
        "Your database has not been recreated or reset. "
        "Please share this error before making further changes."
    )
    st.stop()

categories = sorted(df["category"].dropna().unique().tolist()) if not df.empty else []
if not categories:
    categories = ["Food", "Travel", "Shopping", "Bills", "Health", "Other"]

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="brand-mark">◈ PERSONAL FINANCE <span>PRO</span></div>',
        unsafe_allow_html=True,
    )
    st.caption("YOUR MONEY. YOUR CLARITY.")
    page = st.radio(
        "WORKSPACE",
        ["Overview", "Transactions", "Analytics", "Budgets"],
        label_visibility="visible",
    )
    st.divider()
    st.caption("DATABASE STATUS")
    st.success("Connected to existing SQLite database")
    st.caption(f"Records available: {len(df):,}")
    st.caption("Currency: INR (₹)")


# ---------------------------------------------------------
# REUSABLE DISPLAY HELPERS
# ---------------------------------------------------------
def metric_card(label, value, note):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_theme(fig, height=340):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#B7C2D4"),
        height=height,
        margin=dict(l=15, r=15, t=45, b=15),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#B7C2D4"),
        ),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(148,163,184,.12)", zeroline=False)
    return fig


def page_header(kicker, title, subtitle):
    st.markdown(
        f"""
        <div class="eyebrow">{kicker}</div>
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")


# ---------------------------------------------------------
# OVERVIEW
# ---------------------------------------------------------
if page == "Overview":
    page_header(
        "FINANCIAL COMMAND CENTER",
        "Your money, in focus.",
        "A clear view of your spending, habits and financial activity.",
    )

    if df.empty:
        st.info("Your database is connected, but there are no expense records yet.")
        st.caption("Open Transactions to add your first expense.")
    else:
        total = float(df["amount"].sum())
        count = len(df)
        average = total / count if count else 0
        this_month = date.today().strftime("%Y-%m")
        month_df = df[df["date"].dt.strftime("%Y-%m") == this_month]
        month_total = float(month_df["amount"].sum())

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("TOTAL SPENDING", money(total), "All recorded expenses")
        with c2:
            metric_card("THIS MONTH", money(month_total), date.today().strftime("%B %Y"))
        with c3:
            metric_card("TRANSACTIONS", f"{count:,}", "Recorded expenses")
        with c4:
            metric_card("AVERAGE EXPENSE", money(average), "Per transaction")

        st.write("")
        left, right = st.columns([1.35, 1])

        with left:
            st.markdown('<div class="section-heading">Monthly spending trend</div>', unsafe_allow_html=True)
            monthly = df.copy()
            monthly["month"] = monthly["date"].dt.to_period("M").astype(str)
            monthly = monthly.groupby("month", as_index=False)["amount"].sum()
            fig = px.area(
                monthly,
                x="month",
                y="amount",
                markers=True,
                labels={"month": "Month", "amount": "Spending (₹)"},
            )
            fig.update_traces(
                line=dict(color="#35D39A", width=3),
                fillcolor="rgba(53,211,154,.12)",
                marker=dict(size=7, color="#35D39A"),
            )
            st.plotly_chart(chart_theme(fig), use_container_width=True)

        with right:
            st.markdown('<div class="section-heading">Spending by category</div>', unsafe_allow_html=True)
            by_category = df.groupby("category", as_index=False)["amount"].sum()
            fig = px.pie(
                by_category,
                names="category",
                values="amount",
                hole=.68,
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig.update_traces(textposition="inside", textinfo="percent")
            st.plotly_chart(chart_theme(fig), use_container_width=True)

        st.markdown('<div class="section-heading">Recent transactions</div>', unsafe_allow_html=True)
        recent = df.head(8).copy()
        recent["date"] = recent["date"].dt.strftime("%d %b %Y")
        recent["amount"] = recent["amount"].map(money)
        recent = recent.rename(
            columns={
                "id": "ID",
                "date": "Date",
                "category": "Category",
                "description": "Description",
                "amount": "Amount",
            }
        )
        st.dataframe(
            recent[["ID", "Date", "Category", "Description", "Amount"]],
            use_container_width=True,
            hide_index=True,
        )


# ---------------------------------------------------------
# TRANSACTIONS
# ---------------------------------------------------------
elif page == "Transactions":
    page_header(
        "TRANSACTION MANAGEMENT",
        "Transactions",
        "Add new expenses and review your existing records.",
    )

    with st.expander("＋ Add a new expense", expanded=True):
        with st.form("add_expense_form", clear_on_submit=True):
            a, b = st.columns(2)
            amount = a.number_input("Amount (₹)", min_value=0.0, value=0.0, step=50.0, format="%.2f")
            expense_date = b.date_input("Date", value=date.today())
            category_choice = st.selectbox(
                "Category",
                ["Food", "Travel", "Shopping", "Bills", "Health", "Entertainment", "Education", "Other", "Custom"],
            )
            if category_choice == "Custom":
                category = st.text_input("Enter category")
            else:
                category = category_choice
            description = st.text_input("Description", placeholder="e.g. Lunch, fuel, electricity bill")
            submitted = st.form_submit_button("Save expense", use_container_width=True)

            if submitted:
                if amount <= 0:
                    st.error("Enter an amount greater than ₹0.")
                elif not category.strip():
                    st.error("Please enter a category.")
                else:
                    add_expense(amount, category, description, expense_date)
                    st.success("Expense saved. Your existing records are preserved.")
                    st.rerun()

    st.markdown('<div class="section-heading">All transactions</div>', unsafe_allow_html=True)
    if df.empty:
        st.info("No transactions found.")
    else:
        search = st.text_input("Search by category or description")
        view = df.copy()
        if search.strip():
            mask = (
                view["category"].str.contains(search, case=False, na=False)
                | view["description"].str.contains(search, case=False, na=False)
            )
            view = view[mask]
        display = view.copy()
        display["date"] = display["date"].dt.strftime("%d %b %Y")
        display["amount"] = display["amount"].map(money)
        display = display.rename(
            columns={
                "id": "ID",
                "date": "Date",
                "category": "Category",
                "description": "Description",
                "amount": "Amount",
            }
        )
        st.dataframe(
            display[["ID", "Date", "Category", "Description", "Amount"]],
            use_container_width=True,
            hide_index=True,
        )
        with st.expander("Edit a transaction"):
            edit_id = st.selectbox("Choose transaction ID to edit", view["id"].astype(int).tolist(), key="edit_expense_id")
            current = view.loc[view["id"] == edit_id].iloc[0]
            with st.form("edit_expense_form"):
                e1, e2 = st.columns(2)
                edit_amount = e1.number_input("Amount (₹)", min_value=0.0, value=float(current["amount"]), step=50.0, format="%.2f", key="edit_amount")
                current_date = current["date"].date()
                edit_date = e2.date_input("Date", value=current_date, key="edit_date")
                known_categories = ["Food", "Travel", "Shopping", "Bills", "Health", "Entertainment", "Education", "Other"]
                current_category = str(current["category"])
                category_options = list(dict.fromkeys(known_categories + [current_category]))
                edit_category = st.selectbox("Category", category_options, index=category_options.index(current_category), key="edit_category")
                edit_description = st.text_input("Description", value=str(current["description"]), key="edit_description")
                update_clicked = st.form_submit_button("Save changes", use_container_width=True)
                if update_clicked:
                    if edit_amount <= 0:
                        st.error("Enter an amount greater than ₹0.")
                    else:
                        update_expense(edit_id, edit_amount, edit_category, edit_description, edit_date)
                        st.success(f"Transaction {edit_id} updated.")
                        st.rerun()

        with st.expander("Delete a transaction"):
            st.warning("Deletion is permanent. Make sure you have a database backup.")
            chosen_id = st.selectbox("Select transaction ID", view["id"].astype(int).tolist(), key="delete_expense_id")
            confirm_delete = st.checkbox("I understand this will permanently delete the selected transaction.")
            if st.button("Delete selected transaction", disabled=not confirm_delete):
                delete_expense(chosen_id)
                st.success(f"Transaction {chosen_id} deleted.")
                st.rerun()

        csv_data = view.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download filtered transactions (CSV)",
            data=csv_data,
            file_name="personal_finance_transactions.csv",
            mime="text/csv",
        )


# ---------------------------------------------------------
# ANALYTICS - MONTHLY AND YEARLY
# ---------------------------------------------------------
elif page == "Analytics":
    page_header(
        "INSIGHTS & REPORTING",
        "Understand your spending.",
        "Explore category, monthly and yearly expense patterns.",
    )

    if df.empty:
        st.info("Add expenses to start generating analytics.")
    else:
        min_date = df["date"].min().date()
        max_date = df["date"].max().date()
        date_range = st.date_input(
            "Choose analysis date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="analytics_dates",
        )
        filtered = df.copy()
        if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
            start, end = date_range
            filtered = filtered[
                (filtered["date"].dt.date >= start)
                & (filtered["date"].dt.date <= end)
            ]

        if filtered.empty:
            st.info("No expenses in this date range.")
        else:
            total = float(filtered["amount"].sum())
            x1, x2, x3 = st.columns(3)
            x1.metric("Selected-period spending", money(total))
            x2.metric("Transactions", len(filtered))
            x3.metric("Average transaction", money(total / len(filtered)))

            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="section-heading">Monthly spending</div>', unsafe_allow_html=True)
                monthly = filtered.copy()
                monthly["month"] = monthly["date"].dt.to_period("M").astype(str)
                monthly = monthly.groupby("month", as_index=False)["amount"].sum()
                fig = px.bar(
                    monthly,
                    x="month",
                    y="amount",
                    text_auto=".2s",
                    labels={"month": "Month", "amount": "Spending (₹)"},
                    color_discrete_sequence=["#35D39A"],
                )
                st.plotly_chart(chart_theme(fig), use_container_width=True)

            with c2:
                st.markdown('<div class="section-heading">Yearly spending</div>', unsafe_allow_html=True)
                yearly = filtered.copy()
                yearly["year"] = yearly["date"].dt.year.astype(str)
                yearly = yearly.groupby("year", as_index=False)["amount"].sum()
                fig = px.bar(
                    yearly,
                    x="year",
                    y="amount",
                    text_auto=".2s",
                    labels={"year": "Year", "amount": "Spending (₹)"},
                    color_discrete_sequence=["#6EA8FE"],
                )
                st.plotly_chart(chart_theme(fig), use_container_width=True)

            c3, c4 = st.columns(2)
            with c3:
                st.markdown('<div class="section-heading">Category distribution</div>', unsafe_allow_html=True)
                cat = filtered.groupby("category", as_index=False)["amount"].sum()
                fig = px.pie(
                    cat,
                    names="category",
                    values="amount",
                    hole=.62,
                    color_discrete_sequence=px.colors.qualitative.Safe,
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(chart_theme(fig), use_container_width=True)

            with c4:
                st.markdown('<div class="section-heading">Category summary</div>', unsafe_allow_html=True)
                report = (
                    filtered.groupby("category")
                    .agg(Total_Spending=("amount", "sum"), Transactions=("id", "count"))
                    .reset_index()
                    .sort_values("Total_Spending", ascending=False)
                )
                report["Share"] = report["Total_Spending"] / total * 100
                report["Total_Spending"] = report["Total_Spending"].map(money)
                report["Share"] = report["Share"].map(lambda v: f"{v:.1f}%")
                st.dataframe(report, use_container_width=True, hide_index=True)


# ---------------------------------------------------------
# BUDGETS
# ---------------------------------------------------------
elif page == "Budgets":
    page_header(
        "PLAN & CONTROL",
        "Monthly budgets",
        "Set category spending limits and monitor your progress.",
    )

    selected_month = st.date_input("Choose budget month", value=date.today(), key="budget_month")
    month_key = selected_month.strftime("%Y-%m")
    budget_df = load_budgets(month_key)

    with st.expander("＋ Set or update a category budget", expanded=True):
        with st.form("budget_form"):
            budget_category = st.selectbox("Category", sorted(set(categories + ["Food", "Travel", "Shopping", "Bills", "Other"])))
            budget_amount = st.number_input("Monthly limit (₹)", min_value=1.0, step=500.0)
            save = st.form_submit_button("Save budget", use_container_width=True)
            if save:
                save_budget(month_key, budget_category, budget_amount)
                st.success("Budget saved.")
                st.rerun()

    month_expenses = df[df["date"].dt.strftime("%Y-%m") == month_key] if not df.empty else df
    if budget_df.empty:
        st.info("No budgets set for this month yet. Add a category budget above.")
    else:
        for _, budget in budget_df.iterrows():
            spent = float(
                month_expenses.loc[
                    month_expenses["category"] == budget["category"], "amount"
                ].sum()
            )
            limit = float(budget["amount"])
            ratio = spent / limit if limit else 0
            st.markdown(f"**{budget['category']}**")
            st.progress(min(ratio, 1.0))
            status = "Over budget" if spent > limit else "Within budget"
            st.caption(f"{money(spent)} spent of {money(limit)} · {status}")
            if spent > limit:
                st.warning(f"{budget['category']} budget exceeded by {money(spent - limit)}.")
            st.write("")

        with st.expander("Remove a budget"):
            selected_category = st.selectbox(
                "Budget category to remove",
                budget_df["category"].tolist(),
            )
            if st.button("Remove selected budget"):
                remove_budget(month_key, selected_category)
                st.success("Budget removed.")
                st.rerun()

st.divider()
st.caption("Personal Finance Pro · Your data stays in your local SQLite database.")
