import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd

from backend.database.db import init_db, get_connection, get_all_funds
from backend.services.transactions import get_transactions, add_transaction
from backend.services.auth import get_current_user, show_auth_page, logout

# ── Init ──────────────────────────────────────────────────────────────────────
init_db()

user_id = get_current_user()
if user_id is None:
    show_auth_page()
    st.stop()

st.set_page_config(page_title="Import — MarketSTI Monitor", page_icon="📂", layout="wide")
st.title("📂 Import transakcji")

# ── Sidebar — info o użytkowniku ──────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"👤 **{user_id}**")
    if st.button("Wyloguj", use_container_width=True):
        logout()
    st.divider()
    st.markdown("[📝 Prześlij feedback](https://forms.google.com/))")
    st.markdown("[☕ Postaw kawę](https://buymeacoffee.com/)")

# ── Metryki podsumowujące ─────────────────────────────────────────────────────
transactions_df = get_transactions(user_id) #get_transactions("default")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Transakcji w bazie", len(transactions_df))
col2.metric("Funduszy w portfelu", transactions_df["fund_code"].nunique() if not transactions_df.empty else 0)
col3.metric("Obsługiwane formaty", "CSV, Excel")
col4.metric("Wymagane kolumny", "5")

st.divider()

# ══════════════════════════════════════════════════════════
# INSTRUKCJA
# ══════════════════════════════════════════════════════════
st.subheader("Instrukcja")

col_req, col_opt = st.columns(2)

with col_req:
    st.markdown("""
**Wymagane kolumny:**

| Kolumna | Format | Przykład |
|---|---|---|
| `date` | YYYY-MM-DD | 2024-03-15 |
| `fund_code` | tekst | (kod z tabeli poniżej) |
| `type` | BUY lub SELL | BUY |
| `units` | liczba | 10.5 |
| `price_per_unit` | liczba | 245.20 |
""")

with col_opt:
    st.markdown("""
**Opcjonalne kolumny:**

| Kolumna | Opis |
|---|---|
| `notes` | dowolna notatka |

**Znane kody funduszy:**
""")
    conn = get_connection()
    funds_df = pd.read_sql("SELECT code, name FROM funds ORDER BY name", conn)
    conn.close()

    if funds_df.empty:
        st.info("Brak funduszy w bazie.")
    else:
        st.dataframe(
            funds_df.rename(columns={"code": "Kod", "name": "Nazwa"}),
            use_container_width=True,
            hide_index=True
        )

_fund_codes = [f["code"] for f in get_all_funds()]
_c0 = _fund_codes[0] if _fund_codes else "FUNDXX"
_c1 = _fund_codes[1] if len(_fund_codes) > 1 else _c0

template_csv = f"""date,fund_code,type,units,price_per_unit,notes
2024-03-15,{_c0},BUY,10.5,245.20,pierwsza wpłata
2024-06-01,{_c0},BUY,5.0,251.80,
2024-09-10,{_c1},SELL,2.0,268.40,częściowa sprzedaż
"""

col1, col2, col3 = st.columns(3)
with col2:
    st.download_button(
        label="📄 Pobierz szablon CSV",
        data=template_csv,
        file_name="fund_tracker_template.csv",
        mime="text/csv",
        use_container_width=True
    )

st.divider()

# ══════════════════════════════════════════════════════════
# UPLOAD
# ══════════════════════════════════════════════════════════
st.subheader("Wgraj plik")

uploaded_file = st.file_uploader(
    "Wybierz plik CSV lub Excel",
    type=["csv", "xlsx"],
    help="Plik musi zawierać kolumny: date, fund_code, type, units, price_per_unit"
)

