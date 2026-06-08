import streamlit as st
import pandas as pd
from supabase import create_client

# Initialize Supabase Connection
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("Client & Lead Messaging Hub")

tab1, tab2, tab3 = st.tabs(["Manage Contacts", "Upload CSV", "Edit Dynamic Templates"])

# --- TAB 1: INDIVIDUAL ENTRY ---
with tab1:
    st.header("Add Single Contact")
    name = st.text_input("Full Name")
    phone = st.text_input("Phone Number")
    email = st.text_input("Email (Optional)")
    bday = st.text_input("Birthday (MM-DD) - Optional")
    c_type = st.selectbox("Type", ["client", "lead"])
    
    if st.button("Save Contact"):
        data = {"name": name, "phone": phone, "email": email, "birthday": bday if bday else None, "type": c_type}
        supabase.table("contacts").insert(data).execute()
        st.success(f"Added {name} successfully!")

# --- TAB 2: CSV BULK UPLOAD ---
with tab2:
    st.header("Bulk Upload Contacts via CSV")
    st.write("Ensure columns are exactly: `name`, `phone`, `email`, `birthday`, `type`")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("Preview:", df.head())
        if st.button("Upload All to Cloud DB"):
            records = df.to_dict(orient="records")
            # Replace empty NaN spaces with None for SQL compliance
            clean_records = [{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records]
            supabase.table("contacts").insert(clean_records).execute()
            st.success(f"Successfully imported {len(clean_records)} records!")

# --- TAB 3: DYNAMIC MESSAGES ---
with tab3:
    st.header("Update Message Templates")
    st.caption("Use {name} anywhere in the text to inject the person's actual name automatically.")
    
    types = ["weekend", "birthday", "holiday"]
    for t in types:
        # Fetch current saved template text
        res = supabase.table("templates").select("message_body").eq("id", t).execute()
        current_text = res.data[0]["message_body"] if res.data else f"Hello {{name}}, this is a {t} message."
        
        new_text = st.text_area(f"Template for: {t.upper()}", value=current_text, key=t)
        if st.button(f"Update {t.upper()} Text"):
            supabase.table("templates").upsert({"id": t, "message_body": new_text}).execute()
            st.success(f"Updated {t} layout!")