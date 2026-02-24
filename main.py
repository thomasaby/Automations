import os
import imaplib
import email
import requests

# Groq API Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
# Using the incredibly fast and capable Llama 3.3 70B model
MODEL_ID = "llama-3.3-70b-versatile"

# Personal Config
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_latest_newsletter():
    """Retrieves the plain text body of the newsletter from Gmail."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")
        
        status, messages = mail.search(None, '(SUBJECT "Downes Road Weekly Newsletter")')
        if status != "OK" or not messages[0]:
            print("Newsletter not found.")
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
        print(f"Gmail Connection Error: {e}")
    return None

def summarize_with_groq(text):
    """Summarizes using Groq's lightning-fast LPU inference."""
    if not text: return "No content."
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_ID,
        "messages": [
            {
                "role": "system", 
                "content": "You are a church assistant. Summarize this newsletter in exactly 3 concise sentences. Explicitly state the main scripture reference and the primary sermon points."
            },
            {
                "role": "user", 
                "content": text
            }
        ],
        "temperature": 0.3
    }
    
    try:
        response = requests.post(ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Groq API Error: {e}")
        return "AI Summary unavailable."

def send_telegram(msg):
    """Dispatches the final summary to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": f"{msg}", 
        "parse_mode": "Markdown"
    }
    requests.post(url, json=data)

def main():
    print("Starting SundayPrep with Groq LPU Engine...")
    content = get_latest_newsletter()
    if content:
        print(f"Summarizing via {MODEL_ID}...")
        summary = summarize_with_groq(content)
        print("Sending to Telegram...")
        send_telegram(summary)
        print("Workflow complete!")
    else:
        print("No newsletter found in Gmail.")

if __name__ == "__main__":
    main()