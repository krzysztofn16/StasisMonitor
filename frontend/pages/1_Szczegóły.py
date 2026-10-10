import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from backend.database.db import init_db, get_all_funds
from backend.services.transactions import get_transactions
from backend.services.prices import get_price_history, get_latest_price
from backend.services.portfolio import get_portfolio_summary
from backend.services.auth import get_current_user, show_auth_page, logout

# ── Init ──────────────────────────────────────────────────────────────────────
init_db()
st.set_page_config(page_title="Fundusz — MarketSTI Monitor", page_icon="🏦", layout="wide")

user_id = get_current_user()
if user_id is None:
    show_auth_page()
    st.stop()

# ── Dane ──────────────────────────────────────────────────────────────────────
transactions_df = get_transactions(user_id)

if transactions_df.empty:
    st.title("🏦 Fundusz")
    st.info("Nie masz jeszcze żadnych transakcji. Przejdź do strony **Transakcje** żeby dodać pierwszą.")
    st.stop()

all_funds = {f["code"]: f for f in get_all_funds()}
held_codes = transactions_df["fund_code"].unique().tolist()
held_funds = [all_funds[c] for c in held_codes if c in all_funds]

if not held_funds:
    st.title("🏦 Fundusz")
    st.warning("Brak danych o funduszach.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"👤 **{user_id}**")
    if st.button("Wyloguj", use_container_width=True):
        logout()
    st.divider()

    fund_options = {
        f"{f['name']} ({f['code']})": f["code"]
        for f in held_funds
    }
    selected_label = st.selectbox("Wybierz fundusz", list(fund_options.keys()))
    selected_code = fund_options[selected_label]

    st.divider()
    st.markdown("[📝 Prześlij feedback](https://forms.gle/uDh9U5EAzcZ2s3yP6)")
    st.markdown("[☕ Postaw kawę zeby to rozwijać po godzinach 😏](https://buymeacoffee.com/monitorsti)")

# ── Wybrany fundusz ───────────────────────────────────────────────────────────
fund = all_funds[selected_code]
fund_txns = transactions_df[transactions_df["fund_code"] == selected_code]

latest_price, latest_date = get_latest_price(fund["stooq_ticker"])
summary = get_portfolio_summary(fund_txns, latest_price)

# Udział % w portfelu — sumujemy aktualne wartości wszystkich posiadanych funduszy
total_portfolio_value = 0.0
for code in held_codes:
    f = all_funds.get(code)
    if f and f["stooq_ticker"]:
        p, _ = get_latest_price(f["stooq_ticker"])
        s = get_portfolio_summary(transactions_df[transactions_df["fund_code"] == code], p)
        total_portfolio_value += s["current_value"]

fund_pct_of_wallet = (
    (summary["current_value"] / total_portfolio_value * 100) if total_portfolio_value > 0 else 0.0
)

# ── Tytuł ─────────────────────────────────────────────────────────────────────
st.title(f"🏦 {fund['name']}")
st.markdown(f"""
**Kod:** `{fund['code']}` | **Ticker:** `{fund['stooq_ticker']}` | **Ostatnia wycena:** {latest_price:.2f} PLN ({latest_date})
""")

st.markdown("""
Szczegółowa analiza wybranego funduszu z portfela. Poniżej znajdziesz wykresy, metryki ryzyka i porównanie z benchmarkiem.
""")

st.divider()

# ── 4 metryki ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="Udział w portfelu",
    value=f"{fund_pct_of_wallet:.1f}%",
    help="Procentowy udział aktualnej wartości funduszu w całym portfelu"
)
col2.metric(
    label="Zainwestowano",
    value=f"{summary['total_invested']:,.2f} PLN"
)
col3.metric(
    label="Zysk / Strata",
    value=f"{summary['profit_pln']:,.2f} PLN",
    delta=f"{summary['profit_pct']:.2f}%"
)
col4.metric(
    label="Śr. cena zakupu",
    value=f"{summary['avg_buy_price']:.2f} PLN",
    help=f"Aktualna cena: {latest_price:.2f} PLN"
)

st.divider()

