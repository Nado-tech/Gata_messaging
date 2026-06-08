import os
import datetime
import requests
from supabase import create_client, Client
import resend

# 1. Config Cloud Services
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
resend.api_key = os.environ.get("RESEND_API_KEY")

# Nigerian SMS Gateway Credentials
SMS_API_TOKEN = os.environ.get("BULKSMS_NIGERIA_TOKEN")
SMS_SENDER_ID = "GataHomes" 

# 2. Get Current Date Profiles
today = datetime.date.today()
today_md = today.strftime("%m-%d")  # Format: "10-01"
is_friday = (today.weekday() == 4)   # True if today is Friday

# 3. National Holiday Mapping (MM-DD)
MAJOR_HOLIDAYS = {
    "01-01": "New Year's Day",
    "05-01": "Workers' Day",
    "06-12": "Democracy Day",
    "10-01": "Independence Day",
    "12-25": "Christmas Day",
    "12-26": "Boxing Day"
    # Note: For lunar holidays like Eid el Fitr or Eid el Kabir, 
    # you can just quickly type that date here manually via GitHub once a year.
}

def send_nigerian_sms(to_phone, message):
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
        print(f"Email failed: {e}")

def get_template(template_type):
    res = supabase.table("templates").select("message_body").eq("id", template_type).execute()
    return res.data[0]["message_body"] if res.data else "Hello {name}"

def main():
    # Fetch all live records from the DB
    contacts = supabase.table("contacts").select("*").execute().data
    
    # Pre-fetch template variants
    holiday_template = get_template("holiday")
    birthday_template = get_template("birthday")
    weekend_template = get_template("weekend")

    # Determine if today is a recognized holiday
    is_holiday = today_md in MAJOR_HOLIDAYS
    holiday_name = MAJOR_HOLIDAYS.get(today_md, "")

    for person in contacts:
        name = person["name"]
        phone = person["phone"]
        email = person.get("email")
        bday = person.get("birthday")

        # --- ROUTINE 1: HOLIDAYS (Highest Priority) ---
        if is_holiday:
            # Replaces both {name} and {holiday} dynamically
            custom_msg = holiday_template.replace("{name}", name).replace("{holiday}", holiday_name)
            send_nigerian_sms(phone, custom_msg)
            if email:
                send_email(email, f"Happy {holiday_name}!", f"<p>{custom_msg}</p>")
            
            # Skip checking birthday/weekend rules for this person today
            continue 

        # --- ROUTINE 2: BIRTHDAYS ---
        if bday and bday == today_md:
            custom_msg = birthday_template.replace("{name}", name)
            send_nigerian_sms(phone, custom_msg)
            if email:
                send_email(email, "Happy Birthday from Gata Homes!", f"<h3>{custom_msg}</h3>")
            
            # If it's their birthday on a Friday, prioritize the birthday wish over the weekend blast
            continue

        # --- ROUTINE 3: WEEKENDS ---
        if is_friday:
            custom_msg = weekend_template.replace("{name}", name)
            send_nigerian_sms(phone, custom_msg)
            if email:
                send_email(email, "Have a wonderful weekend!", f"<p>{custom_msg}</p>")

if __name__ == "__main__":
    main()