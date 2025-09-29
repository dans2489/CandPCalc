# style.py
# Minimal styling: keep your original look, only widen the sidebar so inputs fit.

import streamlit as st

def inject_govuk_css():
    # Name kept for compatibility with imports, but the styles are minimal on purpose.
    st.markdown("""
    <style>
      /* Make the sidebar wider so inputs fit comfortably */
      [data-testid="stSidebar"] {
        min-width: 420px !important;
        max-width: 420px !important;
      }
      /* Slightly narrower on smaller screens */
      @media (max-width: 1200px) {
        [data-testid="stSidebar"] {
          min-width: 360px !important;
          max-width: 360px !important;
        }
      }
    </style>
    """, unsafe_allow_html=True)
