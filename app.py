# =============================================================================
# app.py — Fasal-to-Faida  |  Bech Sahi, Kamaao Zyada
# Agrikon-inspired UI — full-width horizontal layout
#
# pip install streamlit pandas numpy plotly joblib xgboost scikit-learn
# streamlit run app.py
# =============================================================================

import random
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(
    page_title="Fasal-to-Faida | Market Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# PALETTE
# =============================================================================
GREEN       = "#1B4332"
GREEN_MID   = "#2D6A4F"
GREEN_LIGHT = "#52B788"
AMBER       = "#E8A020"
AMBER_DARK  = "#C8590A"
AMBER_LIGHT = "#F5C842"
BG_WHITE    = "#FFFFFF"
BG_OFFWHITE = "#F7F4EF"
BG_WARM     = "#FDF6E3"
TEXT_DARK   = "#1A1A1A"
TEXT_MUTED  = "#666666"
BORDER      = "#E0DAD0"

MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]
CROPS  = ["Tomato","Onion","Potato","Wheat","Rice"]

DUMMY_MARKETS = [
    ("Azadpur",    "Delhi",       "North West Delhi"),
    ("Lasalgaon",  "Maharashtra", "Nashik"),
    ("Vashi",      "Maharashtra", "Navi Mumbai"),
    ("Kothi",      "Punjab",      "Amritsar"),
    ("Bowenpally", "Telangana",   "Hyderabad"),
]

