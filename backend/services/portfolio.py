import pandas as pd

def get_units_held(transactions_df: pd.DataFrame) -> float:
    """Ile jednostek aktualnie posiadasz"""
    if transactions_df.empty:
        return 0.0
    
    bought = transactions_df[transactions_df["type"] == "BUY"]["units"].sum()
    sold   = transactions_df[transactions_df["type"] == "SELL"]["units"].sum()
    return bought - sold


def get_avg_buy_price(transactions_df: pd.DataFrame) -> float:
    """Średnia cena zakupu jednostki"""
    buys = transactions_df[transactions_df["type"] == "BUY"]
    if buys.empty:
        return 0.0
    
    total_spent = (buys["units"] * buys["price_per_unit"]).sum()
    total_units = buys["units"].sum()
    return total_spent / total_units


def get_total_invested(transactions_df: pd.DataFrame) -> float:
    """Łączna kwota zainwestowana (tylko BUY)"""
    buys = transactions_df[transactions_df["type"] == "BUY"]
    return (buys["units"] * buys["price_per_unit"]).sum()


def get_portfolio_summary(transactions_df: pd.DataFrame, latest_price: float) -> dict:
    """Główna funkcja — zwraca wszystko czego potrzebuje dashboard"""
    units_held     = get_units_held(transactions_df)
    avg_buy_price  = get_avg_buy_price(transactions_df)
    total_invested = get_total_invested(transactions_df)
    current_value  = units_held * latest_price
    profit_pln     = current_value - total_invested
    profit_pct     = (profit_pln / total_invested * 100) if total_invested > 0 else 0.0

    return {
        "units_held":     units_held,
        "avg_buy_price":  avg_buy_price,
        "total_invested": total_invested,
        "current_value":  current_value,
        "profit_pln":     profit_pln,
        "profit_pct":     profit_pct,
        "latest_price":   latest_price,
    }


def get_portfolio_history(transactions_df: pd.DataFrame, prices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Historia wartości portfela w czasie — dane do wykresu.
    Dla każdego dnia w prices_df oblicza ile jednostek miałeś
    i mnoży przez cenę z tego dnia.
    """
    if transactions_df.empty or prices_df.empty:
        return pd.DataFrame(columns=["date", "value"])

    transactions_df = transactions_df.copy()
    transactions_df["date"] = pd.to_datetime(transactions_df["date"])

    rows = []
    for _, price_row in prices_df.iterrows():
        day = price_row["date"]

        # Transakcje DO tego dnia włącznie
        txns_to_date = transactions_df[transactions_df["date"] <= day]

        bought = txns_to_date[txns_to_date["type"] == "BUY"]["units"].sum()
        sold   = txns_to_date[txns_to_date["type"] == "SELL"]["units"].sum()
        units  = bought - sold

        rows.append({
            "date":  day,
            "value": units * price_row["price"]
        })

    return pd.DataFrame(rows)