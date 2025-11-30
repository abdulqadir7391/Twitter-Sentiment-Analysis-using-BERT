import re
import html
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load .env file
load_dotenv()

ALERT_KEYWORDS = {"hate", "abuse", "kill", "rape", "attack", "terror"}  # simple heuristic

def preprocess_tweet(text: str) -> str:
    if not text:
        return ""
    # unescape html, remove urls, mentions, keep hashtags optional
    text = html.unescape(text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\S+", "", text)
    text = re.sub(r"#", "", text)  # remove hash symbol but keep words
    text = re.sub(r"[^\w\s]", " ", text)  # remove punctuation
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()

def contains_abusive(text: str) -> bool:
    txt = text.lower()
    for kw in ALERT_KEYWORDS:
        if kw in txt:
            return True
    return False

def send_email_alert(subject: str, body: str):
    # env vars
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    ALERT_EMAIL = os.getenv("ALERT_EMAIL")
    
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and ALERT_EMAIL):
        print("SMTP not configured; can't send alert.")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = ALERT_EMAIL
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
        print("Alert email sent.")
        return True
    except Exception as e:
        print("Failed to send email:", e)
        return False