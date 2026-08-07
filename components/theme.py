"""Thème graphique de GeoDashboard."""

PRIMARY = "#17324D"
SECONDARY = "#0F766E"
ACCENT = "#2563EB"

BACKGROUND = "#F4F6F8"
SURFACE = "#FFFFFF"

TEXT = "#1E293B"
TEXT_LIGHT = "#FFFFFF"
TEXT_SECONDARY = "#64748B"

BORDER = "#D8E1E8"

SUCCESS = "#16A34A"
WARNING = "#F59E0B"
DANGER = "#DC2626"

RADIUS = "14px"

LOGO = "🌍"
APP_NAME = "GeoDashboard"
VERSION = "v0.1.0"


def load_theme():
    """Retourne le CSS global de l'application."""

    return f"""
<style>

.stApp {{
    background:{BACKGROUND};
}}

.block-container {{
    padding-top:1rem;
    padding-left:2rem;
    padding-right:2rem;
}}

header {{
    visibility:hidden;
}}

footer {{
    visibility:hidden;
}}

[data-testid="stSidebar"] {{
    display:none;
}}

.main-title {{

    font-size:40px;
    font-weight:800;
    color:{PRIMARY};

}}

.subtitle {{

    color:{TEXT_SECONDARY};
    font-size:18px;

}}

.card {{

    background:{SURFACE};

    border-radius:{RADIUS};

    border:1px solid {BORDER};

    padding:22px;

    box-shadow:
        0 6px 18px rgba(0,0,0,.06);

}}

.metric {{

    text-align:center;

}}

.metric-value {{

    font-size:34px;

    font-weight:800;

    color:{PRIMARY};

}}

.metric-label {{

    color:{TEXT_SECONDARY};

}}

</style>
"""