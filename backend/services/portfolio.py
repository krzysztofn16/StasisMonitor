import pandas as pd
from backend.database.db import get_connection


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
    sells = transactions_df[transactions_df["type"] == "SELL"]
    return (buys["units"] * buys["price_per_unit"]).sum() - (sells["units"] * sells["price_per_unit"]).sum()


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
        return pd.DataFrame(columns=["date", "value", "invested"])

    transactions_df = transactions_df.copy()
    transactions_df["date"] = pd.to_datetime(transactions_df["date"])

    prices_df = prices_df.copy()
    prices_df["date"] = pd.to_datetime(prices_df["date"])

    today = pd.Timestamp.today().normalize()
    last_price = prices_df.iloc[-1]["price"]
    last_date = prices_df.iloc[-1]["date"]

    if last_date < today:
        today_row = pd.DataFrame([{"date": today, "price": last_price}])
        prices_df = pd.concat([prices_df, today_row], ignore_index=True)

    rows = []
    for _, price_row in prices_df.iterrows():
        day = price_row["date"]
        txns_to_date = transactions_df[transactions_df["date"] <= day]

        bought       = txns_to_date[txns_to_date["type"] == "BUY"]["units"].sum()
        sold         = txns_to_date[txns_to_date["type"] == "SELL"]["units"].sum()
        units        = bought - sold

        # Łączna zainwestowana kwota do tego dnia
        invested = (
            txns_to_date[txns_to_date["type"] == "BUY"]["total_value"].sum() -
            txns_to_date[txns_to_date["type"] == "SELL"]["total_value"].sum()
        )

        rows.append({
            "date":     day,
            "value":    units * price_row["price"],
            "invested": invested
        })

    return pd.DataFrame(rows)


def get_portfolio_allocation(fund_summaries: list[dict]) -> dict:
    """
    Oblicza rzeczywistą alokację portfela na podstawie fund_allocation table.
    
    Args:
        fund_summaries: Lista słowników z danymi o funduszach (fund, summary, latest_price, latest_date)
    
    Returns:
        Słownik z alokacją: {"Akcje": 35.5, "Obligacje": 60.0, "Gotówka": 4.5, ...}
    """
    if not fund_summaries:
        return {}
    
    conn = get_connection()
    
    # Oblicz całkowitą wartość portfela
    total_value = sum(f["summary"]["current_value"] for f in fund_summaries)
    
    if total_value == 0:
        conn.close()
        return {}
    
    # Zbierz alokacje dla każdej kategorii
    allocation = {}
    
    for fund_data in fund_summaries:
        fund_code = fund_data["fund"]["code"]
        fund_value = fund_data["summary"]["current_value"]
        
        # Pobierz alokację dla tego funduszu z bazy
        rows = conn.execute(
            "SELECT category, percentage FROM fund_allocation WHERE fund_code = ?",
            (fund_code,)
        ).fetchall()
        
        # Dla każdej kategorii, oblicz jej udział w tym funduszu
        for row in rows:
            category = row["category"]
            category_pct = row["percentage"]
            
            # Wkład tej kategorii z tego funduszu = wartość funduszu * % kategorii w funduszu
            contribution = (fund_value * category_pct) / 100
            
            if category not in allocation:
                allocation[category] = 0
            allocation[category] += contribution
    
    conn.close()
    
    # Konwertuj na procenty (względem całego portfela)
    allocation_pct = {}
    for category, value in allocation.items():
        allocation_pct[category] = round((value / total_value) * 100, 1)
    
    return allocation_pct