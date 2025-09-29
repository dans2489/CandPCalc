# style.py
# Injects GOV.UK-like styling into Streamlit (focus, buttons, typography).
# Guidance: GOV.UK focus & button patterns; Transport font reserved for *.service.gov.uk.
# https://design-system.service.gov.uk/get-started/focus-states/
# https://design-system.service.gov.uk/components/button/
# https://design-system.service.gov.uk/styles/typeface/

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
        background: #ffffff;
      }

      /* Headings scale similar to GOV.UK */
      h1, .stMarkdown h1 { font-weight:700; font-size: 32px; line-height: 1.2; margin-bottom: 10px; }
      h2, .stMarkdown h2 { font-weight:700; font-size: 24px; line-height: 1.3; margin-top: 20px; }
      h3, .stMarkdown h3 { font-weight:700; font-size: 19px; line-height: 1.3; margin-top: 15px; }

      a { color: var(--govuk-link); text-decoration: underline; }
      a:hover { color: var(--govuk-link-hover); }

      /* Buttons */
      .stButton > button {
        background: var(--govuk-button);
        color: #fff;
        border: 2px solid transparent;
        border-radius: 0;
        font-weight: 700;
        padding: 8px 16px;
        box-shadow: 0 2px 0 rgba(0,0,0,.1);
      }
      .stButton > button:hover { filter: brightness(0.95); }
      .stButton > button:focus, .stButton > button:focus-visible {
        outline: 3px solid var(--govuk-focus);
        outline-offset: 0;
        box-shadow: 0 -2px #000, 0 4px var(--govuk-focus), inset 0 0 0 1px #000;
      }

      /* Inputs, radios, checkboxes */
      input, select, textarea {
        border: 1px solid var(--govuk-border); border-radius: 0;
      }
      input:focus, select:focus, textarea:focus,
      .stRadio [role='radio']:focus, .stCheckbox input:focus {
        outline: 3px solid var(--govuk-focus) !important;
        box-shadow: 0 0 0 1px #000 inset !important;
      }

      /* Tables */
      table { border-collapse: collapse; width: 100%; }
      th, td { border-bottom: 1px solid #b1b4b6; padding: 8px 6px; text-align: left; }
      th { font-weight: 700; }
