import os
import imaplib
import email
from google import genai
import requests

# Configuration from Environment Variables
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")  # Mapped to GMAIL_APP_PASSWORD in GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_latest_newsletter():
    """Retrieves the body of the latest Downes Road newsletter."""
    try:
        if not GMAIL_USER or not GMAIL_PASS:
            print("Error: Gmail credentials missing.")
            return None

        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")

        # Search for the exact subject line
        status, messages = mail.search(None, '(SUBJECT "Downes Road Weekly Newsletter")')
        if status != "OK" or not messages[0]:
            print("Newsletter not found in Inbox.")
            return None

        # Fetch the most recent message ID
        latest_id = messages[0].split()[-1]
        res, msg_data = mail.fetch(latest_id, "(RFC822)")
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            return part.get_payload(decode=True).decode()
                else:
                    return msg.get_payload(decode=True).decode()
        
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"Gmail Connection Error: {e}")
    return None

def send_telegram_chunks(text):
    """Splits text into chunks to respect Telegram's 4096 char limit."""
    if not text:
        return

    MAX_LEN = 4000 
    # Create chunks of 4000 characters
    chunks = [text[i:i+MAX_LEN] for i in range(0, len(text), MAX_LEN)]
    
    print(f"Sending {len(chunks)} message(s) to Telegram...")
    
    for i, chunk in enumerate(chunks):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        header = f"📦 *SundayPrep Raw Content (Part {i+1}/{len(chunks)})*\n\n"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": header + chunk,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"Telegram failed on part {i+1}: {e}")

def main():
    print("Step 1: Fetching Newsletter...")
    raw_content = get_latest_newsletter()
    
    if raw_content:
        print(f"Step 2: Sending raw content ({len(raw_content)} characters)...")
        send_telegram_chunks(raw_content)
        print("Success! Check your Telegram.")
    else:
        print("Workflow stopped: No content to send.")

if __name__ == "__main__":
    main()