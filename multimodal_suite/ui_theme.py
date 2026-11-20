import html
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600;700&display=swap');

:root {
  --ink: #f5f3ff; --muted: #c4c2e6;
  --violet: #8b5cf6; --pink: #ec4899; --cyan: #22d3ee; --amber: #fbbf24;
  --glass: rgba(255,255,255,0.06); --line: rgba(255,255,255,0.14);
}
html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif; }

/* Animated 2D backdrop: drifting colour blobs plus a dot grid */
.stApp {
  background: linear-gradient(135deg, #0a0619 0%, #1a0b3d 45%, #0b1d3a 100%);
  color: var(--ink);
  overflow-x: hidden;
}
.stApp::before {
  content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background:
    radial-gradient(rgba(255,255,255,.08) 1px, transparent 1px) 0 0 / 24px 24px;
  mask-image: radial-gradient(ellipse at center, #000 40%, transparent 85%);
}
.stApp::after {
  content: ""; position: fixed; inset: -20%; z-index: 0; pointer-events: none;
  background:
    radial-gradient(40% 40% at 20% 30%, rgba(139,92,246,.55), transparent 70%),
    radial-gradient(35% 35% at 80% 20%, rgba(236,72,153,.45), transparent 70%),
    radial-gradient(35% 35% at 70% 85%, rgba(34,211,238,.35), transparent 70%),
    radial-gradient(30% 30% at 25% 90%, rgba(251,191,36,.25), transparent 70%);
  filter: blur(40px); animation: blobs 18s ease-in-out infinite alternate;
}
@keyframes blobs {
  0%   { transform: translate(0,0) scale(1); }
  50%  { transform: translate(4%,-3%) scale(1.06); }
  100% { transform: translate(-3%,4%) scale(.98); }
}
.block-container, section[data-testid="stSidebar"] { position: relative; z-index: 1; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.4rem; max-width: 1150px; }

section[data-testid="stSidebar"] > div {
  background: linear-gradient(180deg, rgba(28,12,66,.92), rgba(10,5,28,.96));
  border-right: 1px solid var(--line);
}

/* Headings stay readable on every page */
.stApp h2, .stApp h3, .stApp h4, .stApp label { color: var(--ink) !important; }

/* Gradient hero card */
.hero {
  position: relative; overflow: hidden; padding: 32px 36px; margin-bottom: 28px;
  border-radius: 28px; background: var(--glass); border: 1px solid var(--line);
  backdrop-filter: blur(18px); box-shadow: 0 30px 80px rgba(0,0,0,.4);
  animation: rise .8s cubic-bezier(.2,.8,.2,1) both;
}
.hero::before, .hero::after {
  content: ""; position: absolute; border-radius: 50%; pointer-events: none;
}
.hero::before {
  width: 320px; height: 320px; right: -80px; top: -130px;
  background: radial-gradient(circle, rgba(236,72,153,.55), transparent 70%);
  filter: blur(14px); animation: float 10s ease-in-out infinite alternate;
}
.hero::after {
  width: 240px; height: 240px; left: 42%; bottom: -140px;
  background: radial-gradient(circle, rgba(34,211,238,.4), transparent 70%);
  filter: blur(16px); animation: float 13s ease-in-out infinite alternate-reverse;
}
.hero .eyebrow {
  font-size: .72rem; letter-spacing: .24em; text-transform: uppercase;
  color: #f0abfc; font-weight: 700;
}
.hero h1 {
  position: relative; font-family: 'Space Grotesk', 'Inter', sans-serif;
  font-size: 2.6rem; font-weight: 700; line-height: 1.1; margin: .35rem 0 0;
  background: linear-gradient(90deg, #ddd6fe, #f9a8d4, #67e8f9, #ddd6fe);
  background-size: 300% 100%; animation: shimmer 8s linear infinite;
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { position: relative; color: var(--muted); margin: .6rem 0 0; font-size: 1.05rem; max-width: 640px; }
.chip {
  position: relative; display: inline-block; padding: 5px 14px; margin: 14px 8px 0 0;
  border-radius: 999px; font-size: .8rem;
  background: rgba(139,92,246,.2); border: 1px solid rgba(167,139,250,.55); color: #ede9fe;
}

/* Glass panels / forms */
div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--glass) !important; border: 1px solid var(--line) !important;
  border-radius: 22px !important; backdrop-filter: blur(18px); padding: 10px;
  box-shadow: 0 20px 60px rgba(0,0,0,.3);
}
label, [data-testid="stWidgetLabel"] p { color: #ede9fe !important; font-weight: 600; }

/* Inputs */
div[data-baseweb="input"] > div, div[data-baseweb="base-input"],
div[data-baseweb="textarea"], div[data-baseweb="select"] > div {
  background: rgba(14,8,42,.88) !important;
  border: 1px solid rgba(167,139,250,.4) !important;
  border-radius: 14px !important; color: var(--ink) !important;
}
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea,
div[data-baseweb="select"] span,
div[data-baseweb="select"] div { color: var(--ink) !important; }
div[data-baseweb="input"]:focus-within > div,
div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="select"]:focus-within > div {
  border-color: var(--pink) !important;
  box-shadow: 0 0 0 3px rgba(236,72,153,.22) !important;
}
ul[data-baseweb="menu"], li[role="option"] { background: #1a0f45 !important; color: var(--ink) !important; }

/* Buttons */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
  background: linear-gradient(100deg, var(--violet), var(--pink));
  color: #fff !important; border: 0; border-radius: 14px; font-weight: 700;
  padding: .7rem 1.6rem; letter-spacing: .01em;
  box-shadow: 0 14px 34px rgba(236,72,153,.32);
  transition: transform .18s ease, box-shadow .18s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {
  transform: translateY(-2px) scale(1.01);
  box-shadow: 0 18px 44px rgba(139,92,246,.5);
}

/* File uploader */
[data-testid="stFileUploaderDropzone"] {
  background: rgba(14,8,42,.88) !important;
  border: 1.5px dashed rgba(167,139,250,.6) !important;
  border-radius: 18px !important;
}
[data-testid="stFileUploaderDropzone"] * { color: #ddd6fe !important; }
[data-testid="stFileUploaderDropzone"] button {
  background: linear-gradient(100deg, var(--violet), var(--pink)) !important;
  color: #fff !important; border: 0 !important;
}

/* Tabs */
button[data-baseweb="tab"] { color: var(--muted) !important; font-weight: 700; font-size: 1.02rem; }
button[data-baseweb="tab"][aria-selected="true"] { color: #fff !important; }
div[data-baseweb="tab-highlight"] { background: linear-gradient(90deg, var(--violet), var(--pink)) !important; height: 3px !important; }
div[data-baseweb="tab-border"] { background: var(--line) !important; }

/* Alerts / metrics / images */
div[data-testid="stAlert"] { border-radius: 16px; }
div[data-testid="stMetric"] {
  background: var(--glass); border: 1px solid var(--line);
  border-radius: 18px; padding: 16px 20px;
}
img { border-radius: 20px; box-shadow: 0 24px 60px rgba(0,0,0,.5); }

@keyframes rise { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }
@keyframes float { from { transform: translate(0,0); } to { transform: translate(-48px, 34px); } }
@keyframes shimmer { 0% { background-position: 0% 50%; } 100% { background-position: 300% 50%; } }

/* INPUT FIX: dark text on white fields, grey placeholders */
div[data-baseweb="input"] > div, div[data-baseweb="base-input"], div[data-baseweb="textarea"], div[data-baseweb="select"] > div {
  background: #ffffff !important;
}
div[data-baseweb="input"] input, div[data-baseweb="base-input"] input, div[data-baseweb="textarea"] textarea {
  color: #111827 !important; -webkit-text-fill-color: #111827 !important; caret-color: #111827 !important;
}
div[data-baseweb="input"] input::placeholder, div[data-baseweb="textarea"] textarea::placeholder {
  color: #6b7280 !important; -webkit-text-fill-color: #6b7280 !important; opacity: 1 !important;
}
div[data-baseweb="select"] span, div[data-baseweb="select"] div, div[data-baseweb="select"] input {
  color: #111827 !important; -webkit-text-fill-color: #111827 !important;
}
span[data-baseweb="tag"] span, span[data-baseweb="tag"] div { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
input:-webkit-autofill, textarea:-webkit-autofill {
  -webkit-box-shadow: 0 0 0 1000px #ffffff inset !important; -webkit-text-fill-color: #111827 !important;
}

.hero-row { display: flex; gap: 28px; align-items: center; flex-wrap: wrap; }
.hero-text { flex: 1 1 320px; min-width: 260px; }
.hero-art { flex: 1 1 260px; max-width: 380px; }
.hero-art svg { width: 100%; height: auto; overflow: visible; }
.hero-art .f1 { animation: bob 6s ease-in-out infinite; }
.hero-art .f2 { animation: bob 7s ease-in-out infinite reverse; }
.hero-art .f3 { animation: bob 5.5s ease-in-out infinite .6s; }
@keyframes bob { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
</style>
"""

AUTH_VISUAL = """
<svg viewBox="0 0 400 220" xmlns="http://www.w3.org/2000/svg" class="art" role="img" aria-label="Campaign preview">
<defs>
<linearGradient id="gA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8b5cf6"/><stop offset="1" stop-color="#ec4899"/></linearGradient>
<linearGradient id="gB" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22d3ee"/><stop offset="1" stop-color="#8b5cf6"/></linearGradient>
</defs>
<rect x="110" y="20" width="130" height="190" rx="22" fill="rgba(255,255,255,.08)" stroke="rgba(255,255,255,.35)"/>
<rect x="124" y="40" width="102" height="150" rx="12" fill="url(#gA)" opacity=".9"/>
<circle cx="175" cy="95" r="26" fill="#ffffff" opacity=".92"/>
<path d="M160 97 Q175 80 190 97" stroke="#8b5cf6" stroke-width="5" fill="none" stroke-linecap="round"/>
<rect x="136" y="140" width="78" height="8" rx="4" fill="#ffffff" opacity=".85"/>
<rect x="144" y="156" width="62" height="6" rx="3" fill="#ffffff" opacity=".55"/>
<g class="f1"><rect x="26" y="46" width="88" height="60" rx="14" fill="rgba(255,255,255,.16)" stroke="rgba(255,255,255,.45)"/><rect x="40" y="62" width="52" height="6" rx="3" fill="#ffffff"/><rect x="40" y="78" width="34" height="6" rx="3" fill="#f9a8d4"/></g>
<g class="f2"><rect x="268" y="32" width="108" height="76" rx="14" fill="rgba(255,255,255,.16)" stroke="rgba(255,255,255,.45)"/><path d="M282 94 L300 76 L316 86 L338 56" stroke="#67e8f9" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>
<g class="f3"><rect x="262" y="132" width="114" height="62" rx="14" fill="rgba(255,255,255,.16)" stroke="rgba(255,255,255,.45)"/><circle cx="286" cy="163" r="12" fill="url(#gB)"/><rect x="308" y="153" width="52" height="6" rx="3" fill="#ffffff"/><rect x="308" y="167" width="36" height="6" rx="3" fill="#fbcfe8"/></g>
</svg>
"""


def inject_css() -> None:
    """Apply the shared theme. Call once after st.set_page_config()."""
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str = "", chips: list | None = None, eyebrow: str = "Creative AI Workspace", visual: str = "") -> None:
    """Render the animated gradient header card."""
    chip_html = "".join(f'<span class="chip">{html.escape(c)}</span>' for c in (chips or []))
    art = f'<div class="hero-art">{visual}</div>' if visual else ""
    st.markdown(
        '<div class="hero"><div class="hero-row"><div class="hero-text">'
        f'<span class="eyebrow">{html.escape(eyebrow)}</span>'
        f"<h1>{html.escape(title)}</h1>"
        f"<p>{html.escape(subtitle)}</p>"
        f"<div>{chip_html}</div>"
        f"</div>{art}</div></div>",
        unsafe_allow_html=True,
    )


# ---- Login visual, input-colour fix and hero layout (these override the earlier definitions) ----

AUTH_VISUAL = """
<svg viewBox="0 0 400 220" xmlns="http://www.w3.org/2000/svg" class="art" role="img" aria-label="Campaign preview">
<defs>
<linearGradient id="gA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8b5cf6"/><stop offset="1" stop-color="#ec4899"/></linearGradient>
<linearGradient id="gB" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22d3ee"/><stop offset="1" stop-color="#8b5cf6"/></linearGradient>
</defs>
<rect x="110" y="20" width="130" height="190" rx="22" fill="rgba(255,255,255,.08)" stroke="rgba(255,255,255,.35)"/>
<rect x="124" y="40" width="102" height="150" rx="12" fill="url(#gA)" opacity=".9"/>
<circle cx="175" cy="95" r="26" fill="#ffffff" opacity=".92"/>
<path d="M160 97 Q175 80 190 97" stroke="#8b5cf6" stroke-width="5" fill="none" stroke-linecap="round"/>
<rect x="136" y="140" width="78" height="8" rx="4" fill="#ffffff" opacity=".85"/>
<rect x="144" y="156" width="62" height="6" rx="3" fill="#ffffff" opacity=".55"/>
<g class="f1"><rect x="26" y="46" width="88" height="60" rx="14" fill="rgba(255,255,255,.16)" stroke="rgba(255,255,255,.45)"/><rect x="40" y="62" width="52" height="6" rx="3" fill="#ffffff"/><rect x="40" y="78" width="34" height="6" rx="3" fill="#f9a8d4"/></g>
<g class="f2"><rect x="268" y="32" width="108" height="76" rx="14" fill="rgba(255,255,255,.16)" stroke="rgba(255,255,255,.45)"/><path d="M282 94 L300 76 L316 86 L338 56" stroke="#67e8f9" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>
<g class="f3"><rect x="262" y="132" width="114" height="62" rx="14" fill="rgba(255,255,255,.16)" stroke="rgba(255,255,255,.45)"/><circle cx="286" cy="163" r="12" fill="url(#gB)"/><rect x="308" y="153" width="52" height="6" rx="3" fill="#ffffff"/><rect x="308" y="167" width="36" height="6" rx="3" fill="#fbcfe8"/></g>
</svg>
"""

_EXTRA_CSS = """
<style>
/* Input text: dark text on white fields, grey placeholders */
div[data-baseweb="input"] > div, div[data-baseweb="base-input"], div[data-baseweb="textarea"], div[data-baseweb="select"] > div {
  background: #ffffff !important;
}
div[data-baseweb="input"] input, div[data-baseweb="base-input"] input, div[data-baseweb="textarea"] textarea {
  color: #111827 !important; -webkit-text-fill-color: #111827 !important; caret-color: #111827 !important;
}
div[data-baseweb="input"] input::placeholder, div[data-baseweb="textarea"] textarea::placeholder {
  color: #6b7280 !important; -webkit-text-fill-color: #6b7280 !important; opacity: 1 !important;
}
div[data-baseweb="select"] span, div[data-baseweb="select"] div, div[data-baseweb="select"] input {
  color: #111827 !important; -webkit-text-fill-color: #111827 !important;
}
span[data-baseweb="tag"] span, span[data-baseweb="tag"] div { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
input:-webkit-autofill, textarea:-webkit-autofill {
  -webkit-box-shadow: 0 0 0 1000px #ffffff inset !important; -webkit-text-fill-color: #111827 !important;
}
/* Hero layout with artwork on the right */
.hero-row { display: flex; gap: 28px; align-items: center; flex-wrap: wrap; }
.hero-text { flex: 1 1 320px; min-width: 260px; }
.hero-art { flex: 1 1 260px; max-width: 380px; }
.hero-art svg { width: 100%; height: auto; overflow: visible; }
.hero-art .f1 { animation: bob 6s ease-in-out infinite; }
.hero-art .f2 { animation: bob 7s ease-in-out infinite reverse; }
.hero-art .f3 { animation: bob 5.5s ease-in-out infinite .6s; }
</style>
"""


def inject_css() -> None:
    """Apply the full theme, including the input fix. Must run before any widget is drawn."""
    st.markdown(_CSS + _EXTRA_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str = "", chips: list | None = None, eyebrow: str = "Creative AI Workspace", visual: str = "") -> None:
    """Render the gradient header card. Pass visual=AUTH_VISUAL on the login screen."""
    chip_html = "".join(f'<span class="chip">{html.escape(c)}</span>' for c in (chips or []))
    art = f'<div class="hero-art">{visual}</div>' if visual else ""
    st.markdown(
        '<div class="hero"><div class="hero-row"><div class="hero-text">'
        f'<span class="eyebrow">{html.escape(eyebrow)}</span>'
        f"<h1>{html.escape(title)}</h1>"
        f"<p>{html.escape(subtitle)}</p>"
        f"<div>{chip_html}</div>"
        f"</div>{art}</div></div>",
        unsafe_allow_html=True,
    )


_TEXT_FIX = """
<style>
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
textarea[aria-label], input[aria-label] {
  color: #111827 !important;
  -webkit-text-fill-color: #111827 !important;
  background-color: #ffffff !important;
  caret-color: #111827 !important;
}
[data-testid="stTextArea"] textarea::placeholder,
[data-testid="stTextInput"] input::placeholder {
  color: #6b7280 !important;
  -webkit-text-fill-color: #6b7280 !important;
  opacity: 1 !important;
}
</style>
"""
_FINAL_FIX = _TEXT_FIX

_SIDEBAR_FIX = """
<style>
section[data-testid="stSidebar"] * {
  color: #f5f3ff !important; -webkit-text-fill-color: #f5f3ff !important;
}
section[data-testid="stSidebar"] button, section[data-testid="stSidebar"] button * {
  color: #ffffff !important; -webkit-text-fill-color: #ffffff !important;
}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS + _EXTRA_CSS + _FINAL_FIX + _SIDEBAR_FIX, unsafe_allow_html=True)