if uploaded_file is not None:

    # ── Wczytaj plik ─────────────────────────────────────────────────────────
    try:
        if uploaded_file.name.endswith(".csv"):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Nie udało się wczytać pliku: {e}")
        st.stop()

    st.caption(f"Wczytano {len(df_raw)} wierszy · {len(df_raw.columns)} kolumn")

    with st.expander("Podgląd wczytanych danych (pierwsze 10 wierszy)", expanded=True):
        st.dataframe(df_raw.head(10), use_container_width=True, hide_index=True)

    st.divider()

    # ── Mapowanie kolumn ──────────────────────────────────────────────────────
    st.subheader("Mapowanie kolumn")
    st.caption("Przypisz kolumny z pliku do pól wymaganych przez aplikację. Kolumny z pasującymi nazwami są dopasowane automatycznie.")

    file_columns = ["— wybierz —"] + list(df_raw.columns)

    def autodetect(target):
        return target if target in df_raw.columns else "— wybierz —"

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        map_date  = st.selectbox("date (wymagane)",            file_columns, index=file_columns.index(autodetect("date")))
        map_fund  = st.selectbox("fund_code (wymagane)",       file_columns, index=file_columns.index(autodetect("fund_code")))
    with col_m2:
        map_type  = st.selectbox("type — BUY/SELL (wymagane)", file_columns, index=file_columns.index(autodetect("type")))
        map_units = st.selectbox("units (wymagane)",            file_columns, index=file_columns.index(autodetect("units")))
    with col_m3:
        map_price = st.selectbox("price_per_unit (wymagane)",  file_columns, index=file_columns.index(autodetect("price_per_unit")))
        map_notes = st.selectbox("notes (opcjonalne)",          file_columns, index=file_columns.index(autodetect("notes")))

    required_mapped = all(
        m != "— wybierz —"
        for m in [map_date, map_fund, map_type, map_units, map_price]
    )

    st.divider()

    # ── Walidacja i podgląd po mapowaniu ─────────────────────────────────────
    if required_mapped:

        df_mapped = pd.DataFrame()
        df_mapped["date"]           = df_raw[map_date].astype(str).str.strip()
        df_mapped["fund_code"]      = df_raw[map_fund].astype(str).str.strip().str.upper()
        df_mapped["type"]           = df_raw[map_type].astype(str).str.strip().str.upper()
        df_mapped["units"]          = pd.to_numeric(df_raw[map_units], errors="coerce")
        df_mapped["price_per_unit"] = pd.to_numeric(df_raw[map_price], errors="coerce")
        df_mapped["notes"]          = df_raw[map_notes].astype(str).str.strip() if map_notes != "— wybierz —" else ""
        df_mapped["total_value"]    = df_mapped["units"] * df_mapped["price_per_unit"]

        # Walidacja
        errors = []

        invalid_dates = df_mapped[~df_mapped["date"].str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)]
        if not invalid_dates.empty:
            errors.append(f"{len(invalid_dates)} wierszy ma nieprawidłowy format daty (wymagany: YYYY-MM-DD)")

        invalid_types = df_mapped[~df_mapped["type"].isin(["BUY", "SELL"])]
        if not invalid_types.empty:
            errors.append(f"{len(invalid_types)} wierszy ma nieprawidłowy typ (wymagany: BUY lub SELL)")

        invalid_units = df_mapped[df_mapped["units"].isna() | (df_mapped["units"] <= 0)]
        if not invalid_units.empty:
            errors.append(f"{len(invalid_units)} wierszy ma nieprawidłową liczbę jednostek")

        invalid_prices = df_mapped[df_mapped["price_per_unit"].isna() | (df_mapped["price_per_unit"] <= 0)]
        if not invalid_prices.empty:
            errors.append(f"{len(invalid_prices)} wierszy ma nieprawidłową cenę")

        conn = get_connection()
        known_funds = pd.read_sql("SELECT code FROM funds", conn)["code"].tolist()
        conn.close()
        unknown_funds = df_mapped[~df_mapped["fund_code"].isin(known_funds)]["fund_code"].unique()
        if len(unknown_funds) > 0:
            errors.append(f"Nieznane kody funduszy: {', '.join(unknown_funds)} — dodaj je najpierw do bazy")

        if errors:
            for err in errors:
                st.error(f"⚠️ {err}")

        else:
            # Wykryj duplikaty
            existing_df = get_transactions(user_id)
            duplicates = 0

            if not existing_df.empty:
                for _, row in df_mapped.iterrows():
                    mask = (
                        (existing_df["fund_code"]      == row["fund_code"]) &
                        (existing_df["type"]           == row["type"])      &
                        (existing_df["date"]           == row["date"])      &
                        (existing_df["units"]          == row["units"])     &
                        (existing_df["price_per_unit"] == row["price_per_unit"])
                    )
                    if mask.any():
                        duplicates += 1

            new_rows = len(df_mapped) - duplicates

            # Metryki importu
            sum_col1, sum_col2, sum_col3 = st.columns(3)
            sum_col1.metric("Wierszy w pliku",       len(df_mapped))
            sum_col2.metric("Nowych transakcji",      new_rows)
            sum_col3.metric("Duplikatów (pomijane)",  duplicates)

            # Podgląd po mapowaniu
            with st.expander("Podgląd po mapowaniu", expanded=True):
                preview = df_mapped[["date", "fund_code", "type", "units", "price_per_unit", "total_value", "notes"]].copy()
                preview.columns = ["Data", "Fundusz", "Typ", "Jednostki", "Cena (PLN)", "Wartość (PLN)", "Notatka"]

                def color_type(val):
                    if val == "BUY":
                        return "background-color: #EAF3DE; color: #3B6D11; font-weight: 500;"
                    elif val == "SELL":
                        return "background-color: #FCEBEB; color: #A32D2D; font-weight: 500;"
                    return ""

                st.dataframe(
                    preview.style.map(color_type, subset=["Typ"]),
                    use_container_width=True,
                    hide_index=True
                )

            # Przycisk importu
            if new_rows == 0:
                st.warning("Wszystkie wiersze z pliku już istnieją w bazie — brak nowych transakcji do dodania.")
            else:
                if st.button(
                    f"📥 Importuj {new_rows} transakcji",
                    type="primary",
                    use_container_width=True
                ):
                    imported = 0
                    skipped  = 0

                    for _, row in df_mapped.iterrows():
                        if not existing_df.empty:
                            mask = (
                                (existing_df["fund_code"]      == row["fund_code"]) &
                                (existing_df["type"]           == row["type"])      &
                                (existing_df["date"]           == row["date"])      &
                                (existing_df["units"]          == row["units"])     &
                                (existing_df["price_per_unit"] == row["price_per_unit"])
                            )
                            if mask.any():
                                skipped += 1
                                continue

                        add_transaction(
                            user_id=user_id,
                            fund_code=row["fund_code"],
                            type=row["type"],
                            date=row["date"],
                            units=float(row["units"]),
                            price_per_unit=float(row["price_per_unit"]),
                            notes=str(row["notes"]) if row["notes"] else ""
                        )
                        imported += 1

                    st.success(f"✅ Zaimportowano {imported} transakcji · Pominięto {skipped} duplikatów")
                    st.rerun()

    else:
        st.info("Przypisz wszystkie wymagane kolumny żeby zobaczyć podgląd i przycisk importu.")