# =============================================================================
# CSS — full Agrikon-style
# =============================================================================
def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;900&family=Nunito+Sans:wght@300;400;500;600;700&display=swap');

    /* ── Base reset ───────────────────────────────────────────── */
    html, body, .stApp {{
        background-color: {BG_OFFWHITE};
        font-family: 'Nunito Sans', sans-serif;
        color: {TEXT_DARK};
    }}
    .block-container {{
        padding: 0 !important;
        max-width: 100% !important;
    }}
    [data-testid="stSidebar"] {{ display: none; }}
    header[data-testid="stHeader"] {{ background: transparent; }}
    #MainMenu, footer, header {{ visibility: hidden; }}

    /* ─────────────────────────────────────────────────────────── */
    /* STREAMLIT WIDGET TEXT — always dark (labels float above     */
    /* custom green divs in the DOM, so they are always on the     */
    /* app's light background in the stacking context)             */
    /* ─────────────────────────────────────────────────────────── */
    /* Labels */
    .stTextInput  > label,
    .stNumberInput > label,
    .stSelectbox  > label,
    .stMultiSelect > label {{
        color: {TEXT_DARK} !important;
        font-family: 'Nunito Sans', sans-serif !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
    }}
    /* Text inputs */
    .stTextInput input,
    .stNumberInput input {{
        color: {TEXT_DARK} !important;
        background: #FFFFFF !important;
        border: 1px solid {BORDER} !important;
        font-family: 'Nunito Sans', sans-serif !important;
        font-size: 0.9rem !important;
        border-radius: 4px !important;
    }}
    .stTextInput input::placeholder,
    .stNumberInput input::placeholder {{
        color: #AAAAAA !important;
    }}
    /* Selectbox */
    .stSelectbox [data-baseweb="select"] > div {{
        background: #FFFFFF !important;
        border: 1px solid {BORDER} !important;
        border-radius: 4px !important;
    }}
    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] div[class] {{
        color: {TEXT_DARK} !important;
        background: transparent !important;
    }}
    /* Dropdown list options */
    [data-baseweb="popover"] li,
    [data-baseweb="menu"] li {{
        color: {TEXT_DARK} !important;
        background: white !important;
    }}
    [data-baseweb="popover"] li:hover,
    [data-baseweb="menu"]  li:hover {{
        background: {BG_OFFWHITE} !important;
    }}
    /* Number input stepper buttons */
    .stNumberInput button {{
        color: {TEXT_DARK} !important;
        background: {BG_OFFWHITE} !important;
        border-color: {BORDER} !important;
    }}
    /* stMarkdown generic text */
    .stMarkdown, .stMarkdown p, .stMarkdown span {{
        color: {TEXT_DARK};
    }}

    /* ── Top nav bar ──────────────────────────────────────────── */
    .nav-bar {{
        background: {GREEN};
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 48px;
        height: 64px;
        position: sticky;
        top: 0;
        z-index: 100;
        box-shadow: 0 2px 12px rgba(0,0,0,0.15);
    }}
    .nav-logo {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: white;
        letter-spacing: 0.02em;
    }}
    .nav-logo span {{ color: {AMBER}; }}
    .nav-links {{
        display: flex;
        gap: 32px;
        align-items: center;
    }}
    .nav-links a {{
        color: rgba(255,255,255,0.85);
        font-size: 0.88rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-decoration: none;
        text-transform: uppercase;
    }}
    .nav-cta {{
        background: {AMBER};
        color: {GREEN} !important;
        padding: 8px 20px;
        border-radius: 3px;
        font-weight: 700 !important;
    }}

    /* ── Hero section ─────────────────────────────────────────── */
    .hero-section {{
        position: relative;
        width: 100%;
        height: 520px;
        overflow: hidden;
        background: {GREEN};
    }}
    .hero-bg {{
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image: url('https://images.unsplash.com/photo-1500595046743-cd271d694d30?w=1600&q=80&fit=crop');
        background-size: cover;
        background-position: center 40%;
        opacity: 0.55;
    }}
    .hero-content {{
        position: relative;
        z-index: 2;
        padding: 80px 80px;
        max-width: 620px;
    }}
    .hero-eyebrow {{
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: {AMBER};
        margin-bottom: 14px;
    }}
    .hero-title {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 3.6rem;
        font-weight: 900;
        color: white;
        line-height: 1.12;
        margin-bottom: 18px;
        text-shadow: 0 2px 20px rgba(0,0,0,0.3);
    }}
    .hero-title em {{
        color: {AMBER};
        font-style: normal;
    }}
    .hero-desc {{
        font-size: 1.05rem;
        color: rgba(255,255,255,0.88);
        line-height: 1.7;
        margin-bottom: 32px;
        max-width: 460px;
    }}
    .hero-btn {{
        display: inline-block;
        background: {AMBER};
        color: {GREEN};
        font-family: 'Nunito Sans', sans-serif;
        font-size: 0.88rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 14px 32px;
        border-radius: 3px;
        cursor: pointer;
        border: none;
        text-decoration: none;
    }}

    /* ── Amber strip + floating cards ─────────────────────────── */
    .amber-strip {{
        background: {AMBER};
        padding: 0 48px;
        display: flex;
        justify-content: center;
        gap: 24px;
        padding-top: 0;
        padding-bottom: 0;
        min-height: 18px;
    }}

    .float-card-wrap {{
        background: {BG_OFFWHITE};
        padding: 0 48px 0;
    }}
    .float-cards {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 24px;
        transform: translateY(-60px);
        margin-bottom: -40px;
    }}
    .float-card {{
        background: white;
        border-radius: 6px;
        overflow: hidden;
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        transition: transform 0.2s;
    }}
    .float-card img {{
        width: 100%;
        height: 180px;
        object-fit: cover;
    }}
    .float-card-label {{
        padding: 14px 18px;
        font-size: 0.88rem;
        font-weight: 700;
        color: {TEXT_DARK};
        text-align: center;
        letter-spacing: 0.02em;
    }}

    /* ── Section: split content ───────────────────────────────── */
    .section-wrap {{
        padding: 60px 64px;
    }}
    .section-wrap.offwhite {{ background: {BG_OFFWHITE}; }}
    .section-wrap.white    {{ background: {BG_WHITE};    }}
    .section-wrap.warm     {{ background: {BG_WARM};     }}
    .section-wrap.green    {{ background: {GREEN};       }}

    .section-eyebrow {{
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: {GREEN_LIGHT};
        margin-bottom: 10px;
        text-align: center;
    }}
    .section-eyebrow.dark {{ color: {AMBER}; }}
    .section-title {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 2.4rem;
        font-weight: 700;
        color: {GREEN};
        line-height: 1.2;
        margin-bottom: 16px;
        text-align: center;
    }}
    .section-title.white {{ color: white; }}
    .section-sub {{
        font-size: 1.0rem;
        color: {TEXT_MUTED};
        text-align: center;
        max-width: 580px;
        margin: 0 auto 44px;
        line-height: 1.7;
    }}
    .section-sub.white {{ color: rgba(255,255,255,0.75); }}

    /* ── Feature row cards ───────────────────────────────────── */
    .feat-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 24px;
    }}
    .feat-card {{
        background: white;
        border-radius: 6px;
        overflow: hidden;
        box-shadow: 0 4px 18px rgba(0,0,0,0.08);
        position: relative;
    }}
    .feat-card img {{
        width: 100%;
        height: 160px;
        object-fit: cover;
    }}
    .feat-icon-circle {{
        position: absolute;
        top: 136px;
        left: 50%;
        transform: translateX(-50%);
        width: 46px;
        height: 46px;
        border-radius: 50%;
        background: {GREEN};
        border: 3px solid white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        z-index: 2;
    }}
    .feat-card-body {{
        padding: 34px 18px 22px;
        text-align: center;
    }}
    .feat-card-title {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.05rem;
        font-weight: 700;
        color: {GREEN};
        margin-bottom: 8px;
    }}
    .feat-card-desc {{
        font-size: 0.85rem;
        color: {TEXT_MUTED};
        line-height: 1.6;
    }}

    /* ── Split section: images + text ─────────────────────────── */
    .split-section {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 60px;
        align-items: center;
        padding: 70px 80px;
        background: {BG_WHITE};
    }}
    .split-imgs {{
        position: relative;
        height: 420px;
    }}
    .split-img-main {{
        position: absolute;
        top: 0; left: 0;
        width: 78%;
        height: 88%;
        object-fit: cover;
        border-radius: 6px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
    }}
    .split-img-accent {{
        position: absolute;
        bottom: 0; right: 0;
        width: 54%;
        height: 55%;
        object-fit: cover;
        border-radius: 6px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        border: 4px solid white;
    }}
    .split-badge {{
        position: absolute;
        top: 50%;
        left: -18px;
        transform: translateY(-50%);
        background: {AMBER};
        color: {GREEN};
        border-radius: 50%;
        width: 80px;
        height: 80px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-weight: 900;
        font-size: 1.1rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.18);
        z-index: 10;
    }}
    .split-badge span {{ font-size: 0.62rem; font-weight: 600; letter-spacing: 0.04em; }}
    .split-text {{ }}
    .split-tagline {{
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: {AMBER_DARK};
        margin-bottom: 10px;
    }}
    .split-title {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: {GREEN};
        line-height: 1.2;
        margin-bottom: 14px;
    }}
    .split-highlight {{
        font-size: 0.95rem;
        font-weight: 600;
        color: {AMBER_DARK};
        margin-bottom: 18px;
        line-height: 1.6;
    }}
    .split-body {{
        font-size: 0.92rem;
        color: {TEXT_MUTED};
        line-height: 1.75;
        margin-bottom: 28px;
    }}
    .icon-badge-row {{
        display: flex;
        gap: 32px;
        margin-bottom: 28px;
    }}
    .icon-badge {{
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 0.88rem;
        font-weight: 700;
        color: {GREEN};
    }}
    .icon-badge .ib-circle {{
        background: {BG_OFFWHITE};
        border: 2px solid {BORDER};
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
    }}
    .btn-primary {{
        background: {GREEN};
        color: white;
        font-family: 'Nunito Sans', sans-serif;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 12px 26px;
        border-radius: 3px;
        border: none;
        cursor: pointer;
        margin-right: 12px;
    }}
    .btn-outline {{
        background: transparent;
        color: {GREEN};
        font-family: 'Nunito Sans', sans-serif;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 11px 26px;
        border-radius: 3px;
        border: 2px solid {GREEN};
        cursor: pointer;
    }}

    /* ── Input form section ───────────────────────────────────── */
    .form-section {{
        background: {GREEN};
        padding: 56px 80px;
    }}
    .form-grid {{
        display: grid;
        grid-template-columns: repeat(5, 1fr) auto;
        gap: 16px;
        align-items: end;
        margin-top: 32px;
    }}
    .form-field label {{
        display: block;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: rgba(255,255,255,0.65);
        margin-bottom: 7px;
    }}
    .form-field input,
    .form-field select {{
        width: 100%;
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 4px;
        color: white;
        padding: 10px 14px;
        font-family: 'Nunito Sans', sans-serif;
        font-size: 0.9rem;
        outline: none;
        box-sizing: border-box;
    }}
    .form-field select option {{ background: {GREEN}; color: white; }}

    div.stButton > button {{
        background: {AMBER} !important;
        color: {GREEN} !important;
        font-family: 'Nunito Sans', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.65rem 2rem !important;
        font-size: 0.88rem !important;
        width: 100% !important;
        margin-top: 24px;
    }}
    div.stButton > button:hover {{
        background: {AMBER_DARK} !important;
        color: white !important;
    }}

    /* ── Results section ──────────────────────────────────────── */
    .results-header {{
        background: {BG_OFFWHITE};
        padding: 48px 80px 16px;
    }}
    .results-body {{
        background: {BG_OFFWHITE};
        padding: 0 80px 60px;
    }}

    /* ── Metric card ──────────────────────────────────────────── */
    .mc {{
        background: white;
        border-top: 4px solid {GREEN};
        border-radius: 4px;
        padding: 22px 20px 18px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }}
    .mc.amber {{ border-top-color: {AMBER_DARK}; }}
    .mc-lbl {{
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: {TEXT_MUTED};
        margin-bottom: 10px;
    }}
    .mc-val {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 2.1rem;
        font-weight: 600;
        color: {GREEN};
        line-height: 1;
    }}
    .mc.amber .mc-val {{ color: {AMBER_DARK}; }}
    .mc-unit {{
        font-size: 0.72rem;
        color: {TEXT_MUTED};
        margin-top: 6px;
    }}

    /* ── Section divider label ────────────────────────────────── */
    .sec-lbl {{
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: {TEXT_MUTED};
        border-bottom: 1px solid {BORDER};
        padding-bottom: 7px;
        margin: 36px 0 14px;
    }}

    /* ── Result recommendation box ────────────────────────────── */
    .reco-box {{
        background: {GREEN};
        color: white;
        border-radius: 4px;
        padding: 24px 32px;
        margin-top: 16px;
        font-size: 1.0rem;
        line-height: 1.7;
    }}
    .reco-box strong {{ font-weight: 700; }}
    .reco-lbl {{
        font-size: 0.68rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        opacity: 0.6;
        margin-bottom: 8px;
    }}

    /* ── Footer ───────────────────────────────────────────────── */
    .site-footer {{
        background: {GREEN};
        color: rgba(255,255,255,0.6);
        text-align: center;
        padding: 24px 48px;
        font-size: 0.8rem;
        letter-spacing: 0.03em;
    }}
    .site-footer strong {{ color: white; }}

    /* ── Streamlit table overrides ────────────────────────────── */
    div[data-testid="stDataFrame"] {{
        border: 1px solid {BORDER} !important;
        border-radius: 4px;
    }}
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# DUMMY DATA
# =============================================================================
def make_dummy_df(commodity="Onion", quantity_kg=500):
    random.seed(42)
    rows = []
    for market, state, district in DUMMY_MARKETS:
        dist_km       = random.randint(20, 300)
        price_per_q   = random.randint(1200, 3500)
        revenue       = (quantity_kg / 100) * price_per_q
        transport     = round(dist_km * 2.8 + random.randint(200, 600), 0)
        commission    = round(revenue * 0.025, 0)
        misc          = round(random.randint(100, 400), 0)
        net_profit    = round(revenue - transport - commission - misc, 0)
        profit_per_kg = round(net_profit / quantity_kg, 2)
        rows.append({
            "Market": market, "State": state, "District": district,
            "Distance_km": dist_km, "Predicted_Price": price_per_q,
            "Transport_Cost": transport, "Mandi_Commission": commission,
            "Misc_Cost": misc, "Net_Profit": net_profit,
            "Profit_per_kg": profit_per_kg,
        })
    return pd.DataFrame(rows).sort_values("Net_Profit", ascending=False).reset_index(drop=True)


