"""
Personal Expense Tracker — Streamlit UI.

Run with:  streamlit run app.py

All data handling lives in expense_tracker.py; this file only builds the
interface and calls into it.
"""

import matplotlib.pyplot as plt
import streamlit as st

import expense_tracker as et

st.set_page_config(page_title="Personal Expense Tracker", page_icon="💰", layout="wide")

# Load the expenses, seeding sample data the very first time the app runs.
expenses = et.ensure_data_file()


def format_rupees(amount: float) -> str:
    return f"₹{amount:,.2f}"


# ---------------------------------------------------------------------------
# Sidebar: add a new expense
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Add an expense")
    with st.form("add_expense_form", clear_on_submit=True):
        expense_date = st.date_input("Date")
        category = st.selectbox("Category", et.CATEGORIES)
        amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
        payment_mode = st.selectbox("Payment mode", et.PAYMENT_MODES)
        note = st.text_input("Note (optional)")
        submitted = st.form_submit_button("Add expense")

    if submitted:
        if amount <= 0:
            st.error("Amount must be greater than zero.")
        else:
            expenses = et.add_expense(
                expenses, expense_date, category, amount, payment_mode, note
            )
            et.save_expenses(expenses)
            st.success("Expense added.")
            st.rerun()

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

st.title("💰 Personal Expense Tracker")
st.caption("Track where your money goes — categorise expenses and see spending trends.")

if expenses.empty:
    st.info("No expenses yet. Add your first one from the sidebar.")
    st.stop()

# --- Filters ---------------------------------------------------------------

months = sorted(expenses["date"].dt.strftime("%Y-%m").unique(), reverse=True)
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    selected_month = st.selectbox("Filter by month", ["All months"] + months)
with filter_col2:
    selected_categories = st.multiselect(
        "Filter by category", et.CATEGORIES, default=et.CATEGORIES
    )

view = expenses[expenses["category"].isin(selected_categories)]
if selected_month != "All months":
    view = view[view["date"].dt.strftime("%Y-%m") == selected_month]
view = view.sort_values("date", ascending=False)

# --- Summary cards (reflect the current filter) -----------------------------

metric_cols = st.columns(3)
metric_cols[0].metric("Total spend", format_rupees(et.total_spend(view)))
top = et.top_category(view)
metric_cols[1].metric("Top category", top if top else "—")
metric_cols[2].metric(
    "Average daily spend", format_rupees(et.average_daily_spend(view))
)

# --- Expense table + delete -------------------------------------------------

st.subheader("Expenses")
if view.empty:
    st.info("No expenses match the current filters.")
else:
    display = view.copy()
    display["date"] = display["date"].dt.strftime("%Y-%m-%d")
    display["amount"] = display["amount"].map(format_rupees)
    st.dataframe(
        display[["date", "category", "amount", "payment_mode", "note"]],
        width="stretch",
        hide_index=True,
    )

    # Delete works on the expense id, shown in the label so there is no
    # ambiguity about which row is being removed.
    labels = {
        int(row.id): (
            f"#{int(row.id)} · {row.date:%Y-%m-%d} · {row.category} · "
            f"{format_rupees(row.amount)} · {row.note or 'no note'}"
        )
        for row in view.itertuples()
    }
    delete_col1, delete_col2 = st.columns([3, 1])
    with delete_col1:
        expense_to_delete = st.selectbox(
            "Select an expense to delete",
            options=list(labels.keys()),
            format_func=lambda expense_id: labels[expense_id],
        )
    with delete_col2:
        st.write("")  # nudge the button down to align with the selectbox
        if st.button("Delete expense", type="secondary"):
            expenses = et.delete_expense(expenses, expense_to_delete)
            et.save_expenses(expenses)
            st.success("Expense deleted.")
            st.rerun()

# --- Charts -------------------------------------------------------------------

st.subheader("Spending analytics")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**Spend by category**")
    by_category = et.spend_by_category(view)
    if by_category.empty:
        st.info("Nothing to chart for the current filters.")
    else:
        st.bar_chart(by_category)

with chart_col2:
    st.markdown("**Category share**")
    if by_category.empty:
        st.info("Nothing to chart for the current filters.")
    else:
        # Streamlit has no native pie chart, so this one is matplotlib.
        fig, ax = plt.subplots()
        ax.pie(
            by_category.values,
            labels=by_category.index,
            autopct="%1.0f%%",
            startangle=90,
        )
        ax.axis("equal")  # keep the pie a circle, not an ellipse
        st.pyplot(fig)

st.markdown("**Monthly spending trend**")
trend = et.monthly_trend(view)
if trend.empty:
    st.info("Nothing to chart for the current filters.")
else:
    st.line_chart(trend.set_index("month")["amount"])
