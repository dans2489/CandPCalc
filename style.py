# style.py

def inject_govuk_style(st):
    """Injects GOV.UK Design System inspired CSS into Streamlit app."""
    st.markdown(
        """
        <style>
        html, body, [class*="css"] {
          font-family: system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, Ubuntu, Cantarell,
                       Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", sans-serif;
        }
        .stButton > button {
          background: #00703C; color: #fff; border: 2px solid #005A30;
          border-radius: 4px; padding: .50rem 1rem; font-weight: 600; width: 100%;
        }
        .stButton > button:focus { outline: 3px solid #FFDD00; outline-offset: 2px; }
        .stDownloadButton > button { width: 100%; }
        table { border-collapse: collapse; width: 100%; margin: .5rem 0 1rem; }
        th, td { border: 1px solid #b1b4b6; padding: .5rem .6rem; text-align: left; }
        thead th { background: #f3f2f1; font-weight: 700; }
        tr.grand td { font-weight: 800; border-top: 3px double #0b0c0c; }
        td.neg { color: #D4351C; }
        .muted { color: #6f777b; }
        [data-testid="stSidebar"] { background-color: #f3f2f1 !important; min-height: 100vh; min-width: 420px; }
        [data-testid="stSidebar"] > div, [data-testid="stSidebar"] > div > div,
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { background: transparent !important; }
        [data-testid="stSidebar"] > div:first-child { max-width: 480px; padding-right: 8px; }
        .sb-callout { background: #f3f2f1; border-left: 6px solid #b1b4b6;
          padding: 8px 10px; margin-bottom: 6px; font-weight: 700; }
        section[data-testid="stSidebar"][aria-expanded="false"] {
          width: 0 !important; min-width: 0 !important; max-width: 0 !important;
        }
        div[data-testid="stAppViewContainer"] {
          margin-left: auto !important; margin-right: auto !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )