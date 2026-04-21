import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import date

from backend.database.db import init_db, get_connection
from backend.services.transactions import get_transactions, add_transaction, delete_transaction
from backend.services.prices import get_latest_price
from backend.services.portfolio import get_portfolio_summary

# ── Init ──────────────────────────────────────────────────────────────────────
init_db()

st.set_page_config(page_title="Transakcje — MarketSTI Monitor", page_icon="📋", layout="wide")
st.title("📋 Transakcje")

# ── Pobierz dane ──────────────────────────────────────────────────────────────
transactions_df = get_transactions("default")
latest_price, latest_date = get_latest_price("3965.n")

# ── Metryki podsumowujące ─────────────────────────────────────────────────────
if not transactions_df.empty:
    summary = get_portfolio_summary(transactions_df, latest_price)
    #count of different fund codes in transactions_df which status is BUY
    fund_types_amount = transactions_df[transactions_df["type"] == "BUY"]["fund_code"].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Liczba transakcji", len(transactions_df))
    col2.metric("Liczba posiadanych funduszy", fund_types_amount)
    col3.metric("Zainwestowano", f"{summary['total_invested']:,.2f} PLN")
    col4.metric(
        "Zysk / Strata",
        f"{summary['profit_pln']:,.2f} PLN",
        delta=f"{summary['profit_pct']:.2f}%"
    )

st.divider()

# ── Dwa panele ────────────────────────────────────────────────────────────────
col_form, col_table = st.columns([1, 1.4], gap="large")

# ══════════════════════════════════════════════════════════
# LEWA STRONA — formularz dodawania
# ══════════════════════════════════════════════════════════
with col_form:
    st.subheader("Dodaj transakcję")

    # Pobierz listę funduszy z bazy
    conn = get_connection()
    funds_df = pd.read_sql("SELECT code, name FROM funds ORDER BY name", conn)
    conn.close()

    fund_options = {
        f"{row['name']} ({row['code']})": row['code']
        for _, row in funds_df.iterrows()
    }

    with st.form("add_transaction_form", clear_on_submit=True):

        selected_fund_label = st.selectbox(
            "Fundusz",
            options=list(fund_options.keys())
        )
        selected_fund_code = fund_options[selected_fund_label]

        transaction_type = st.radio(
            "Typ transakcji",
            options=["BUY", "SELL"],
            horizontal=True
        )

        col_date, col_units = st.columns(2)
        with col_date:
            transaction_date = st.date_input(
                "Data",
                value=date.today(),
                max_value=date.today()
            )
        with col_units:
            units = st.number_input(
                "Liczba jednostek",
                min_value=0.001,
                step=0.001,
                format="%.3f"
            )

        col_price, col_notes = st.columns(2)
        with col_price:
            price_per_unit = st.number_input(
                "Cena jednostki (PLN)",
                min_value=0.01,
                step=0.01,
                format="%.2f",
                help=f"Ostatnia wycena: {latest_price:.2f} PLN ({latest_date})"
            )
        with col_notes:
            notes = st.text_input(
                "Notatka (opcjonalnie)",
                placeholder="np. pierwsza wpłata"
            )

        # Podgląd wartości transakcji
        total_preview = units * price_per_unit
        st.info(f"Wartość transakcji: **{total_preview:,.2f} PLN**")

        submitted = st.form_submit_button(
            "💾 Zapisz transakcję",
            use_container_width=True
        )

        if submitted:
            # Walidacja
            if units <= 0:
                st.error("Liczba jednostek musi być większa niż 0.")
            elif price_per_unit <= 0:
                st.error("Cena jednostki musi być większa niż 0.")
            elif transaction_type == "SELL":
                # Sprawdź czy masz wystarczająco jednostek do sprzedaży
                current_txns = get_transactions("default")
                if not current_txns.empty:
                    bought = current_txns[current_txns["type"] == "BUY"]["units"].sum()
                    sold   = current_txns[current_txns["type"] == "SELL"]["units"].sum()
                    available = bought - sold
                else:
                    available = 0.0

                if units > available:
                    st.error(f"Nie możesz sprzedać {units:.3f} jednostek — posiadasz tylko {available:.3f}.")
                else:
                    add_transaction(
                        user_id="default",
                        fund_code=selected_fund_code,
                        type=transaction_type,
                        date=str(transaction_date),
                        units=units,
                        price_per_unit=price_per_unit,
                        notes=notes
                    )
                    st.success(f"Dodano: {transaction_type} {units:.3f} jedn. @ {price_per_unit:.2f} PLN")
                    st.rerun()
            else:
                add_transaction(
                    user_id="default",
                    fund_code=selected_fund_code,
                    type=transaction_type,
                    date=str(transaction_date),
                    units=units,
                    price_per_unit=price_per_unit,
                    notes=notes
                )
                st.success(f"Dodano: {transaction_type} {units:.3f} jedn. @ {price_per_unit:.2f} PLN")
                st.rerun()

