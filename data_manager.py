# data_manager.py
import json
import os
from supabase import create_client, Client
import streamlit as st

# Supabase credentials (store in st.secrets)
url = st.secrets["https://ztlemssridgrenpkkbdv.supabase.co"]
key = st.secrets["sb_publishable_bKv9fj-e3L9PNj5uhUQVUA_iR6bJdWM"]
supabase: Client = create_client(url, key)

TABLE_NAME = "app_data"
ROW_ID = "app"  # we'll use a single row

def load_data():
    try:
        response = supabase.table(TABLE_NAME).select("data").eq("id", ROW_ID).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["data"]
        else:
            # If no row exists, create one with default empty structure
            default = {"groups": {}}
            supabase.table(TABLE_NAME).insert({"id": ROW_ID, "data": default}).execute()
            return default
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return {"groups": {}}

def save_data(data):
    try:
        supabase.table(TABLE_NAME).update({"data": data}).eq("id", ROW_ID).execute()
    except Exception as e:
        st.error(f"Error saving data: {e}")
