import os
import imaplib
import email
import requests

# --- Configuration & Environment Variables ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
MODEL_ID = "llama-3.3-70b-versatile"

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_latest_newsletter():
    """Retrieves the plain text body of the newsletter from Gmail via IMAP."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")
        
        # Searching for the specific church newsletter subject
        status, messages = mail.search(None, '(SUBJECT "Downes Road Weekly Newsletter")')
        if status != "OK" or not messages[0]:
            print("Newsletter not found in inbox.")
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
    """Summarizes newsletter content using Groq LPU and an external prompt template."""
    if not text:
        return "No content provided for summarization."
    
    # Load the external prompt from prompt.txt
    try:
        with open("prompt.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print("Error: prompt.txt was not found in the root directory.")
        return "Configuration Error: Prompt file missing."

    # Inject the newsletter content into the template placeholder {newsletter_content}
    formatted_prompt = prompt_template.format(newsletter_content=text)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_ID,
        "messages": [
            {
                "role": "user", 
                "content": formatted_prompt
            }
        ],
        "temperature": 0.3 # Low temperature for factual consistency
    }
    
    try:
        response = requests.post(ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Groq API Error: {e}")
        return "AI Summary generation failed."

def send_telegram(msg):
    """Sends the final Markdown summary to the Telegram Bot."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": f"📖 *SundayPrep Summary*:\n\n{msg}", 
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=data)
        res.raise_for_status()
    except Exception as e:
        print(f"Telegram Delivery Error: {e}")

def main():
    print(f"--- Starting SundayPrep (Engine: {MODEL_ID}) ---")
    
    print("Step 1: Fetching latest newsletter...")
    content = get_latest_newsletter()
    
    if content:
        print("Step 2: Processing summary via Groq...")
        summary = summarize_with_groq(content)
        
        print("Step 3: Dispatched to Telegram...")
        send_telegram(summary)
        print("Workflow Complete!")
    else:
        print("Workflow Aborted: No newsletter found.")

if __name__ == "__main__":
    main()