# Personal Expense Tracker

An expense-tracking app with categorization and visual analytics for spending trends. A small web app to record everyday expenses, organise them by category, and understand where the money goes through summary metrics and charts. Data is stored locally in a CSV file — no database or account needed.

## Features

- **Add expenses** from a sidebar form: date, category, amount, payment mode and an optional note
- **Fixed categories** — Food, Transport, Rent, Shopping, Entertainment, Bills, Other — so analytics stay consistent
- **Expense table** with filters by month and category, and a delete option for individual entries
- **Summary cards**: total spend, top category and average daily spend (all respond to the active filters)
- **Visual analytics**:
  - Bar chart of spend per category
  - Pie chart of category share
  - Line chart of the monthly spending trend
- **Demo-ready**: on first run the app seeds ~30 realistic sample expenses from the last three months so the charts work immediately; your own data is never overwritten afterwards

## Tech Stack

- **Python**
- **Streamlit** — web UI and native charts
- **Pandas** — data handling and analytics (group-by aggregations)
- **Matplotlib** — pie chart (Streamlit has no native one)
- **CSV** — local storage (`data/expenses.csv`)

## Setup & Run

```bash
# 1. Clone the repository and enter it
git clone https://github.com/Vishal-361/Personal-Expense-Tracker.git
cd Personal-Expense-Tracker

# 2. Create and activate a virtual environment
python -m venv venv
# Windows:  venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`.

## Project Structure

```
Personal-Expense-Tracker/
├── app.py               # Streamlit UI: form, filters, table, charts
├── expense_tracker.py   # Data layer (pandas): load/save, add/delete, analytics
├── requirements.txt     # Python dependencies
├── data/
│   └── expenses.csv     # Created automatically on first run (seeded with samples)
└── README.md
```

## How It Works

`expense_tracker.py` is deliberately independent of Streamlit: every function takes and returns a pandas DataFrame, so the logic can be imported and tested on its own.

- `load_expenses` / `save_expenses` — read/write the CSV; loading a missing file returns an empty, correctly-shaped DataFrame instead of crashing
- `add_expense` / `delete_expense` — rows carry a unique `id` (`max id + 1`) so a specific expense can be deleted unambiguously
- Analytics — `total_spend`, `spend_by_category` (group-by sum), `monthly_trend` (group-by month), `top_category`, `average_daily_spend` (total ÷ days between first and last expense)
- `ensure_data_file` — seeds sample data **only if** the CSV does not exist yet, so real user data is never overwritten