# ══════════════════════════════════════════════════════════
# PRAWA STRONA — tabela transakcji
# ══════════════════════════════════════════════════════════
with col_table:

    header_col, export_col = st.columns([3, 1])
    with header_col:
        st.subheader("Historia transakcji")
    with export_col:
        if not transactions_df.empty:
            csv = transactions_df.to_csv(index=False)
            st.download_button(
                label="📥 Eksportuj CSV",
                data=csv,
                file_name="fund_tracker_backup.csv",
                mime="text/csv",
                use_container_width=True
            )

    if transactions_df.empty:
        st.info("Brak transakcji. Dodaj pierwszą używając formularza po lewej.")
    else:
        # Przygotuj czytelną tabelę do wyświetlenia
        display_df = transactions_df[["id", "date", "fund_code", "type", "units", "price_per_unit", "total_value", "notes"]].copy()
        display_df.columns = ["ID", "Data", "Fundusz", "Typ", "Jednostki", "Cena (PLN)", "Wartość (PLN)", "Notatka"]
        display_df["Jednostki"]    = display_df["Jednostki"].map("{:.3f}".format)
        display_df["Cena (PLN)"]   = display_df["Cena (PLN)"].map("{:.2f}".format)
        display_df["Wartość (PLN)"] = display_df["Wartość (PLN)"].map("{:,.2f}".format)
        display_df["Notatka"]      = display_df["Notatka"].fillna("")

        # Kolorowanie BUY/SELL
        def color_type(val):
            if val == "BUY":
                return "background-color: #EAF3DE; color: #3B6D11; font-weight: 500;"
            elif val == "SELL":
                return "background-color: #FCEBEB; color: #A32D2D; font-weight: 500;"
            return ""

        styled = display_df.drop(columns=["ID"]).style.map(color_type, subset=["Typ"])

        st.dataframe(styled, use_container_width=True, hide_index=True)

        # ── Usuwanie transakcji ───────────────────────────────────────────────
        st.divider()
        with st.expander("🗑️ Usuń transakcję"):
            st.caption("Wybierz ID transakcji którą chcesz usunąć. Operacja jest nieodwracalna.")

            id_to_delete = st.selectbox(
                "ID transakcji",
                options=transactions_df["id"].tolist(),
                format_func=lambda x: (
                    f"ID {x} — "
                    + transactions_df[transactions_df['id'] == x]['type'].values[0]
                    + " "
                    + str(transactions_df[transactions_df['id'] == x]['units'].values[0])
                    + " jedn. @ "
                    + str(transactions_df[transactions_df['id'] == x]['price_per_unit'].values[0])
                    + " PLN ("
                    + str(transactions_df[transactions_df['id'] == x]['date'].values[0])
                    + ")"
                )
            )

            if st.button("Usuń transakcję", type="secondary", use_container_width=True):
                delete_transaction(id_to_delete)
                st.warning(f"Transakcja ID {id_to_delete} została usunięta.")
                st.rerun()