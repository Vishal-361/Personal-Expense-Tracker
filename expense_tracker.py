"""
Data layer for the Personal Expense Tracker.

Everything in this module works with plain pandas DataFrames, so the logic
can be imported and tested without Streamlit. ``app.py`` is only the UI —
it calls into the functions here.

Expenses are stored in a CSV file with these columns:

    id, date, category, amount, payment_mode, note
"""

from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# Fixed category list. The UI builds its dropdown from this and the
# analytics group by it, so new categories should only be added here.
CATEGORIES = [
    "Food",
    "Transport",
    "Rent",
    "Shopping",
    "Entertainment",
    "Bills",
    "Other",
]

PAYMENT_MODES = ["Cash", "Card", "UPI", "Bank Transfer"]

COLUMNS = ["id", "date", "category", "amount", "payment_mode", "note"]

DEFAULT_DATA_PATH = Path(__file__).parent / "data" / "expenses.csv"


# ---------------------------------------------------------------------------
# Loading / saving
# ---------------------------------------------------------------------------

def _empty_frame() -> pd.DataFrame:
    """An expenses DataFrame with the right columns and dtypes, but no rows."""
    frame = pd.DataFrame(columns=COLUMNS)
    frame["date"] = pd.to_datetime(frame["date"])
    return frame


def load_expenses(path=DEFAULT_DATA_PATH) -> pd.DataFrame:
    """Read expenses from the CSV file.

    Returns an empty (but correctly shaped) DataFrame if the file does not
    exist yet, so the rest of the code never has to special-case it.
    """
    path = Path(path)
    if not path.exists():
        return _empty_frame()

    frame = pd.read_csv(path, parse_dates=["date"])
    # Guard against a hand-edited CSV that's missing a column.
    for column in COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    frame = frame[COLUMNS]
    frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce").fillna(0.0)
    return frame.sort_values("date").reset_index(drop=True)


