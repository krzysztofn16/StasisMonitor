import os
import io
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

STOOQ_API_KEY = os.getenv("STOOQ_API_KEY")

def _fetch_raw(stooq_ticker: str) -> pd.DataFrame:
    """Pobiera surowe dane ze Stooq i zwraca czysty DataFrame"""
    url = f"https://stooq.pl/q/d/l/?s={stooq_ticker}&i=d&apikey={STOOQ_API_KEY}"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()

    df = pd.read_csv(io.StringIO(r.text))

    # Kolumny są po polsku — standaryzujemy
    df.columns = ["date", "open", "high", "low", "close"]
    df["date"] = pd.to_datetime(df["date"])
    df = df[["date", "close"]].rename(columns={"close": "price"})
    df = df.sort_values("date").reset_index(drop=True)

    return df


def _filter_by_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Przytnij do wybranego okresu"""
    if period == "MAX":
        return df

    today = pd.Timestamp.today()
    cutoffs = {
        "1M": today - pd.DateOffset(months=1),
        "3M": today - pd.DateOffset(months=3),
        "6M": today - pd.DateOffset(months=6),
        "1Y": today - pd.DateOffset(years=1),
        "2Y": today - pd.DateOffset(years=2),
    }
    cutoff = cutoffs.get(period, cutoffs["1Y"])
    return df[df["date"] >= cutoff].reset_index(drop=True)


@st.cache_data(ttl=3600)
def get_price_history(stooq_ticker: str, period: str = "1Y") -> pd.DataFrame:
    """
    Pobiera historię cen ze Stooq.
    Cache na 1 godzinę — nie odpytujemy API przy każdym kliknięciu.
    """
    try:
        df = _fetch_raw(stooq_ticker)
        return _filter_by_period(df, period)
    except Exception as e:
        st.warning(f"Nie udało się pobrać cen ze Stooq: {e}")
        return pd.DataFrame(columns=["date", "price"])


def get_latest_price(stooq_ticker: str) -> tuple[float, str]:
    """Zwraca ostatnią cenę i datę wyceny"""
    df = get_price_history(stooq_ticker, period="1M")
    if df.empty:
        return 0.0, "brak danych"

    latest = df.iloc[-1]
    return float(latest["price"]), str(latest["date"].date())