# ── Przełącznik okresu ────────────────────────────────────────────────────────
period = st.radio(
    "Okres",
    options=["1M", "3M", "6M", "1Y", "2Y", "5Y", "MAX"],
    index=3,
    horizontal=True
)

prices_df = get_price_history(fund["stooq_ticker"], period=period)

# ── Wykres 1: Cena funduszu z transakcjami ────────────────────────────────────
st.subheader("Cena funduszu i transakcje")

if not prices_df.empty:
    buy_txns = fund_txns[fund_txns["type"] == "BUY"].copy()
    buy_txns["date"] = pd.to_datetime(buy_txns["date"])
    sell_txns = fund_txns[fund_txns["type"] == "SELL"].copy()
    sell_txns["date"] = pd.to_datetime(sell_txns["date"])

    period_start = prices_df["date"].min()
    buy_in_period = buy_txns[buy_txns["date"] >= period_start]
    sell_in_period = sell_txns[sell_txns["date"] >= period_start]

    fig1 = go.Figure()

    fig1.add_trace(go.Scatter(
        x=prices_df["date"],
        y=prices_df["price"],
        name="Cena",
        line=dict(color="#2E75B6", width=2)
    ))

    if not buy_in_period.empty:
        fig1.add_trace(go.Scatter(
            x=buy_in_period["date"],
            y=buy_in_period["price_per_unit"],
            mode="markers",
            name="Zakup",
            marker=dict(
                color="#3B6D11",
                size=11,
                symbol="triangle-up",
                line=dict(color="white", width=1.5)
            ),
            customdata=np.column_stack([
                buy_in_period["units"].values,
                buy_in_period["total_value"].values
            ]),
            hovertemplate=(
                "<b>Zakup</b><br>"
                "Data: %{x}<br>"
                "Cena: %{y:.2f} PLN<br>"
                "Jednostki: %{customdata[0]:.3f}<br>"
                "Wartość: %{customdata[1]:,.2f} PLN"
                "<extra></extra>"
            )
        ))

    if not sell_in_period.empty:
        fig1.add_trace(go.Scatter(
            x=sell_in_period["date"],
            y=sell_in_period["price_per_unit"],
            mode="markers",
            name="Sprzedaż",
            marker=dict(
                color="#A32D2D",
                size=11,
                symbol="triangle-down",
                line=dict(color="white", width=1.5)
            ),
            customdata=np.column_stack([
                sell_in_period["units"].values,
                sell_in_period["total_value"].values
            ]),
            hovertemplate=(
                "<b>Sprzedaż</b><br>"
                "Data: %{x}<br>"
                "Cena: %{y:.2f} PLN<br>"
                "Jednostki: %{customdata[0]:.3f}<br>"
                "Wartość: %{customdata[1]:,.2f} PLN"
                "<extra></extra>"
            )
        ))

    fig1.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis_title="Cena (PLN)"
    )

    st.plotly_chart(fig1, use_container_width=True)
else:
    st.info("Brak danych cenowych dla tego funduszu.")

st.divider()

# ── Wykres 2: Porównanie do WIG20 ─────────────────────────────────────────────
st.subheader("Porównanie do WIG20")

wig20_df = get_price_history("wig20", period=period)

if not prices_df.empty and not wig20_df.empty:
    fund_norm = prices_df.copy()
    wig20_norm = wig20_df.copy()

    fund_base = fund_norm.iloc[0]["price"]
    wig20_base = wig20_norm.iloc[0]["price"]

    fund_norm["normalized"] = fund_norm["price"] / fund_base * 100
    wig20_norm["normalized"] = wig20_norm["price"] / wig20_base * 100

    fund_end = fund_norm.iloc[-1]["normalized"]
    wig20_end = wig20_norm.iloc[-1]["normalized"]
    fund_vs_wig = fund_end - wig20_end

    wig20_norm["mean20"] = wig20_norm["normalized"].rolling(window=20, min_periods=1).mean()

    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(
        x=wig20_norm["date"],
        y=wig20_norm["normalized"],
        name="WIG20",
        line=dict(color="#BBBBBB", width=1.5, dash="dot"),
        opacity=0.6
    ))

    fig2.add_trace(go.Scatter(
        x=wig20_norm["date"],
        y=wig20_norm["mean20"],
        name="WIG20 (śr. 20 sesji)",
        line=dict(color="#888888", width=2)
    ))

    fig2.add_trace(go.Scatter(
        x=fund_norm["date"],
        y=fund_norm["normalized"],
        name=fund["name"],
        line=dict(color="#2E75B6", width=2)
    ))

    fig2.add_hline(y=100, line_dash="dash", line_color="rgba(0,0,0,0.2)", line_width=1)

    fig2.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis_title="Wynik (baza = 100)",
        yaxis_tickformat=".1f"
    )

    st.plotly_chart(fig2, use_container_width=True)

    delta_color = "normal" if fund_vs_wig >= 0 else "inverse"
    st.caption(
        f"W wybranym okresie fundusz osiągnął **{fund_end - 100:+.1f}%**, "
        f"WIG20 **{wig20_end - 100:+.1f}%** — "
        f"różnica: **{fund_vs_wig:+.1f} pp**"
    )
