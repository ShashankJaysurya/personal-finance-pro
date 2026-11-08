import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Personal Expense Tracker")
st.caption("Your personal financial dashboard")

DB_PATH = Path.cwd() / "data" / "expenses.db"

def get_expenses():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM expenses ORDER BY id DESC",
        conn
    )
    conn.close()
    return df

try:
    df = get_expenses()

    if df.empty:
        st.info("No expenses recorded yet.")
        st.stop()

    total = df["amount"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Spending", f"₹{total:,.2f}")
    col2.metric("Transactions", len(df))
    col3.metric(
        "Average Expense",
        f"₹{df['amount'].mean():,.2f}"
    )

    st.divider()

    st.subheader("Expense History")
    st.dataframe(df, use_container_width=True)

    st.subheader("Category-wise Spending")

    category_data = (
        df.groupby("category")["amount"]
        .sum()
        .reset_index()
    )

    fig = px.pie(
        category_data,
        names="category",
        values="amount",
        hole=0.4
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Monthly Spending")

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    monthly_data = (
        df.groupby("month")["amount"]
        .sum()
        .reset_index()
    )

    fig2 = px.bar(
        monthly_data,
        x="month",
        y="amount",
        title="Monthly Expense Overview"
    )

    st.plotly_chart(fig2, use_container_width=True)

except Exception as e:
    st.error(f"Dashboard error: {e}")

    # ==========================================
# PHASE 2: VISUAL FINANCIAL ANALYTICS
# ==========================================

st.markdown("---")
st.header("📊 Financial Analytics")

# Load existing expense records
try:
    conn = sqlite3.connect(str(DB_PATH))

    df = pd.read_sql_query(
        """
        SELECT id, amount, category, description, date
        FROM expenses
        """,
        conn
    )

    conn.close()

    if not df.empty:

        # Data preparation
        df["amount"] = pd.to_numeric(
            df["amount"], errors="coerce"
        )

        df["date"] = pd.to_datetime(
            df["date"], errors="coerce"
        )

        df = df.dropna(
            subset=["amount", "date"]
        )

        df["category"] = (
            df["category"].fillna("Uncategorized")
        )

        # Date filters
        st.subheader("Filter Your Expenses")

        min_date = df["date"].min().date()
        max_date = df["date"].max().date()

        selected_dates = st.date_input(
            "Select date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        if (
            isinstance(selected_dates, tuple)
            and len(selected_dates) == 2
        ):
            start_date, end_date = selected_dates

            filtered_df = df[
                (df["date"].dt.date >= start_date)
                & (df["date"].dt.date <= end_date)
            ]
        else:
            filtered_df = df

        if not filtered_df.empty:

            # Summary metrics
            total = filtered_df["amount"].sum()

            transactions = len(filtered_df)

            average = total / transactions

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Filtered Spending",
                f"₹{total:,.2f}"
            )

            col2.metric(
                "Transactions",
                transactions
            )

            col3.metric(
                "Average Expense",
                f"₹{average:,.2f}"
            )

            st.markdown("---")

            # Two-column chart layout
            chart1, chart2 = st.columns(2)

            # Category-wise spending
            with chart1:

                st.subheader(
                    "Category-wise Spending"
                )

                category_data = (
                    filtered_df.groupby("category")[
                        "amount"
                    ]
                    .sum()
                    .reset_index()
                )

                fig1 = px.pie(
                    category_data,
                    names="category",
                    values="amount",
                    hole=0.45,
                    title="Expense Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )

                fig1.update_traces(
                    textinfo="percent+label"
                )

                fig1.update_layout(
                    height=400,
                    margin=dict(
                        t=50, b=20, l=20, r=20
                    )
                )

                st.plotly_chart(
                    fig1,
                    use_container_width=True
                )

            # Monthly spending
            with chart2:

                st.subheader(
                    "Monthly Spending"
                )

                monthly_data = filtered_df.copy()

                monthly_data["month"] = (
                    monthly_data["date"]
                    .dt.to_period("M")
                    .astype(str)
                )

                monthly_data = (
                    monthly_data.groupby("month")[
                        "amount"
                    ]
                    .sum()
                    .reset_index()
                )

                fig2 = px.bar(
                    monthly_data,
                    x="month",
                    y="amount",
                    title="Monthly Expense Overview",
                    labels={
                        "month": "Month",
                        "amount": "Spending (INR)"
                    },
                    text_auto=".2f"
                )

                fig2.update_layout(
                    height=400,
                    xaxis_title="Month",
                    yaxis_title="Amount (INR)",
                    margin=dict(
                        t=50, b=20, l=20, r=20
                    )
                )

                st.plotly_chart(
                    fig2,
                    use_container_width=True
                )

            # Detailed category report
            st.markdown("---")

            st.subheader(
                "Category Spending Report"
            )

            category_report = (
                filtered_df.groupby("category")
                .agg(
                    Total_Spending=("amount", "sum"),
                    Transactions=("id", "count")
                )
                .reset_index()
                .sort_values(
                    "Total_Spending",
                    ascending=False
                )
            )

            st.dataframe(
                category_report,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info(
                "No expenses found for the selected dates."
            )

    else:
        st.info(
            "Add expenses to generate financial analytics."
        )

except Exception as e:

    st.error(
        f"Analytics error: {e}"
    )