def save_expenses(expenses: pd.DataFrame, path=DEFAULT_DATA_PATH) -> None:
    """Write expenses back to the CSV file, creating the folder if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    expenses.to_csv(path, index=False, date_format="%Y-%m-%d")


# ---------------------------------------------------------------------------
# Adding / deleting
# ---------------------------------------------------------------------------

def add_expense(expenses: pd.DataFrame, expense_date, category: str,
                amount: float, payment_mode: str, note: str = "") -> pd.DataFrame:
    """Return a new DataFrame with one expense appended.

    The new row gets ``id = max(existing ids) + 1`` so ids stay unique and
    can be used to delete a specific expense later.
    """
    if category not in CATEGORIES:
        raise ValueError(f"Unknown category: {category!r}")
    if amount <= 0:
        raise ValueError("Amount must be positive")

    next_id = int(expenses["id"].max()) + 1 if not expenses.empty else 1
    new_row = {
        "id": next_id,
        "date": pd.to_datetime(expense_date),
        "category": category,
        "amount": round(float(amount), 2),
        "payment_mode": payment_mode,
        "note": note.strip(),
    }
    updated = pd.concat([expenses, pd.DataFrame([new_row])], ignore_index=True)
    return updated.sort_values("date").reset_index(drop=True)


def delete_expense(expenses: pd.DataFrame, expense_id: int) -> pd.DataFrame:
    """Return a new DataFrame with the expense of the given id removed."""
    return expenses[expenses["id"] != expense_id].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

def total_spend(expenses: pd.DataFrame) -> float:
    """Total amount spent across all rows."""
    if expenses.empty:
        return 0.0
    return float(expenses["amount"].sum())


def spend_by_category(expenses: pd.DataFrame) -> pd.Series:
    """Total spend per category, highest first."""
    if expenses.empty:
        return pd.Series(dtype=float)
    return expenses.groupby("category")["amount"].sum().sort_values(ascending=False)


def monthly_trend(expenses: pd.DataFrame) -> pd.DataFrame:
    """Total spend per calendar month.

    Returns a DataFrame with ``month`` ("YYYY-MM") and ``amount`` columns,
    sorted chronologically — ready to feed to a line chart.
    """
    if expenses.empty:
        return pd.DataFrame(columns=["month", "amount"])
    trend = (
        expenses.groupby(expenses["date"].dt.strftime("%Y-%m"))["amount"]
        .sum()
        .reset_index()
        .rename(columns={"date": "month"})
        .sort_values("month")
    )
    return trend


def top_category(expenses: pd.DataFrame):
    """Name of the category with the highest total spend (None if no data)."""
    by_category = spend_by_category(expenses)
    if by_category.empty:
        return None
    return by_category.index[0]


def average_daily_spend(expenses: pd.DataFrame) -> float:
    """Average spend per day over the span covered by the data.

    The span runs from the earliest to the latest expense date (inclusive),
    so a single day of data averages to that day's total.
    """
    if expenses.empty:
        return 0.0
    span_days = (expenses["date"].max() - expenses["date"].min()).days + 1
    return total_spend(expenses) / span_days


# ---------------------------------------------------------------------------
# Seed data (first run only)
# ---------------------------------------------------------------------------

# Sample expenses as (days_ago, category, amount, payment_mode, note).
# "days_ago" is relative to today so the demo data always covers roughly
# the last three months, whenever the app is first run.
_SEED_ROWS = [
    (61, "Rent", 6500, "Bank Transfer", "Monthly rent"),
    (57, "Bills", 842, "Card", "Electricity bill"),
    (54, "Food", 1330, "Card", "Weekly groceries"),
    (52, "Bills", 999, "UPI", "Broadband internet"),
    (49, "Other", 120, "Cash", "Printouts"),
    (47, "Shopping", 1499, "Card", "Running shoes"),
    (44, "Food", 1150, "Card", "Weekly groceries"),
    (42, "Other", 200, "Cash", "Haircut"),
    (38, "Transport", 300, "UPI", "Metro card recharge"),
    (35, "Bills", 299, "UPI", "Mobile recharge"),
    (33, "Food", 180, "Cash", "Snacks"),
    (31, "Rent", 6500, "Bank Transfer", "Monthly rent"),
    (29, "Entertainment", 199, "Card", "OTT subscription"),
    (27, "Bills", 910, "Card", "Electricity bill"),
    (24, "Food", 1410, "Card", "Weekly groceries"),
    (22, "Bills", 999, "UPI", "Broadband internet"),
    (19, "Transport", 340, "UPI", "Cab ride"),
    (16, "Food", 240, "Cash", "Lunch near college"),
    (15, "Shopping", 799, "Card", "T-shirt"),
    (14, "Other", 260, "Cash", "Pharmacy"),
    (11, "Food", 980, "Card", "Weekly groceries"),
    (9, "Transport", 500, "Cash", "Petrol"),
    (7, "Bills", 876, "Card", "Electricity bill"),
    (6, "Entertainment", 350, "UPI", "Movie ticket"),
    (5, "Food", 860, "UPI", "Dinner with friends"),
    (3, "Transport", 120, "Cash", "Auto to college"),
    (2, "Food", 1240, "Card", "Weekly groceries"),
    (1, "Rent", 6500, "Bank Transfer", "Monthly rent"),
    (0, "Shopping", 350, "UPI", "Notebook and stationery"),
    (0, "Food", 210, "Cash", "Lunch near college"),
]


def generate_seed_data() -> pd.DataFrame:
    """Build the ~30 sample expenses used to demo the app on first run."""
    today = date.today()
    frame = pd.DataFrame(
        [
            {
                "id": index + 1,
                "date": today - timedelta(days=days_ago),
                "category": category,
                "amount": float(amount),
                "payment_mode": payment_mode,
                "note": note,
            }
            for index, (days_ago, category, amount, payment_mode, note)
            in enumerate(_SEED_ROWS)
        ]
    )
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.sort_values("date").reset_index(drop=True)


def ensure_data_file(path=DEFAULT_DATA_PATH) -> pd.DataFrame:
    """Load expenses, seeding the CSV with sample data on first run only.

    If the file already exists it is loaded as-is — real data entered by
    the user is never overwritten.
    """
    path = Path(path)
    if path.exists():
        return load_expenses(path)

    seeded = generate_seed_data()
    save_expenses(seeded, path)
    return seeded
