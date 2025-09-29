# style.py
# Injects a GOV.UK-like look & feel into Streamlit.

import streamlit as st

def inject_govuk_css():
    st.markdown("""
    <style>
      :root{
        --govuk-text:#0b0c0c;
        --govuk-link:#1d70b8;
        --govuk-link-hover:#003078;
        --govuk-focus:#ffdd00;
        --govuk-button:#00703c;
        --govuk-border:#0b0c0c;
      }

      html, body, [class*="css"] {
        font-family: Arial, Helvetica, sans-serif; /* GDS Transport reserved for *.service.gov.uk */
        color: var(--govuk-text);
        background: #fff;
      }

      /* Headings similar to GOV.UK scale */
      h1, .stMarkdown h1 { font-weight:700; font-size: 32px; line-height: 1.2; margin: 0 0 10px 0; }
      h2, .stMarkdown h2 { font-weight:700; font-size: 24px; line-height: 1.3; margin: 20px 0 5px 0; }
      h3, .stMarkdown h3 { font-weight:700; font-size: 19px; line-height: 1.3; margin: 15px 0 5px 0; }

      p, .stMarkdown p { font-size: 19px; line-height: 1.5; }

      a { color: var(--govuk-link); text-decoration: underline; }
      a:hover { color: var(--govuk-link-hover); }

      /* Buttons */
      .stButton > button {
        background: var(--govuk-button);
        color: #fff;
        border: 2px solid transparent;
        border-radius: 0;
        font-weight: 700;
        padding: 9px 18px;
        box-shadow: 0 2px 0 rgba(0,0,0,.1);
      }
      .stButton > button:hover { filter: brightness(0.95); }
      .stButton > button:focus, .stButton > button:focus-visible {
        outline: 3px solid var(--govuk-focus);
        outline-offset: 0;
        box-shadow: 0 -2px #000, 0 4px var(--govuk-focus), inset 0 0 0 1px #000;
      }

      /* Inputs, selects, textareas */
      input, select, textarea {
        border: 1px solid var(--govuk-border) !important; border-radius: 0 !important;
      }
      input:focus, select:focus, textarea:focus {
        outline: 3px solid var(--govuk-focus) !important;
        box-shadow: 0 0 0 1px #000 inset !important;
      }

      /* Radios, checkboxes focus */
      .stRadio [role='radio']:focus, .stCheckbox input:focus {
        outline: 3px solid var(--govuk-focus) !important;
        box-shadow: 0 0 0 1px #000 inset !important;
      }

      /* Tables */
      table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 16px; }
      th, td { border-bottom: 1px solid #b1b4b6; padding: 8px; text-align: left; }
      th { background: #f3f2f1; }
      td.neg { color: #d4351c; }
      tr.grand td { font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)
