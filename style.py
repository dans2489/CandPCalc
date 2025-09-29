# style.py
# Minimal styling to keep your original look, widen the sidebar,
# and apply GOV.UK green/yellow to buttons and sliders only.

import streamlit as st

def inject_govuk_css():
    st.markdown("""
    <style>
      /* Wider sidebar so controls fit comfortably */
      [data-testid="stSidebar"] {
        min-width: 420px !important;
        max-width: 420px !important;
      }
      @media (max-width: 1200px) {
        [data-testid="stSidebar"] {
          min-width: 360px !important;
          max-width: 360px !important;
        }
      }

      /* GOV.UK colours (no typography changes) */
      :root {
        --govuk-green: #00703c;  /* Button green */
        --govuk-yellow: #ffdd00; /* Focus yellow */
      }

      /* Buttons: keep Streamlit look, just recolour */
      .stButton > button {
        background: var(--govuk-green) !important;
        color: #fff !important;
        border: 2px solid transparent !important;
        border-radius: 0 !important;
        font-weight: 600;
      }
      .stButton > button:hover { filter: brightness(0.95); }
      .stButton > button:focus, .stButton > button:focus-visible {
        outline: 3px solid var(--govuk-yellow) !important;
        outline-offset: 0 !important;
        box-shadow: 0 0 0 1px #000 inset !important;
      }

      /* Sliders: colour the handle and focus ring */
      [data-testid="stSlider"] [role="slider"] {
        background: var(--govuk-green) !important;
        border: 2px solid var(--govuk-green) !important;
        box-shadow: none !important;
      }
      [data-testid="stSlider"] [role="slider"]:focus,
      [data-testid="stSlider"] [role="slider"]:focus-visible {
        outline: 3px solid var(--govuk-yellow) !important;
        outline-offset: 0 !important;
        box-shadow: 0 0 0 1px #000 inset !important;
      }
      /* Try to tint the filled track (best-effort; Streamlit DOM may change) */
      [data-testid="stSlider"] div[aria-hidden="true"] > div > div {
        background-color: var(--govuk-green) !important;
      }
    </style>
    """, unsafe_allow_html=True)
