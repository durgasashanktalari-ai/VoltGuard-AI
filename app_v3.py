import streamlit as st
import google.generativeai as genai
from PIL import Image
import re
import io
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================

API_KEY = st.secrets["API_KEY"] 

genai.configure(api_key=API_KEY)
text_model = genai.GenerativeModel("gemini-2.5-flash")
vision_model = genai.GenerativeModel("gemini-2.5-flash")

st.set_page_config(
    page_title="VoltGuard AI | Electrical Fault Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "history" not in st.session_state:
    st.session_state.history = []

# =========================================================
# STYLES
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}

/* ---- App background ---- */
.stApp {
    background: radial-gradient(circle at 15% 0%, #101a2b 0%, #0a0f1a 45%, #070a12 100%);
    color: #E6EDF7;
}

/* ---- Hide default streamlit chrome ---- */
#MainMenu, footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0c1424 0%, #0a0f1a 100%);
    border-right: 1px solid rgba(0, 212, 255, 0.12);
}
section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] p {
    color: #B7C4D9;
}

/* ---- Hero header ---- */
.hero-wrap {
    text-align: center;
    padding: 18px 0 6px 0;
}
.hero-badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 999px;
    background: rgba(0, 212, 255, 0.08);
    border: 1px solid rgba(0, 212, 255, 0.35);
    color: #4FD8FF;
    font-size: 12.5px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 14px;
}
.hero-title {
    font-size: 46px;
    font-weight: 800;
    background: linear-gradient(90deg, #4FD8FF 0%, #7C6CFF 55%, #FF6FD8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
    margin: 0;
}
.hero-sub {
    color: #93A2B9;
    font-size: 16.5px;
    font-weight: 400;
    margin-top: 8px;
}

/* ---- Card ---- */
.vg-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.035), rgba(255,255,255,0.015));
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 22px 24px;
    margin-bottom: 18px;
}
.vg-card h3, .vg-card h2 {
    margin-top: 0;
}
.section-title {
    font-size: 22px;
    font-weight: 700;
    color: #EAF1FB;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 4px;
}
.section-caption {
    color: #85920 !important;
    color: #8B98AD;
    font-size: 13.5px;
    margin-bottom: 18px;
}

