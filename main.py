import os
import imaplib
import email
from email.header import decode_header
import google.generativeai as genai
import requests

# Configuration from Environment Variables
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")  # Use an App Password
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_latest_newsletter():
    """Connects to Gmail and retrieves the body of the latest newsletter."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")

        # Search for the specific sender and subject
        status, messages = mail.search(None, '(SUBJECT "Downes Road Weekly Newsletter")')
        if status != "OK" or not messages[0]:
            return None

        # Get the latest email ID
        latest_email_id = messages[0].split()[-1]
        res, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        
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
        print(f"Error accessing Gmail: {e}")
    return None

def summarize_with_gemini(text):
    """Uses Gemini API to condense the newsletter into 3 concise sentences."""
    if not text:
        print("Error: No text provided to summarize.")
        return "No content found in the newsletter."

    # Add this line here to debug
    print(f"DEBUG: Sending {len(text)} characters to Gemini API.")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    prompt = f"""
    The following is a church newsletter. Extract the main scripture reference 
    and the primary sermon points. Provide a summary in exactly 3 concise sentences 
    suitable for a mobile notification.
    
    Newsletter Content:
    {text}
    """
    response = model.generate_content(prompt)
    return response.text

def send_telegram_notification(message):
    """Sends the final summary to the Telegram bot."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"📖 SundayPrep Summary:\n\n{message}",
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def main():
    print("Fetching newsletter...")
    content = get_latest_newsletter()
    if content:
        print("Summarizing with AI...")
        summary = summarize_with_gemini(content)
        print("Sending notification...")
        send_telegram_notification(summary)
        print("Done!")
    else:
        print("No newsletter found.")

if __name__ == "__main__":
    main()