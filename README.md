# StasisMonitor

A Streamlit dashboard for tracking investment fund portfolio performance. Fetches live prices from Stooq, stores transactions in a local SQLite database, and displays portfolio value over time.

## Features

- **Dashboard** — portfolio value, profit/loss, and a time-series chart with selectable periods (1M / 3M / 6M / 1Y / 2Y / MAX)
- **Transactions** — add and delete BUY/SELL transactions; color-coded history table
- **Live prices** — fetched from [Stooq](https://stooq.pl) and cached for 1 hour
- **CSV export** — download your transaction history at any time

## Project structure

```
StasisMonitor/
├── frontend/
│   ├── Monitor.py          # main dashboard page
│   └── pages/
│       ├── 1_Transakcje.py # transactions page
│       └── 2_Importuj.py   # CSV import page
├── backend/
│   ├── database/
│   │   ├── db.py           # SQLite connection & init
│   │   └── schema.sql      # table definitions
│   └── services/
│       ├── prices.py       # Stooq price fetching
│       ├── portfolio.py    # portfolio calculations
│       └── transactions.py # CRUD for transactions
└── data/
    └── investments.db      # local SQLite database
```

## Setup

1. Clone the repo and create a virtual environment:

   ```bash
   python -m venv .stasisVenv
   source .stasisVenv/bin/activate
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root:

   ```
   STOOQ_API_KEY=your_key_here
   ```

3. Run the app:

   ```bash
   streamlit run frontend/Monitor.py
   ```

## Requirements

- Python 3.10+
- See [requirements.txt](requirements.txt) for dependencies (`streamlit`, `pandas`, `plotly`, `requests`, `beautifulsoup4`, `openpyxl`, `python-dotenv`)