/* ---- Status pill metrics ---- */
.status-row { display:flex; gap:14px; flex-wrap: wrap; }
.status-pill {
    flex: 1;
    min-width: 200px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 16px 18px;
    display:flex;
    align-items:center;
    gap: 14px;
}
.status-dot {
    width: 10px; height:10px; border-radius:50%;
    background: #33E39B;
    box-shadow: 0 0 10px #33E39B;
}
.status-label { color:#8B98AD; font-size:12.5px; text-transform:uppercase; letter-spacing:.05em;}
.status-value { color:#EAF1FB; font-size:16px; font-weight:700; }

/* ---- Buttons ---- */
.stButton>button {
    background: linear-gradient(90deg, #00D4FF 0%, #7C6CFF 100%);
    color: #06101F;
    font-weight: 700;
    border: none;
    border-radius: 10px;
    padding: 10px 22px;
    letter-spacing: 0.01em;
    transition: all 0.15s ease;
}
.stButton>button:hover {
    filter: brightness(1.08);
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(0, 212, 255, 0.25);
}
.stDownloadButton>button {
    background: rgba(255,255,255,0.05);
    color: #EAF1FB;
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 10px;
    font-weight: 600;
}

/* ---- Inputs ---- */
.stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
    background-color: rgba(255,255,255,0.03) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #EAF1FB !important;
}

/* ---- Risk badges ---- */
.risk-badge {
    display:inline-block;
    padding: 6px 16px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 13px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.risk-low { background: rgba(51,227,155,0.12); color:#33E39B; border:1px solid rgba(51,227,155,0.4);}
.risk-medium { background: rgba(255,196,61,0.12); color:#FFC43D; border:1px solid rgba(255,196,61,0.4);}
.risk-high { background: rgba(255,90,90,0.12); color:#FF5A5A; border:1px solid rgba(255,90,90,0.4);}
.risk-unknown { background: rgba(150,160,180,0.12); color:#9AA6BB; border:1px solid rgba(150,160,180,0.4);}

/* ---- Report box ---- */
.report-box {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 24px 26px;
}
.report-box h1 { font-size: 22px; color:#4FD8FF; }
.report-box h2, .report-box h3 { font-size: 18px; color:#EAF1FB; margin-top: 20px;}

/* ---- Industry chips ---- */
.chip {
    background: rgba(124,108,255,0.08);
    border: 1px solid rgba(124,108,255,0.3);
    color: #B7ADFF;
    padding: 14px 16px;
    border-radius: 12px;
    font-weight: 600;
    text-align:center;
}

/* ---- AI confidence bar ---- */
.confidence-wrap {
    display:flex;
    align-items:center;
    gap: 12px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 16px;
}
.confidence-label {
    color:#8B98AD;
    font-size: 12.5px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
    white-space: nowrap;
}
.confidence-track {
    flex:1;
    height: 10px;
    border-radius: 999px;
    background: rgba(255,255,255,0.08);
    overflow: hidden;
}
.confidence-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #00D4FF, #7C6CFF);
}
.confidence-pct {
    font-family: 'JetBrains Mono', monospace;
    color: #4FD8FF;
    font-weight: 700;
    font-size: 14px;
    min-width: 44px;
    text-align: right;
}

/* ---- Report metadata header ---- */
.meta-header {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-left: 3px solid #4FD8FF;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 16px;
    font-size: 13.5px;
    color: #C4CEDF;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 8px 20px;
}
.meta-header b { color: #EAF1FB; }

/* ---- Report section blocks ---- */
.report-box h1 { font-size: 20px; color:#4FD8FF; margin-top: 4px; }
.report-box h2 { font-size: 17px; color:#EAF1FB; margin-top: 18px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.06); }

/* footer */
.vg-footer {
    text-align:center;
    color: #5D6B82;
    font-size: 12.5px;
    padding: 28px 0 8px 0;
    letter-spacing: 0.03em;
}
hr { border-color: rgba(255,255,255,0.08) !important; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# HELPERS
# =========================================================

def extract_risk_level(text: str) -> str:
    match = re.search(r"risk level.*?(LOW|MEDIUM|HIGH)", text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).upper()
    return "UNKNOWN"

def extract_severity(text: str) -> int:
    match = re.search(r"severity score.*?(\d{1,2})\s*/?\s*10?", text, re.IGNORECASE | re.DOTALL)
    if match:
        try:
            val = int(match.group(1))
            return max(1, min(val, 10))
        except ValueError:
            return 0
    return 0

def risk_badge_html(risk: str) -> str:
    css_class = {
        "LOW": "risk-low",
        "MEDIUM": "risk-medium",
        "HIGH": "risk-high",
    }.get(risk, "risk-unknown")
    return f'<span class="risk-badge {css_class}">{risk} RISK</span>'

def extract_confidence(text: str) -> int:
    match = re.search(r"AI Confidence.*?(\d{1,3})\s*%", text, re.IGNORECASE)
    if match:
        try:
            return max(0, min(int(match.group(1)), 100))
        except ValueError:
            return 0
    return 0

def confidence_bar_html(pct: int) -> str:
    if not pct:
        return ""
    return f"""
<div class="confidence-wrap">
    <span class="confidence-label">🤖 AI Confidence</span>
    <div class="confidence-track">
        <div class="confidence-fill" style="width:{pct}%;"></div>
    </div>
    <span class="confidence-pct">{pct}%</span>
</div>
"""

def strip_confidence_line(text: str) -> str:
    return re.sub(r"^.*AI Confidence.*\n?", "", text, flags=re.IGNORECASE | re.MULTILINE).strip()

def meta_header_html(prepared_by: str, asset_id: str, location: str, category: str, timestamp: str) -> str:
    return f"""
<div class="meta-header">
    <div>👤 <b>Prepared By:</b> {prepared_by or "—"}</div>
    <div>🏷 <b>Asset ID:</b> {asset_id or "—"}</div>
    <div>📍 <b>Location:</b> {location or "—"}</div>
    <div>🗂 <b>Category:</b> {category or "—"}</div>
    <div>🕒 <b>Generated:</b> {timestamp}</div>
</div>
"""

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("### ⚡ VoltGuard AI")
    st.caption("Electrical Fault Intelligence Platform")
    st.markdown("---")

    st.markdown("**System Status**")
    st.markdown("🟢 AI Engine — Online")
    st.markdown("🟢 Fault Detection — Active")
    st.markdown("🟢 Safety Monitor — Enabled")

    st.markdown("---")
    st.markdown("**Capabilities**")
    st.markdown("""
- Text-based fault diagnosis
- Vision-based equipment inspection
- Risk & severity scoring
- Safety & maintenance guidance
- Downloadable technical reports
    """)

    st.markdown("---")
    st.markdown("**Report Metadata**")
    st.caption("Applied to every report generated in this session.")
    prepared_by = st.text_input("Prepared By", value=st.session_state.get("prepared_by", "T. Durga Sashank"))
    asset_id = st.text_input("Asset ID", value=st.session_state.get("asset_id", "sashank2006"))
    location = st.text_input("Location", value=st.session_state.get("location", "Chennai"))
    st.session_state["prepared_by"] = prepared_by
    st.session_state["asset_id"] = asset_id
    st.session_state["location"] = location

    st.markdown("---")
    st.markdown("**Session**")
    st.markdown(f"Reports generated: **{len(st.session_state.history)}**")
    if st.session_state.history and st.button("Clear history", use_container_width=True):
        st.session_state.history = []
        st.rerun()

    st.markdown("---")
    st.caption("VoltGuard AI · Built with Streamlit + Gemini")

# =========================================================
# HERO
# =========================================================

st.markdown("""
<div class="hero-wrap">
    <div class="hero-badge">AI-Powered Diagnostics</div>
    <div class="hero-title">⚡ VoltGuard AI</div>
    <div class="hero-sub">Intelligent electrical fault detection, risk assessment &amp; safety guidance</div>
</div>
""", unsafe_allow_html=True)

st.write("")

st.markdown(f"""
<div class="status-row">
    <div class="status-pill">
        <div class="status-dot"></div>
        <div>
            <div class="status-label">AI Engine</div>
            <div class="status-value">Online</div>
        </div>
    </div>
    <div class="status-pill">
        <div class="status-dot"></div>
        <div>
            <div class="status-label">Fault Detection</div>
            <div class="status-value">Active</div>
        </div>
    </div>
    <div class="status-pill">
        <div class="status-dot"></div>
        <div>
            <div class="status-label">Reports Today</div>
            <div class="status-value">{len(st.session_state.history)}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.write("")

# =========================================================
# TABS
# =========================================================

tab_text, tab_image, tab_history = st.tabs(["📝 Text Analysis", "📷 Image Analysis", "📊 Report History"])

# ---------------------------------------------------------
# TAB 1 — TEXT ANALYSIS
# ---------------------------------------------------------
with tab_text:
    st.markdown('<div class="vg-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📝 Describe the Fault</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Provide as much detail as possible for a more accurate diagnostic report.</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([1, 2])
    with col_a:
        category = st.selectbox(
            "Fault Category",
            [
                "Motor Faults",
                "Transformer Faults",
                "Circuit Protection",
                "Electrical Panels",
                "Power Quality",
                "General Electrical Issues",
            ],
        )
    with col_b:
        fault = st.text_area(
            "Problem Description",
            height=120,
            placeholder="e.g. Motor is overheating and tripping the overload relay every 20 minutes under load...",
        )

    analyze_clicked = st.button("🔍 Analyze Fault", use_container_width=False)
    st.markdown('</div>', unsafe_allow_html=True)

    if analyze_clicked:
        if not fault.strip():
            st.warning("Please describe the electrical problem before analyzing.")
        elif not API_KEY:
            st.error("No Gemini API key configured. Add your key to `API_KEY` in the script.")
        else:
            prompt = f"""
You are a senior electrical engineer and industrial safety expert.

Analyze the following electrical fault in detail.

Fault Category:
{category}

Problem Description:
{fault}

Generate a professional technical report. Start with a single line stating your
diagnostic confidence, in exactly this format:
AI Confidence: XX%

Then generate the report using EXACTLY these section headings, in this order:

## 🔴 Fault Name

## ⚠ Risk Level
(LOW / MEDIUM / HIGH)

## 📊 Severity
(Provide a score between 1 and 10, plus a one-line justification)

## 🔍 Root Cause
(Explain the most likely underlying cause(s) of the fault)

## 🛠 Recommended Action
(Immediate safety steps and troubleshooting steps, as bullet points)

## 📅 Maintenance Schedule
(Suggested inspection/maintenance interval and preventive actions)

Use professional headings, bullet points and technical language. Do not add
any extra top-level sections beyond the ones listed above.
"""
            try:
                with st.spinner("Running diagnostic analysis..."):
                    response = text_model.generate_content(prompt)
                    report_text = response.text

                risk = extract_risk_level(report_text)
                severity = extract_severity(report_text)
                confidence = extract_confidence(report_text)
                clean_report = strip_confidence_line(report_text)
                gen_time = datetime.now().strftime("%Y-%m-%d %H:%M")

                st.session_state.history.append({
                    "type": "Text",
                    "category": category,
                    "input": fault,
                    "report": clean_report,
                    "risk": risk,
                    "severity": severity,
                    "confidence": confidence,
                    "prepared_by": prepared_by,
                    "asset_id": asset_id,
                    "location": location,
                    "time": gen_time,
                })

                st.success("Analysis complete")

                st.markdown(confidence_bar_html(confidence), unsafe_allow_html=True)
                st.markdown(
                    meta_header_html(prepared_by, asset_id, location, category, gen_time),
                    unsafe_allow_html=True,
                )

                res_col1, res_col2 = st.columns([1, 3])
                with res_col1:
                    st.markdown(risk_badge_html(risk), unsafe_allow_html=True)
                    st.write("")
                    if severity:
                        st.metric("Severity Score", f"{severity} / 10")
                with res_col2:
                    st.markdown(f'<div class="report-box">{clean_report}</div>', unsafe_allow_html=True)

                download_text = (
                    f"VoltGuard AI — Diagnostic Report\n"
                    f"Prepared By: {prepared_by}\n"
                    f"Asset ID: {asset_id}\n"
                    f"Location: {location}\n"
                    f"Category: {category}\n"
                    f"Generated: {gen_time}\n"
                    f"AI Confidence: {confidence}%\n"
                    f"{'-'*50}\n\n"
                    f"{clean_report}"
                )

                st.download_button(
                    "⬇ Download Report",
                    data=download_text,
                    file_name=f"voltguard_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown",
                )

            except Exception as e:
                st.error(f"Error: {e}")

# ---------------------------------------------------------
# TAB 2 — IMAGE ANALYSIS
# ---------------------------------------------------------
with tab_image:
    st.markdown('<div class="vg-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📷 Upload Equipment Image</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Upload a photo of the electrical equipment, panel, wiring, or component for visual fault inspection.</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload an Electrical Equipment Image",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
    )

    img_notes = st.text_input("Additional context (optional)", placeholder="e.g. panel making buzzing noise, visible discoloration...")

    img_col1, img_col2 = st.columns([1, 1.4])
    image = None
    if uploaded_file:
        image = Image.open(uploaded_file)
        with img_col1:
            st.image(image, caption="Uploaded Image", use_container_width=True)

    analyze_img_clicked = st.button("🔍 Analyze Image", use_container_width=False)
    st.markdown('</div>', unsafe_allow_html=True)

    if analyze_img_clicked:
        if not uploaded_file:
            st.warning("Please upload an image first.")
        elif not API_KEY:
            st.error("No Gemini API key configured. Add your key to `API_KEY` in the script.")
        else:
            vision_prompt = f"""
You are a senior electrical engineer performing a visual inspection.

Examine the uploaded image of electrical equipment carefully.
Additional context provided by the user: {img_notes if img_notes else "None"}

Generate a professional technical report. Start with a single line stating your
diagnostic confidence, in exactly this format:
AI Confidence: XX%

Then generate the report using EXACTLY these section headings, in this order:

## 🔴 Fault Name
(Name the fault, or state "No Fault Detected" if equipment looks normal)

## ⚠ Risk Level
(LOW / MEDIUM / HIGH)

## 📊 Severity
(Provide a score between 1 and 10, plus a one-line justification)

## 🔍 Root Cause
(Explain the most likely underlying cause(s) based on what is visible)

## 🛠 Recommended Action
(Immediate safety steps and troubleshooting steps, as bullet points)

## 📅 Maintenance Schedule
(Suggested inspection/maintenance interval and preventive actions)

Use professional headings, bullet points and technical language. Do not add
any extra top-level sections beyond the ones listed above. If no clear fault
is visible, state that the equipment appears to be in normal condition.
"""
            try:
                with st.spinner("Inspecting image..."):
                    response = vision_model.generate_content([vision_prompt, image])
                    report_text = response.text

                risk = extract_risk_level(report_text)
                severity = extract_severity(report_text)
                confidence = extract_confidence(report_text)
                clean_report = strip_confidence_line(report_text)
                gen_time = datetime.now().strftime("%Y-%m-%d %H:%M")

                st.session_state.history.append({
                    "type": "Image",
                    "category": "Image Inspection",
                    "input": img_notes or "(no additional notes)",
                    "report": clean_report,
                    "risk": risk,
                    "severity": severity,
                    "confidence": confidence,
                    "prepared_by": prepared_by,
                    "asset_id": asset_id,
                    "location": location,
                    "time": gen_time,
                })

                st.success("Inspection complete")

                st.markdown(confidence_bar_html(confidence), unsafe_allow_html=True)
                st.markdown(
                    meta_header_html(prepared_by, asset_id, location, "Image Inspection", gen_time),
                    unsafe_allow_html=True,
                )

                with img_col2:
                    st.markdown(risk_badge_html(risk), unsafe_allow_html=True)
                    st.write("")
                    if severity:
                        st.metric("Severity Score", f"{severity} / 10")

                st.markdown(f'<div class="report-box">{clean_report}</div>', unsafe_allow_html=True)

                download_text = (
                    f"VoltGuard AI — Image Inspection Report\n"
                    f"Prepared By: {prepared_by}\n"
                    f"Asset ID: {asset_id}\n"
                    f"Location: {location}\n"
                    f"Category: Image Inspection\n"
                    f"Generated: {gen_time}\n"
                    f"AI Confidence: {confidence}%\n"
                    f"{'-'*50}\n\n"
                    f"{clean_report}"
                )

                st.download_button(
                    "⬇ Download Report",
                    data=download_text,
                    file_name=f"voltguard_image_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown",
                )

            except Exception as e:
                st.error(f"Error: {e}")

# ---------------------------------------------------------
# TAB 3 — HISTORY
# ---------------------------------------------------------
with tab_history:
    st.markdown('<div class="vg-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Report History</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">All diagnostic reports generated during this session.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if not st.session_state.history:
        st.info("No reports generated yet. Run a text or image analysis to see it here.")
    else:
        for i, entry in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{entry['time']} · {entry['type']} · {entry['category']} · {entry['risk']} risk"):
                if entry.get("confidence"):
                    st.markdown(confidence_bar_html(entry["confidence"]), unsafe_allow_html=True)
                st.markdown(
                    meta_header_html(
                        entry.get("prepared_by", ""),
                        entry.get("asset_id", ""),
                        entry.get("location", ""),
                        entry["category"],
                        entry["time"],
                    ),
                    unsafe_allow_html=True,
                )
                st.markdown(risk_badge_html(entry["risk"]), unsafe_allow_html=True)
                if entry["severity"]:
                    st.write(f"**Severity:** {entry['severity']} / 10")
                st.write(f"**Input:** {entry['input']}")
                st.markdown(f'<div class="report-box">{entry["report"]}</div>', unsafe_allow_html=True)

# =========================================================
# INDUSTRY APPLICATIONS
# =========================================================

st.write("")
st.markdown('<div class="vg-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🏭 Industry Applications</div>', unsafe_allow_html=True)
st.markdown('<div class="section-caption">Where VoltGuard AI fits into your operations.</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
for col, label in zip([c1, c2, c3, c4], ["Manufacturing Plants", "Power Distribution", "Commercial Buildings", "Industrial Facilities"]):
    with col:
        st.markdown(f'<div class="chip">{label}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================

st.markdown(
    '<div class="vg-footer">VoltGuard AI · Streamlit + Gemini AI · Electrical Safety Intelligence Platform</div>',
    unsafe_allow_html=True,
)