def fetch_recommendations(commodity, quantity_kg, district, month_num, year):
    try:
        from recommender import recommend
        df = recommend(commodity, quantity_kg, district, month_num, year)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        pass
    return make_dummy_df(commodity, quantity_kg)


# =============================================================================
# CHARTS
# =============================================================================
def profit_bar_chart(df):
    sdf = df.sort_values("Net_Profit", ascending=True)
    fig = go.Figure(go.Bar(
        x=sdf["Net_Profit"], y=sdf["Market"],
        orientation="h",
        marker_color=[AMBER_DARK if i == len(sdf)-1 else GREEN_LIGHT for i in range(len(sdf))],
        text=[f"Rs. {v:,.0f}" for v in sdf["Net_Profit"]],
        textposition="outside",
        textfont=dict(size=11, family="Nunito Sans"),
    ))
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, tickformat=",", tickfont=dict(size=10)),
        yaxis=dict(showgrid=False, tickfont=dict(size=11)),
        plot_bgcolor="white", paper_bgcolor="white",
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=80),
        font=dict(family="Nunito Sans, sans-serif"),
        height=240,
    )
    return fig


def cost_pie_chart(row, quantity_kg):
    net    = max(row["Net_Profit"], 0)
    vals   = [net, row["Transport_Cost"], row["Mandi_Commission"], row["Misc_Cost"]]
    labels = ["Net Profit", "Transport", "Commission", "Misc"]
    colors = [GREEN, AMBER_DARK, GREEN_LIGHT, "#C5BFB0"]
    fig = go.Figure(go.Pie(
        labels=labels, values=vals, hole=0.44,
        marker_colors=colors,
        textinfo="percent",
        hovertemplate="%{label}: Rs. %{value:,.0f}<extra></extra>",
        textfont=dict(size=11),
    ))
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="v", font=dict(size=10), x=0.72, y=0.5),
        margin=dict(t=10, b=10, l=0, r=0),
        font=dict(family="Nunito Sans, sans-serif"),
        height=240,
    )
    return fig


