# dashboard/theme.py
"""
SaaS-style card layout for the dashboard — no data logic here.
Injected once at the top of app.py.
"""

import streamlit as st

CUSTOM_CSS = """
<style>
.stApp {
    background-color: #f4f6fb;
    color: #031716;
}

section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e8ebf3;
}
section[data-testid="stSidebar"] * {
    color: #031716 !important;
}
section[data-testid="stSidebar"] .stRadio label {
    font-size: 15px;
    padding: 10px 12px;
    border-radius: 10px;
    margin-bottom: 4px;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background-color: #eef1fa;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #ffffff;
    border-radius: 16px !important;
    border: 1px solid #e5e7eb !important;
    box-shadow: 0 2px 10px rgba(15, 26, 33, 0.06);
    padding: 18px 20px !important;
}

div[data-testid="stMetric"] {
    background-color: transparent;
    border: none;
    padding: 4px 0;
}
div[data-testid="stMetricLabel"] {
    color: #4b5563;
    font-weight: 500;
    font-size: 13px;
}
div[data-testid="stMetricValue"] {
    color: #031716;
    font-size: 30px;
    font-weight: 700;
}

h1, h2, h3, h4, h5, h6,
p, li, span, label, th, td, div {
    color: #031716;
}

.stButton > button {
    background-color: #0A7075;
    color: #ffffff;
    border-radius: 10px;
    border: none;
    padding: 8px 22px;
    font-weight: 600;
}
.stButton > button:hover {
    background-color: #074f52;
    color: #ffffff;
}

.prototype-banner {
    background-color: #fef3e2;
    border-left: 4px solid #f59e0b;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 13.5px;
    color: #6b4c0b;
    margin-bottom: 18px;
}

.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 11px;
    color: white;
}
.badge-low, .badge-success { background-color: #10b981; }
.badge-medium { background-color: #f59e0b; }
.badge-high, .badge-failed { background-color: #ef4444; }
.badge-stable { background-color: #6b7280; }
.badge-increasing { background-color: #ef4444; }
.badge-decreasing { background-color: #10b981; }
.badge-new { background-color: #3b82f6; }

.card-title {
    font-size: 15px;
    font-weight: 700;
    color: #031716;
    margin-bottom: 10px;
}
</style>
"""


def apply_theme():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def prototype_banner(text: str):
    st.markdown(f'<div class="prototype-banner">{text}</div>', unsafe_allow_html=True)


def badge(text: str, kind: str) -> str:
    """kind: low/medium/high/success/failed/stable/increasing/decreasing/new (case-insensitive)"""
    css_class = f"badge-{kind.lower()}"
    return f'<span class="badge {css_class}">{text}</span>'


def risk_badge(risk_level: str) -> str:
    css_class = {"LOW": "low", "MEDIUM": "medium", "HIGH": "high"}.get(risk_level, "medium")
    return badge(risk_level, css_class)
