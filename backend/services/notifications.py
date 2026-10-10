import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.database.db import get_connection


def get_user_alerts(user_id: str) -> list[dict]:
    """Get all price alerts for a user"""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT 
            pa.id, pa.fund_code, pa.alert_type, pa.threshold_price,
            pa.drawback_percent, pa.email, pa.is_active, pa.created_at,
            f.name as fund_name
        FROM price_alerts pa
        JOIN funds f ON pa.fund_code = f.code
        WHERE pa.user_id = ?
        ORDER BY pa.created_at DESC
        """,
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_alert(user_id: str, fund_code: str, alert_type: str, 
                email: str, threshold_price: float = None, drawback_percent: float = None) -> bool:
    """Create a new price alert"""
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO price_alerts 
            (user_id, fund_code, alert_type, threshold_price, drawback_percent, email, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (user_id, fund_code, alert_type, threshold_price, drawback_percent, email)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating alert: {e}")
        conn.close()
        return False


def delete_alert(alert_id: int) -> bool:
    """Delete a price alert"""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM price_alerts WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting alert: {e}")
        conn.close()
        return False


def send_notification_email(email_to: str, fund_name: str, alert_type: str, 
                           current_price: float, threshold: float = None, drawback: float = None) -> bool:
    """
    Send email notification (demo mode - simulates sending)
    In production, use real SMTP credentials
    """
    try:
        # For demo purposes, we'll just log the email that would be sent
        subject = f"🔔 MarketSTI Monitor - Powiadomienie o funduszu {fund_name}"
        
        if alert_type == "BELOW":
            body = f"""
Cześć!

Fundusz <b>{fund_name}</b> osiągnął cenę poniżej ustawionego progu!

📊 Aktualna cena: {current_price:.2f} PLN
🎯 Próg alert: {threshold:.2f} PLN

To może być dobry moment na zakup! 🚀

---
MarketSTI Monitor
            """
        elif alert_type == "ABOVE":
            body = f"""
Cześć!

Fundusz <b>{fund_name}</b> osiągnął cenę powyżej ustawionego progu!

📊 Aktualna cena: {current_price:.2f} PLN
🎯 Próg alert: {threshold:.2f} PLN

Możesz rozważyć sprzedaż! 📈

---
MarketSTI Monitor
            """
        else:  # DRAWBACK
            body = f"""
Cześć!

Fundusz <b>{fund_name}</b> zanotował znaczący spadek!

📊 Aktualna cena: {current_price:.2f} PLN
📉 Spadek: {drawback:.1f}% od średniej

Historycznie to może być okazja do kupna! 💡

---
MarketSTI Monitor
            """
        
        # Demo: write to file instead of sending actual email
        with open("data/notifications_log.txt", "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"TO: {email_to}\n")
            f.write(f"SUBJECT: {subject}\n")
            f.write(f"BODY:\n{body}\n")
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_demo_notification(email_to: str, fund_name: str, alert_type: str,
                          current_price: float, threshold: float = None, drawback: float = None):
    """Send demo notification immediately"""
    return send_notification_email(email_to, fund_name, alert_type, current_price, threshold, drawback)