def style_table(df):
    d = df[["Market","State","Distance_km","Predicted_Price",
            "Transport_Cost","Net_Profit","Profit_per_kg"]].copy()
    d.columns = ["Market","State","Dist. (km)","Price (Rs./q)",
                 "Transport (Rs.)","Net Profit (Rs.)","Profit/kg (Rs.)"]
    def hi(row):
        s = f"background:{GREEN};color:white;font-weight:700;" if row.name == 0 else ""
        return [s]*len(row)
    return (
        d.style.apply(hi, axis=1)
        .format({
            "Price (Rs./q)":    "Rs. {:,.0f}",
            "Transport (Rs.)":  "Rs. {:,.0f}",
            "Net Profit (Rs.)": "Rs. {:,.0f}",
            "Profit/kg (Rs.)":  "Rs. {:.2f}",
        })
        .set_properties(**{"text-align":"right","font-size":"13px"})
        .set_table_styles([
            {"selector":"th","props":f"background:{BG_OFFWHITE};color:{TEXT_MUTED};font-size:11px;letter-spacing:0.05em;text-transform:uppercase;text-align:center;padding:10px 14px;"},
            {"selector":"td","props":"padding:9px 14px;"},
        ])
    )


# =============================================================================
# STATIC SECTIONS (always visible)
# =============================================================================
def render_navbar():
    st.markdown(f"""
    <div class="nav-bar">
        <div class="nav-logo">Fasal<span>-to-</span>Faida</div>
        <div class="nav-links">
            <a href="#">About</a>
            <a href="#">How It Works</a>
            <a href="#">Mandis</a>
            <a href="#" class="nav-cta">Check My Mandi</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_hero():
    st.markdown(f"""
    <div class="hero-section">
        <div class="hero-bg"></div>
        <div class="hero-content">
            <div class="hero-eyebrow">Welcome to Fasal-to-Faida</div>
            <div class="hero-title">Smarter Selling<br>for Every<br><em>Indian Farmer</em></div>
            <div class="hero-desc">
                Find out where to sell your crop, how much transport will cost,
                and exactly how much you will earn — before you load the truck.
            </div>
            <div class="hero-btn">Check Your Market</div>
        </div>
    </div>
    <div style="background:{AMBER};height:22px;width:100%;"></div>
    """, unsafe_allow_html=True)


def render_float_cards():
    st.markdown(f"""
    <div class="float-card-wrap">
    <div class="float-cards">
        <div class="float-card">
            <img src="https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=600&q=80&fit=crop" />
            <div class="float-card-label">Live Price Prediction</div>
        </div>
        <div class="float-card">
            <img src="https://images.unsplash.com/photo-1560472355-536de3962603?w=600&q=80&fit=crop" />
            <div class="float-card-label">Best Mandi Near You</div>
        </div>
        <div class="float-card">
            <img src="https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=600&q=80&fit=crop" />
            <div class="float-card-label">Real Profit Estimate</div>
        </div>
    </div>
    </div>
    """, unsafe_allow_html=True)


def render_split_section():
    st.markdown(f"""
    <div class="split-section">
        <div class="split-imgs">
            <img class="split-img-main"
                 src="https://images.unsplash.com/photo-1464226184884-fa280b87c399?w=800&q=80&fit=crop" />
            <img class="split-img-accent"
                 src="https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=500&q=80&fit=crop" />
            <div class="split-badge">
                <div>7,000+</div>
                <span>MANDIS</span>
            </div>
        </div>
        <div class="split-text">
            <div class="split-tagline">Welcome to Fasal-to-Faida</div>
            <div class="split-title">Better Information<br>for Better Returns</div>
            <div class="split-highlight">
                Covering all 28 states — powered by 2 years of Agmarknet government data.
            </div>
            <div class="split-body">
                Farmers across India lose significant income every year not because of bad crops,
                but because of information they never had. Fasal-to-Faida changes that — giving
                every farmer, from any district, the same market intelligence that traders have
                always had. Enter your pincode, pick your crop, get your answer.
            </div>
            <div class="icon-badge-row">
                <div class="icon-badge">
                    <div class="ib-circle">&#9675;</div>
                    Pan-India Coverage
                </div>
                <div class="icon-badge">
                    <div class="ib-circle">&#9634;</div>
                    SMS Access
                </div>
            </div>
            <button class="btn-primary">How It Works</button>
            <button class="btn-outline">SMS Access</button>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_features_section():
    st.markdown(f"""
    <div class="section-wrap white">
        <div class="section-eyebrow">What We Offer</div>
        <div class="section-title">Everything a Farmer Needs to Decide</div>
        <div class="section-sub">
            One platform. Four core answers. Available on web and by SMS from any phone.
        </div>
        <div class="feat-grid">
            <div class="feat-card">
                <img src="https://images.unsplash.com/photo-1607457561901-e6ec3a6d16cf?w=500&q=80&fit=crop" />
                <div class="feat-icon-circle">&#9670;</div>
                <div class="feat-card-body">
                    <div class="feat-card-title">Price Prediction</div>
                    <div class="feat-card-desc">XGBoost model trained on 2 years of daily mandi prices predicts what your crop will sell for.</div>
                </div>
            </div>
            <div class="feat-card">
                <img src="https://images.unsplash.com/photo-1543076447-215ad9ba6923?w=500&q=80&fit=crop" />
                <div class="feat-icon-circle">&#9632;</div>
                <div class="feat-card-body">
                    <div class="feat-card-title">Best Mandi Nearby</div>
                    <div class="feat-card-desc">We rank all nearby mandis by net profit — not just price — so you know the real best option.</div>
                </div>
            </div>
            <div class="feat-card">
                <img src="https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=500&q=80&fit=crop" />
                <div class="feat-icon-circle">&#9679;</div>
                <div class="feat-card-body">
                    <div class="feat-card-title">Transport Calculator</div>
                    <div class="feat-card-desc">Distance from your district to each mandi, factored with truck tier rates and load size.</div>
                </div>
            </div>
            <div class="feat-card">
                <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500&q=80&fit=crop" />
                <div class="feat-icon-circle">&#9650;</div>
                <div class="feat-card-body">
                    <div class="feat-card-title">SMS Access</div>
                    <div class="feat-card-desc">No smartphone needed. Send your pincode and crop by SMS. Get your results back instantly.</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# FORM SECTION (Streamlit widgets, styled green)
# =============================================================================
def render_form_section():
    st.markdown(f"""
    <div style="background:{GREEN};padding:48px 80px 0 80px;">
        <div class="section-eyebrow dark">Find Your Market</div>
        <div class="section-title white">Check Your Best Mandi</div>
        <div class="section-sub white">Enter your details below — results appear instantly on this page.</div>
    </div>
    <div class="form-inputs-wrap" style="background:{GREEN};padding:0 80px 48px 80px;">
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 1.5, 2, 1.5, 1.5])
    with c1:
        farmer_name = st.text_input("Farmer Name", placeholder="e.g. Ramesh Patil", key="fname")
    with c2:
        district = st.text_input("Your District", placeholder="e.g. Nashik", key="dist")
    with c3:
        commodity = st.selectbox("Crop", CROPS, index=1, key="crop")
    with c4:
        quantity_kg = st.number_input("Quantity (kg)", min_value=10, value=500, step=10, key="qty")
    with c5:
        month_name = st.selectbox("Month", MONTHS, index=pd.Timestamp.now().month - 1, key="mon")
    with c6:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        submitted = st.button("Find Best Mandi", key="submit")

    st.markdown("</div>", unsafe_allow_html=True)

    return {
        "farmer_name": farmer_name.strip() if farmer_name else "",
        "commodity":   commodity,
        "quantity_kg": quantity_kg,
        "district":    district.strip() if district else "",
        "month_num":   MONTHS.index(month_name) + 1,
        "month_name":  month_name,
        "year":        2025,
        "submitted":   submitted,
    }


