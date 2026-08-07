"""
Composant MetricCard.
"""

from __future__ import annotations

import streamlit as st


def render_metric_card(
    title: str,
    value: str,
    subtitle: str = "",
    color: str = "#17324D",
) -> None:
    """Affiche une carte KPI."""

    st.markdown(
        f"""
<div style="
background:white;
border-radius:14px;
padding:18px;
border:1px solid #E2E8F0;
box-shadow:0 4px 10px rgba(0,0,0,.05);
">

<div style="
font-size:14px;
color:#64748B;
margin-bottom:8px;
">
{title}
</div>

<div style="
font-size:34px;
font-weight:700;
color:{color};
">
{value}
</div>

<div style="
font-size:12px;
color:#94A3B8;
margin-top:8px;
">
{subtitle}
</div>

</div>
""",
        unsafe_allow_html=True,
    )