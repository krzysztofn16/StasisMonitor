import streamlit as st
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

import sys
import os

# Dodaj główny folder projektu do Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.db import init_db, get_all_funds
from backend.services.transactions import get_transactions
from backend.services.prices import get_price_history, get_latest_price
from backend.services.portfolio import get_portfolio_summary, get_portfolio_history
from backend.services.auth import get_current_user, show_auth_page, logout

# ── Inicjalizacja bazy przy każdym starcie ────────────────────────────────────
init_db()

# ── Konfiguracja strony ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="MarketSTI Monitor",
    page_icon="📊",
    layout="wide"
)

# ── Auth — jeśli nie zalogowany pokaż ekran logowania ────────────────────────
user_id = get_current_user()
if user_id is None:
    show_auth_page()
    st.stop()

# ── Sidebar — info o użytkowniku ──────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"👤 **{user_id}**")
    if st.button("wyloguj", use_container_width=True):
        logout()
    st.divider()
    st.markdown("[📝 Prześlij feedback](https://forms.gle/uDh9U5EAzcZ2s3yP6)")
    st.markdown("[☕ Postaw kawę zeby to rozwijać po godzinach 😏](https://buymeacoffee.com/monitorsti)")

st.title("📊 MarketSTI Monitor")

# ── Pobierz dane ──────────────────────────────────────────────────────────────
transactions_df = get_transactions(user_id)

# ── Obsługa pustej bazy ───────────────────────────────────────────────────────
if transactions_df.empty:
    st.info("Nie masz jeszcze żadnych transakcji. Przejdź do strony **Transakcje** żeby dodać pierwszą, albo zaimportuj plik CSV.")
    st.stop()

# ── Oblicz statystyki dla każdego posiadanego funduszu ───────────────────────
all_funds = {f["code"]: f for f in get_all_funds()}
held_fund_codes = transactions_df["fund_code"].unique().tolist()
held_funds = [all_funds[c] for c in held_fund_codes if c in all_funds]

fund_summaries = []
total_current_value = total_invested = total_profit_pln = 0.0

for fund in held_funds:
    fund_txns = transactions_df[transactions_df["fund_code"] == fund["code"]]
    latest_price, latest_date = get_latest_price(fund["stooq_ticker"])
    s = get_portfolio_summary(fund_txns, latest_price)
    total_current_value += s["current_value"]
    total_invested      += s["total_invested"]
    total_profit_pln    += s["profit_pln"]
    fund_summaries.append({"fund": fund, "summary": s,
                           "latest_price": latest_price, "latest_date": latest_date})

total_profit_pct = (total_profit_pln / total_invested * 100) if total_invested else 0.0

# ── 4 metryki ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

col1.metric(label="Wartość portfela",    value=f"{total_current_value:,.2f} PLN")
col2.metric(label="Zysk / Strata",       value=f"{total_profit_pln:,.2f} PLN",
            delta=f"{total_profit_pct:.2f}%")
col3.metric(label="Zainwestowano",       value=f"{total_invested:,.2f} PLN")
col4.metric(label="Funduszy w portfelu", value=len(held_funds))

st.divider()

# ── Wykres z przełącznikiem okresu ────────────────────────────────────────────
st.subheader("Wartość portfela w czasie")

period = st.radio(
    label="Okres",
    options=["1M", "3M", "6M", "1Y", "2Y", "5Y", "MAX"],
    index=1,          # domyślnie 3M
    horizontal=True
)

history_frames = []
for fund in held_funds:
    fund_txns = transactions_df[transactions_df["fund_code"] == fund["code"]]
    prices_df = get_price_history(fund["stooq_ticker"], period=period)
    h = get_portfolio_history(fund_txns, prices_df)
    if not h.empty:
        history_frames.append(h.set_index("date"))

if history_frames:
    combined = history_frames[0]
    for frame in history_frames[1:]:
        combined = combined.add(frame, fill_value=0)
    history_df = combined.reset_index()
else:
    history_df = pd.DataFrame(columns=["date", "value", "invested"])

if not history_df.empty:
    fig = go.Figure()

    # Linia — zainwestowano (baseline)
    fig.add_trace(go.Scatter(
        x=history_df["date"],
        y=history_df["invested"],
        name="Zainwestowano",
        line=dict(color="#888888", width=2, dash="dot")
    ))

    # Linia — wartość portfela
    fig.add_trace(go.Scatter(
        x=history_df["date"],
        y=history_df["value"],
        name="Wartość portfela",
        line=dict(color="#2E75B6", width=2),
        fill="tonexty",
        fillcolor="rgba(39, 174, 96, 0.1)"
    ))

    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=0, t=30, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Tabela podsumowania funduszu ──────────────────────────────────────────────
st.subheader("Podsumowanie")

rows = []
for item in fund_summaries:
    s = item["summary"]
    rows.append({
        "Fundusz":         item["fund"]["name"],
        "Jednostki":       f"{s['units_held']:.4f}",
        "Śr. cena zakupu": f"{s['avg_buy_price']:.2f} PLN",
        "Aktualna cena":   f"{item['latest_price']:.2f} PLN",
        "Wartość":         f"{s['current_value']:,.2f} PLN",
        "Zysk / Strata":   f"{s['profit_pln']:,.2f} PLN ({s['profit_pct']:.2f}%)",
    })
summary_table = pd.DataFrame(rows)

st.dataframe(summary_table, use_container_width=True, hide_index=True)

# ── Eksport CSV ───────────────────────────────────────────────────────────────
st.divider()

csv = transactions_df.to_csv(index=False)
st.download_button(
    label="📥 Eksportuj transakcje CSV",
    data=csv,
    file_name="fund_tracker_backup.csv",
    mime="text/csv"
)