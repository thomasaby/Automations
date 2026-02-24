import os
import imaplib
import email
import requests
from datetime import datetime

# --- Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
MODEL_ID = "llama-3.3-70b-versatile"

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_abbotsford_weather():
    """Fetches real-time Sunday forecast for Abbotsford, BC."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 49.0504,
        "longitude": -122.3045,
        "daily": "temperature_2m_max,temperature_2m_min,weathercode",
        "timezone": "America/Los_Angeles",
        "forecast_days": 7
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        # Index 0 is today, but since we run Sunday, we'll grab the first available
        max_temp = data['daily']['temperature_2m_max'][0]
        min_temp = data['daily']['temperature_2m_min'][0]
        return f"High of {max_temp}°C, Low of {min_temp}°C with typical Fraser Valley conditions."
    except Exception as e:
        print(f"Weather Error: {e}")
        return "Weather data unavailable."

def get_latest_newsletter():
    """Retrieves the newsletter body from Gmail."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")
        status, messages = mail.search(None, '(SUBJECT "Downes Road Weekly Newsletter")')
        if status != "OK" or not messages[0]:
            return None
        
        latest_id = messages[0].split()[-1]
        res, msg_data = mail.fetch(latest_id, "(RFC822)")
        for part in msg_data:
            if isinstance(part, tuple):
                msg = email.message_from_bytes(part[1])
                if msg.is_multipart():
                    for subpart in msg.walk():
                        if subpart.get_content_type() == "text/plain":
                            return subpart.get_payload(decode=True).decode()
                else:
                    return msg.get_payload(decode=True).decode()
        mail.logout()
    except Exception as e:
        print(f"Gmail Error: {e}")
    return None

def summarize_with_groq(newsletter_text, weather_text):
    """Summarizes using Groq and the external prompt template."""
    try:
        with open("prompt.txt", "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        return "Error: prompt.txt not found."

    # Injecting both the newsletter and the REAL weather data
    full_prompt = template.format(
        newsletter_content=newsletter_text,
        weather_info=weather_text
    )

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.2
    }
    
    try:
        response = requests.post(GROQ_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Inference Error: {e}"

def send_telegram(msg):
    """Sends the summary to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": msg, 
        "parse_mode": "Markdown"
    })

def main():
    print("🚀 SundayPrep Started...")
    weather = get_abbotsford_weather()
    content = get_latest_newsletter()
    
    if content:
        summary = summarize_with_groq(content, weather)
        send_telegram(summary)
        print("✅ Telegram notification sent!")
    else:
        print("❌ No newsletter found.")

if __name__ == "__main__":
    main()