else:
    st.info("Brak danych do porównania z WIG20.")

st.divider()

# ── Wykres 3: Drawdown ────────────────────────────────────────────────────────
st.subheader("Spadek wyceny od szczytu (Drawdown)")

if not prices_df.empty and len(prices_df) > 1:
    running_max = prices_df["price"].cummax()
    drawdown_pct = (prices_df["price"] - running_max) / running_max * 100

    fig3 = go.Figure()

    fig3.add_trace(go.Scatter(
        x=prices_df["date"],
        y=drawdown_pct,
        name="Drawdown",
        line=dict(color="#A32D2D", width=1.5),
        fill="tozeroy",
        fillcolor="rgba(163, 45, 45, 0.12)",
        hovertemplate="Data: %{x}<br>Drawdown: %{y:.2f}%<extra></extra>"
    ))

    fig3.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis_title="Drawdown (%)",
        yaxis_tickformat=".1f"
    )

    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Niewystarczająca ilość danych do wykresu drawdown.")

st.divider()

# ── Metryki ryzyka ────────────────────────────────────────────────────────────
st.subheader("Metryki ryzyka")

if not prices_df.empty and len(prices_df) > 2:
    daily_returns = prices_df["price"].pct_change().dropna()

    # Zmienność — annualizowane odchylenie standardowe
    volatility = daily_returns.std() * (252 ** 0.5) * 100

    # Max Drawdown
    running_max_r = prices_df["price"].cummax()
    drawdown_series = (prices_df["price"] - running_max_r) / running_max_r * 100
    max_dd = drawdown_series.min()

    # Sharpe Ratio — stopa wolna od ryzyka ≈ 5.25% (NBP)
    risk_free_daily = 0.0525 / 252
    excess_returns = daily_returns - risk_free_daily
    sharpe = (
        (excess_returns.mean() / daily_returns.std()) * (252 ** 0.5)
        if daily_returns.std() > 0 else 0.0
    )

    # Downside Deviation — annualizowane odch. std. ujemnych zwrotów
    negative_returns = daily_returns[daily_returns < 0]
    downside_dev = (
        negative_returns.std() * (252 ** 0.5) * 100
        if len(negative_returns) > 1 else 0.0
    )

    rc1, rc2, rc3, rc4 = st.columns(4)

    rc1.metric(
        label="Zmienność (ann.)",
        value=f"{volatility:.2f}%",
        help="Odchylenie standardowe dziennych stóp zwrotu annualizowane (× √252)"
    )
    rc2.metric(
        label="Max Spadek wyceny",
        value=f"{max_dd:.2f}%",
        help="Maksymalny szczytowo-dolny spadek ceny w wybranym okresie"
    )
    rc3.metric(
        label="Współczynnik Sharpe'a",
        value=f"{sharpe:.2f}",
        help="Nadwyżka zwrotu ponad stopę wolną od ryzyka (5.25% NBP) podzielona przez zmienność"
    )
    rc4.metric(
        label="Downside Deviation",
        value=f"{downside_dev:.2f}%",
        help="Niskie odchylenie w dół oznacza, że stopy zwrotu z inwestycji rzadko spadają"
    )
else:
    st.info("Niewystarczająca ilość danych do obliczenia metryk ryzyka.")
