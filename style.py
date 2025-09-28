def inject_govuk_style(st):
    st.markdown(
        """
        <style>
        body, html, [class*="css"] {
          font-family: "GDS Transport", Arial, sans-serif;
        }
        h1, h2, h3, .stMarkdown h2 {
          font-weight: 700; margin-bottom: 0.5rem;
        }
        label, .stRadio label, .stSelectbox label, .stNumberInput label {
          font-weight: 600; margin-bottom: 0.25rem;
        }
        .stButton > button {
          background: #00703C; border: 2px solid #005A30; border-radius: 4px;
          padding: .6rem 1.2rem; font-size: 1rem; font-weight: 600; width: auto;
        }
        .stButton > button:hover { background: #005A30; }
        .stButton > button:focus { outline: 3px solid #FFDD00; outline-offset: 2px; }
        .hint { color: #505a5f; font-size: 0.9rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )