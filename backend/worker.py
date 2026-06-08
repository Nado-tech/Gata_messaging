import os
import datetime
import requests
from supabase import create_client, Client
import resend

# 1. Config Cloud Services
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
resend.api_key = os.environ.get("RESEND_API_KEY")

# Nigerian Gateway Credentials (e.g., BulkSMS Nigeria)
SMS_API_TOKEN = os.environ.get("BULKSMS_NIGERIA_TOKEN")
SMS_SENDER_ID = "GataHomes"  # Your approved alphanumeric business header

today = datetime.date.today()
today_md = today.strftime("%m-%d")
is_friday = (today.weekday() == 4)

def send_nigerian_sms(to_phone, message):
    """Sends SMS cleanly through local delivery routes to override DND issues."""
    url = "https://www.bulksmsnigeria.com/api/v2/sms"
    payload = {
        "body": message,
        "from": SMS_SENDER_ID,
        "to": to_phone
    }
    headers = {
        "Authorization": f"Bearer {SMS_API_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    try:
        r = requests.post(url, json=payload, headers=headers)
        print(f"SMS Response for {to_phone}: {r.json()}")
    except Exception as e:
        print(f"SMS Gateway Error: {e}")

def send_email(to_email, subject, html_body):
    try:
        resend.Emails.send({
            "from": "Gata Homes <info@yourdomain.com>",
            "to": to_email,
            "subject": subject,
            "html": html_body
        })
    except Exception as e:
        print(f"Email failed to send to {to_email}: {e}")

def get_template(template_type):
    res = supabase.table("templates").select("message_body").eq("id", template_type).execute()
    return res.data[0]["message_body"] if res.data else "Hello {name}"

def main():
    # Pull contacts & active text variations from cloud
    contacts = supabase.table("contacts").select("*").execute().data
    
    weekend_template = get_template("weekend")
    birthday_template = get_template("birthday")

    for person in contacts:
        name = person["name"]
        phone = person["phone"]
        email = person.get("email")
        p_type = person["type"]
        bday = person.get("birthday")

        # --- ROUTINE 1: BIRTHDAY (Only clients or leads who have a valid birthday) ---
        if bday and bday == today_md:
            custom_msg = birthday_template.replace("{name}", name)
            send_nigerian_sms(phone, custom_msg)
            if email:
                send_email(email, "Happy Birthday from Us!", f"<h3>{custom_msg}</h3>")

        # --- ROUTINE 2: WEEKENDS (Fridays - Sends to everyone: leads & clients) ---
        if is_friday:
            custom_msg = weekend_template.replace("{name}", name)
            send_nigerian_sms(phone, custom_msg)
            if email:
                send_email(email, f"Have a great weekend, {name}!", f"<p>{custom_msg}</p>")

if __name__ == "__main__":
    main()