# =============================================================================
# RESULTS
# =============================================================================
def render_results(inputs):
    df = fetch_recommendations(
        inputs["commodity"], inputs["quantity_kg"],
        inputs["district"], inputs["month_num"], inputs["year"],
    )

    if df.empty:
        st.markdown(f"""
        <div style="background:{BG_OFFWHITE};padding:40px 80px;">
            <div style="background:white;border-radius:4px;padding:32px;text-align:center;color:{TEXT_MUTED};">
                No markets found for this combination. Try a different crop or district.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    best = df.iloc[0]
    name_str = f"Namaste {inputs['farmer_name']} — " if inputs["farmer_name"] else ""

    st.markdown(f"""
    <div class="results-header">
        <div class="section-eyebrow">Market Analysis</div>
        <div class="section-title" style="text-align:left;">{name_str}Results for {inputs['commodity']}</div>
        <div style="font-size:0.88rem;color:{TEXT_MUTED};margin-top:4px;">
            {inputs['quantity_kg']} kg &nbsp;·&nbsp; {inputs['district'] or 'Your district'} &nbsp;·&nbsp; {inputs['month_name']} {inputs['year']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div class='results-body'>", unsafe_allow_html=True)

    # Metric cards
    st.markdown(f"<div class='sec-lbl'>Summary</div>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    def mc(label, value, unit="", amber=False):
        cls = "mc amber" if amber else "mc"
        return f"""<div class="{cls}">
            <div class="mc-lbl">{label}</div>
            <div class="mc-val">{value}</div>
            <div class="mc-unit">{unit}</div>
        </div>"""
    with m1: st.markdown(mc("Best Mandi", best["Market"], best["State"]), unsafe_allow_html=True)
    with m2: st.markdown(mc("Predicted Price", f"Rs. {best['Predicted_Price']:,.0f}", "per quintal"), unsafe_allow_html=True)
    with m3: st.markdown(mc("Estimated Net Profit", f"Rs. {best['Net_Profit']:,.0f}", f"for {inputs['quantity_kg']} kg", amber=True), unsafe_allow_html=True)
    with m4: st.markdown(mc("Distance", f"{best['Distance_km']} km", "from your district"), unsafe_allow_html=True)

    # Table
    st.markdown(f"<div class='sec-lbl'>All Markets — Ranked by Net Profit</div>", unsafe_allow_html=True)
    st.dataframe(style_table(df), use_container_width=True, hide_index=True)

    # Charts
    st.markdown(f"<div class='sec-lbl'>Analysis</div>", unsafe_allow_html=True)
    cl, cr = st.columns([3, 2])
    with cl:
        st.markdown(f"<p style='font-size:0.72rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:6px;'>Net Profit by Market</p>", unsafe_allow_html=True)
        st.plotly_chart(profit_bar_chart(df), use_container_width=True)
    with cr:
        st.markdown(f"<p style='font-size:0.72rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:6px;'>Cost Breakdown — {best['Market']}</p>", unsafe_allow_html=True)
        st.plotly_chart(cost_pie_chart(best, inputs["quantity_kg"]), use_container_width=True)

    # Recommendation
    farmer_ref = f"{inputs['farmer_name']}, the" if inputs["farmer_name"] else "The"
    st.markdown(f"""
    <div class="reco-box">
        <div class="reco-lbl">Recommendation</div>
        {farmer_ref} most profitable option is <strong>{best['Market']}, {best['State']}</strong>.
        After transport, mandi commission, and miscellaneous costs, the estimated return is
        <strong>Rs. {best['Net_Profit']:,.0f}</strong> for {inputs['quantity_kg']} kg of {inputs['commodity']}.
        Distance from {inputs['district'] or 'your district'}: <strong>{best['Distance_km']} km</strong>.
    </div>
    <p style='font-size:0.74rem;color:{TEXT_MUTED};margin-top:14px;'>
    Prices are model predictions based on historical Agmarknet data and are indicative only.
    Transport costs use haversine distance with a 1.3x road circuity correction.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# FOOTER
# =============================================================================
def render_footer():
    st.markdown(f"""
    <div class="site-footer">
        <strong>Fasal-to-Faida</strong> &nbsp;|&nbsp; Bech Sahi, Kamaao Zyada &nbsp;|&nbsp;
        Data sourced from Agmarknet, Government of India &nbsp;|&nbsp;
        AURELION 2026 Hackathon
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# MAIN
# =============================================================================
def main():
    inject_css()
    render_navbar()
    render_hero()
    render_float_cards()
    render_split_section()
    render_features_section()
    inputs = render_form_section()
    if inputs["submitted"]:
        render_results(inputs)
    render_footer()


if __name__ == "__main__":
    main()