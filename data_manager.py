# data_manager.py
import json
import os
import streamlit as st

# Try to import Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

DATA_FILE = "students_data.json"

# Supabase configuration – using proper key names
if SUPABASE_AVAILABLE and "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
    url = st.secrets["https://ztlemssridgrenpkkbdv.supabase.co"]     
    key = st.secrets["sb_publishable_bKv9fj-e3L9PNj5uhUQVUA_iR6bJdWM"]      
    supabase: Client = create_client(url, key)
    TABLE_NAME = "app_data"
    ROW_ID = "app"
    USE_SUPABASE = True
else:
    USE_SUPABASE = False
    if not SUPABASE_AVAILABLE:
        st.warning("Supabase library not installed – using local JSON storage.")
    else:
        st.warning("Supabase secrets not configured – using local JSON storage.")

def load_data():
    if USE_SUPABASE:
        try:
            response = supabase.table(TABLE_NAME).select("data").eq("id", ROW_ID).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]["data"]
            else:
                default = {"groups": {}}
                supabase.table(TABLE_NAME).insert({"id": ROW_ID, "data": default}).execute()
                return default
        except Exception as e:
            st.error(f"Supabase error: {e} – falling back to local JSON")
            return load_local_data()
    else:
        return load_local_data()

def save_data(data):
    if USE_SUPABASE:
        try:
            supabase.table(TABLE_NAME).update({"data": data}).eq("id", ROW_ID).execute()
        except Exception as e:
            st.error(f"Supabase save error: {e} – saving locally instead")
            save_local_data(data)
    else:
        save_local_data(data)

def load_local_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"groups": {}}

def save_local_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
