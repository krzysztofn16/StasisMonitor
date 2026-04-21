import streamlit as st
from backend.services.users import register_user, login_user, user_exists

def get_current_user() -> str | None:
    """Zwraca aktualnie zalogowanego uzytkownika lub None"""
    return st.session_state.get("user_id", None)

def logout():
    """Wylogowuje użytkownika"""
    st.session_state.pop("user_id", None)
    st.rerun()

def show_auth_page():
    """
    Wyświetla ekran logownaie/rejestracji
    Wywołanie gdy zytkownik nie jest zalogowany
    """
    st.title("📊 MarketSTI Monitor")
    st.markdown("Śledź swoje inwestycje w funduszach TFI.")
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col2:

        tab_login, tab_register = st.tabs(["Wejdź", "Nowe konto"])

        # ── Logowanie ─────────────────────────────────────────────
        with tab_login:
            st.markdown(" ")
            with st.form("login_form"):
                username = st.text_input(
                    "Nick",
                    placeholder="np. marek123",
                    max_chars=30
                )
                pin = st.text_input(
                    "PIN (4 cyfry)",
                    type="password",
                    max_chars=4,
                    placeholder="••••"
                )
                login_submitted = st.form_submit_button(
                    "Wejdź ->",
                    use_container_width=True
                )

            if login_submitted:
                if not username or not pin:
                    st.error("Wypełnij nick i PIN.")
                else:
                    success,msg = login_user(username, pin)
                    if success:
                        st.session_state["user_id"] = username.strip().lower()
                        st.rerun()
                    else:
                        st.error(msg)
        
        # ── Rejestracja ─────────────────────────────────────────────
        with tab_register:
            st.markdown(" ")
            with st.form("register_form"):
                new_username = st.text_input(
                    "Nick",
                    placeholder="np. marek123",
                    max_chars=30
                )
                new_pin = st.text_input(
                    "PIN (4 cyfry)",
                    type="password",
                    max_chars=4,
                    placeholder="••••"
                )
                new_pin_confirm = st.text_input(
                    "Powtórz PIN",
                    type="password",
                    max_chars=4,
                    placeholder="••••"
                )
                register_submitted = st.form_submit_button(
                    "Utwórz konto ->",
                    use_container_width=True
                )

            if register_submitted:
                if not new_username or not new_pin:
                    st.error("Wypełnij wszystkie pola.")
                elif new_pin != new_pin_confirm:
                    st.error("PINy się nie zgadzają")
                else:
                    success,  msg = register_user(new_username, new_pin)
                    if success:
                        st.session_state["user_id"] = new_username.strip().lower()
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)