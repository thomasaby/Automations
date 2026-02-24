import os
import imaplib
import email
import requests

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

def summarize_with_ollama(text):
    """Summarizes using the local Ollama server running on the GitHub Action."""
    if not text: return "No content."
    
    # Pointing directly to the local Ollama API
    url = "http://localhost:11434/api/chat"
    
    payload = {
        "model": "llama3.2:1b",
        "messages": [
            {
                "role": "system", 
                "content": "You are a church assistant. Read the newsletter and summarize it in exactly 3 concise sentences. Explicitly state the main scripture reference and the primary sermon points."
            },
            {
                "role": "user", 
                "content": text
            }
        ],
        "stream": False # We want the whole response at once, not streaming
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()['message']['content']
    except Exception as e:
        print(f"Ollama API Error: {e}")
        return "Local AI Summary unavailable."

def send_telegram(msg):
    """Dispatches the final summary to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": f"📖 *SundayPrep Summary*:\n\n{msg}", 
        "parse_mode": "Markdown"
    }
    requests.post(url, json=data)

def main():
    print("Starting SundayPrep with Local Ollama Engine...")
    content = get_latest_newsletter()
    if content:
        print("Sending to Ollama for summarization...")
        summary = summarize_with_ollama(content)
        print("Sending to Telegram...")
        send_telegram(summary)
        print("Workflow complete!")
    else:
        print("No newsletter found in Gmail.")

if __name__ == "__main__":
    main()