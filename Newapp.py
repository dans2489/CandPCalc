import streamlit as st
import smtplib
from email.message import EmailMessage

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(page_title="Prison Workshop Costing Tool", layout="centered")

# ------------------------------
# CUSTOM CSS FOR GOV STYLE
# ------------------------------
st.markdown("""
<style>
.main { background-color: #ffffff; color: #0b0c0c; }
.stApp h1 { color: #005ea5; font-weight: bold; margin-bottom: 20px; }
.stApp h2, .stApp h3 { color: #005ea5; margin-top: 15px; margin-bottom: 10px; }
div.stButton > button:first-child { background-color: #10703c; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; margin-top: 10px; margin-bottom: 10px; }
div.stTextInput > label, div.stNumberInput > label, div.stSelectbox > label, div.stRadio > label { font-weight: bold; margin-bottom: 5px; }
.stSlider > div > div:nth-child(1) > div > div > div { color: #005ea5; }
.stForm, .stContainer { box-shadow: 0 0 5px #e1e1e1; padding: 12px 15px; border-radius: 5px; margin-bottom: 15px; }
table { width: 100%; border-collapse: collapse; }
table th { background-color: #f3f2f1; text-align: left; padding: 8px; border-bottom: 2px solid #b1b4b6; }
table td { padding: 8px; border-bottom: 1px solid #e1e1e1; }
table tr.total-row { font-weight: bold; background-color: #e6f0fa; }
</style>
""", unsafe_allow_html=True)

# (rest of the code is the same as the last provided combined code... including the enhanced production section)
