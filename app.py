# =============================================================================
# app.py — Fasal-to-Faida  |  Bech Sahi, Kamaao Zyada
# Agrikon-inspired UI — integrated with live XGBoost price model
#
# pip install streamlit pandas numpy matplotlib joblib xgboost scikit-learn
# streamlit run app.py
# =============================================================================

import html
import io
import logging
import random
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

import geo

log = logging.getLogger("fasal.web")

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
BG_WHITE    = "#FFFFFF"
BG_OFFWHITE = "#F7F4EF"
TEXT_DARK   = "#1A1A1A"
TEXT_MUTED  = "#666666"
BORDER      = "#E0DAD0"

MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]
CROPS  = ["Tomato","Onion","Potato","Wheat","Rice"]
MAX_DISTANCE_KM = 200   # same as SMS

# Fallback dummy markets (used only when model can't find results)
DUMMY_MARKETS = [
    ("Azadpur",    "Delhi",       "North West Delhi"),
    ("Lasalgaon",  "Maharashtra", "Nashik"),
    ("Vashi",      "Maharashtra", "Navi Mumbai"),
    ("Kothi",      "Punjab",      "Amritsar"),
    ("Bowenpally", "Telangana",   "Hyderabad"),
]

# =============================================================================
# CSS
# =============================================================================
def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;900&family=Nunito+Sans:wght@300;400;500;600;700&display=swap');

    html, body, .stApp {{
        background-color: {BG_OFFWHITE};
        font-family: 'Nunito Sans', sans-serif;
        color: {TEXT_DARK};
    }}
    .block-container {{ padding: 0 !important; max-width: 100% !important; }}
    [data-testid="stSidebar"] {{ display: none; }}
    header[data-testid="stHeader"] {{ background: transparent; }}
    #MainMenu, footer, header {{ visibility: hidden; }}

    /* ── Widget labels & inputs — always dark ─────────────────── */
    .stTextInput > label, .stNumberInput > label,
    .stSelectbox > label, .stMultiSelect > label, .stSlider > label {{
        color: {TEXT_DARK} !important;
        font-family: 'Nunito Sans', sans-serif !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
    }}
    .stTextInput input, .stNumberInput input {{
        color: {TEXT_DARK} !important;
        background: #FFFFFF !important;
        border: 1px solid {BORDER} !important;
        font-family: 'Nunito Sans', sans-serif !important;
        font-size: 0.9rem !important;
        border-radius: 4px !important;
    }}
    .stTextInput input::placeholder, .stNumberInput input::placeholder {{
        color: #AAAAAA !important;
    }}
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
    [data-baseweb="popover"] li, [data-baseweb="menu"] li {{
        color: {TEXT_DARK} !important; background: white !important;
    }}
    [data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover {{
        background: {BG_OFFWHITE} !important;
    }}
    .stNumberInput button {{
        color: {TEXT_DARK} !important; background: {BG_OFFWHITE} !important;
        border-color: {BORDER} !important;
    }}
    .stMarkdown, .stMarkdown p, .stMarkdown span {{ color: {TEXT_DARK}; }}

    /* ── Nav ───────────────────────────────────────────────────── */
    .nav-bar {{
        background: {GREEN}; display: flex; align-items: center;
        justify-content: space-between; padding: 0 48px; height: 64px;
        position: sticky; top: 0; z-index: 100;
        box-shadow: 0 2px 12px rgba(0,0,0,0.15);
    }}
    .nav-logo {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.5rem; font-weight: 700; color: white;
    }}
    .nav-logo span {{ color: {AMBER}; }}
    .nav-links {{ display: flex; gap: 32px; align-items: center; }}
    .nav-links a {{
        color: rgba(255,255,255,0.85); font-size: 0.88rem; font-weight: 600;
        letter-spacing: 0.04em; text-decoration: none; text-transform: uppercase;
    }}
    .nav-cta {{
        background: {AMBER}; color: {GREEN} !important;
        padding: 8px 20px; border-radius: 3px; font-weight: 700 !important;
    }}

    /* ── Hero ──────────────────────────────────────────────────── */
    .hero-section {{
        position: relative; width: 100%; height: 480px;
        overflow: hidden; background: {GREEN};
    }}
    .hero-bg {{
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background-image: url('https://images.unsplash.com/photo-1500595046743-cd271d694d30?w=1600&q=80&fit=crop');
        background-size: cover; background-position: center 40%; opacity: 0.5;
    }}
    .hero-content {{
        position: relative; z-index: 2; padding: 72px 80px; max-width: 620px;
    }}
    .hero-eyebrow {{
        font-size: 0.78rem; font-weight: 700; letter-spacing: 0.14em;
        text-transform: uppercase; color: {AMBER}; margin-bottom: 14px;
    }}
    .hero-title {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 3.4rem; font-weight: 900; color: white;
        line-height: 1.12; margin-bottom: 18px;
        text-shadow: 0 2px 20px rgba(0,0,0,0.3);
    }}
    .hero-title em {{ color: {AMBER}; font-style: normal; }}
    .hero-desc {{
        font-size: 1.0rem; color: rgba(255,255,255,0.88);
        line-height: 1.7; margin-bottom: 24px; max-width: 460px;
    }}
    .hero-cta-btn {{
        display: inline-block; background: {AMBER}; color: {GREEN} !important;
        font-family: 'Nunito Sans', sans-serif; font-weight: 700;
        font-size: 0.95rem; letter-spacing: 0.06em; text-transform: uppercase;
        text-decoration: none; padding: 14px 32px; border-radius: 4px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.25); transition: background 0.2s;
    }}
    .hero-cta-btn:hover {{ background: {AMBER_DARK} !important; color: white !important; }}

    /* ── Section headings ──────────────────────────────────────── */
    .section-eyebrow {{
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em;
        text-transform: uppercase; color: {GREEN_LIGHT};
        margin-bottom: 10px; text-align: center;
    }}
    .section-eyebrow.dark {{ color: {AMBER}; }}
    .section-title {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 2.2rem; font-weight: 700; color: {GREEN};
        line-height: 1.2; margin-bottom: 12px; text-align: center;
    }}
    .section-title.white {{ color: white; }}
    .section-sub {{
        font-size: 1.0rem; color: {TEXT_MUTED}; text-align: center;
        max-width: 560px; margin: 0 auto 32px; line-height: 1.7;
    }}
    .section-sub.white {{ color: rgba(255,255,255,0.75); }}

    /* ── Feature cards ─────────────────────────────────────────── */
    .feat-grid {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 24px; }}
    .feat-card {{
        background: white; border-radius: 6px; overflow: hidden;
        box-shadow: 0 4px 18px rgba(0,0,0,0.08); position: relative;
    }}
    .feat-card img {{ width: 100%; height: 150px; object-fit: cover; }}
    .feat-icon-circle {{
        position: absolute; top: 127px; left: 50%; transform: translateX(-50%);
        width: 44px; height: 44px; border-radius: 50%; background: {GREEN};
        border: 3px solid white; display: flex; align-items: center;
        justify-content: center; font-size: 17px; z-index: 2;
    }}
    .feat-card-body {{ padding: 32px 18px 20px; text-align: center; }}
    .feat-card-title {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.0rem; font-weight: 700; color: {GREEN}; margin-bottom: 7px;
    }}
    .feat-card-desc {{ font-size: 0.84rem; color: {TEXT_MUTED}; line-height: 1.6; }}

    /* ── Form section (green bg) ───────────────────────────────── */
    div.stButton > button {{
        background: {AMBER} !important; color: {GREEN} !important;
        font-family: 'Nunito Sans', sans-serif !important; font-weight: 700 !important;
        letter-spacing: 0.06em !important; text-transform: uppercase !important;
        border: none !important; border-radius: 4px !important;
        padding: 0.65rem 2rem !important; font-size: 0.88rem !important; width: 100% !important;
    }}
    div.stButton > button:hover {{
        background: {AMBER_DARK} !important; color: white !important;
    }}

    /* ── Results ───────────────────────────────────────────────── */
    .results-header {{ background: {BG_OFFWHITE}; padding: 40px 80px 12px; }}
    .results-body   {{ background: {BG_OFFWHITE}; padding: 0 80px 60px; }}

    /* ── Metric card ───────────────────────────────────────────── */
    .mc {{
        background: white; border-top: 4px solid {GREEN}; border-radius: 4px;
        padding: 20px 18px 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }}
    .mc.amber {{ border-top-color: {AMBER_DARK}; }}
    .mc.red   {{ border-top-color: #E53E3E; }}
    .mc-lbl {{
        font-size: 0.66rem; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; color: {TEXT_MUTED}; margin-bottom: 8px;
    }}
    .mc-val {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.9rem; font-weight: 600; color: {GREEN}; line-height: 1;
    }}
    .mc.amber .mc-val {{ color: {AMBER_DARK}; }}
    .mc.red   .mc-val {{ color: #E53E3E; }}
    .mc-unit {{ font-size: 0.7rem; color: {TEXT_MUTED}; margin-top: 5px; }}

    /* ── Section divider label ─────────────────────────────────── */
    .sec-lbl {{
        font-size: 0.68rem; font-weight: 700; letter-spacing: 0.12em;
        text-transform: uppercase; color: {TEXT_MUTED};
        border-bottom: 1px solid {BORDER}; padding-bottom: 6px; margin: 32px 0 14px;
    }}

    /* ── Recommendation box ────────────────────────────────────── */
    .reco-box {{
        background: {GREEN}; color: white; border-radius: 4px;
        padding: 22px 28px; margin-top: 14px; font-size: 1.0rem; line-height: 1.7;
    }}
    .reco-box strong {{ font-weight: 700; color: {AMBER}; }}
    .reco-lbl {{
        font-size: 0.66rem; letter-spacing: 0.12em; text-transform: uppercase;
        opacity: 0.6; margin-bottom: 8px;
    }}

    /* ── Spinner / info ────────────────────────────────────────── */
    .loading-box {{
        background: white; border-radius: 6px; padding: 32px;
        text-align: center; font-size: 1.1rem; color: {TEXT_MUTED};
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }}

    /* ── Footer ────────────────────────────────────────────────── */
    .site-footer {{
        background: {GREEN}; color: rgba(255,255,255,0.6);
        text-align: center; padding: 22px 48px; font-size: 0.8rem;
    }}
    .site-footer strong {{ color: white; }}

    /* ── Table ─────────────────────────────────────────────────── */
    div[data-testid="stDataFrame"] {{
        border: 1px solid {BORDER} !important; border-radius: 4px;
    }}
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# DUMMY DATA (fallback only)
# =============================================================================
def make_dummy_df(commodity="Onion", quantity_kg=500):
    random.seed(42)
    rows = []
    for market, state, district in DUMMY_MARKETS:
        dist_km       = random.randint(20, 150)
        price_per_q   = random.randint(1200, 3500)
        qty_q         = quantity_kg / 100
        gross_revenue = round(price_per_q * qty_q, 2)
        transport     = round(dist_km * 15 + 300, 2)
        mandi_fee     = round(gross_revenue * 0.02, 2)
        misc_costs    = round(qty_q * 10, 2)
        total_costs   = round(transport + mandi_fee + misc_costs, 2)
        net_profit    = round(gross_revenue - total_costs, 2)
        profit_per_kg = round(net_profit / quantity_kg, 2)
        rows.append({
            "market": market, "state": state, "district": district,
            "distance_km": dist_km, "predicted_price": price_per_q,
            "gross_revenue": gross_revenue, "transport_cost": transport,
            "mandi_fee": mandi_fee, "misc_costs": misc_costs,
            "total_costs": total_costs, "net_profit": net_profit,
            "profit_per_kg": profit_per_kg,
        })
    return sorted(rows, key=lambda x: x["net_profit"], reverse=True)


# =============================================================================
# MODEL CALL
# =============================================================================
def get_recommendations(commodity, quantity_kg, loc, month_num, year):
    """Call real model; fall back to dummy on any error. loc = geo.lookup_pincode()."""
    district, state = loc["district"], loc["state"]
    try:
        from recommender import recommend
        results = recommend(
            commodity        = commodity,
            quantity_kg      = quantity_kg,
            farmer_lat       = loc["lat"],
            farmer_lon       = loc["lon"],
            target_month     = month_num,
            target_year      = year,
            max_distance_km  = MAX_DISTANCE_KM,
            top_n            = 3,            # same as SMS
            farmer_district  = district,
        )
        if results and len(results) > 0:
            return results, False   # (data, is_dummy)
        # Model ran but found 0 markets — not a crash, just no results
        return [], False
    except Exception:
        log.exception("recommend() failed (commodity=%s district=%s state=%s month=%s)",
                      commodity, district, state, month_num)
        return make_dummy_df(commodity, quantity_kg), True


# =============================================================================
# CHARTS
# =============================================================================
def _fig_to_img(fig):
    """Convert a matplotlib Figure to a PNG bytes buffer."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=130)
    buf.seek(0)
    plt.close(fig)
    return buf


def profit_bar_chart(records):
    """Horizontal bar — Net Profit per market, best highlighted (Matplotlib)."""
    pairs = sorted(zip(
        [r["net_profit"] for r in records],
        [r["market"]    for r in records],
    ))
    profits_s = [p for p, _ in pairs]
    markets_s = [m for _, m in pairs]
    colors_s  = [AMBER_DARK if m == records[0]["market"] else GREEN_LIGHT
                 for m in markets_s]

    fig, ax = plt.subplots(figsize=(7, max(2.5, len(markets_s) * 0.45)))
    bars = ax.barh(markets_s, profits_s, color=colors_s, edgecolor="none", height=0.55)
    for bar, val in zip(bars, profits_s):
        ax.text(bar.get_width() + max(profits_s) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"Rs. {val:,.0f}", va="center", ha="left", fontsize=8, color=TEXT_DARK)
    ax.set_xlabel("Net Profit (Rs.)", fontsize=8, color=TEXT_MUTED)
    ax.tick_params(axis="both", labelsize=8, colors=TEXT_DARK)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    return _fig_to_img(fig)


def cost_waterfall_chart(best):
    """Waterfall: Gross Revenue → costs → Net Profit (Matplotlib)."""
    labels  = ["Gross\nRevenue", "Transport", "Mandi Fee", "Misc", "Net Profit"]
    amounts = [
        best["gross_revenue"],
        -best["transport_cost"],
        -best["mandi_fee"],
        -best["misc_costs"],
        best["net_profit"],
    ]
    bottoms, running = [], 0
    for i, a in enumerate(amounts):
        if i == 0 or i == len(amounts) - 1:
            bottoms.append(0)
        else:
            bottoms.append(running)
        if i < len(amounts) - 1:
            running += a

    bar_colors = []
    for i, a in enumerate(amounts):
        if i == 0:
            bar_colors.append(GREEN_LIGHT)
        elif i == len(amounts) - 1:
            bar_colors.append(GREEN)
        else:
            bar_colors.append(AMBER_DARK if a < 0 else GREEN_LIGHT)

    fig, ax = plt.subplots(figsize=(6, 3.5))
    bars = ax.bar(labels, [abs(a) for a in amounts], bottom=bottoms,
                  color=bar_colors, edgecolor="none", width=0.5)
    for bar, val in zip(bars, amounts):
        sign = "-" if val < 0 else ""
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_y() + bar.get_height() + max(abs(a) for a in amounts) * 0.01,
                f"{sign}Rs.{abs(val):,.0f}", ha="center", va="bottom", fontsize=7, color=TEXT_DARK)
    ax.set_ylabel("Amount (Rs.)", fontsize=8, color=TEXT_MUTED)
    ax.tick_params(axis="both", labelsize=8, colors=TEXT_DARK)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    return _fig_to_img(fig)


def cost_pie_chart(best):
    """Donut: how the gross revenue is split (Matplotlib)."""
    labels = ["Net Profit", "Transport", "Mandi Fee", "Misc"]
    values = [max(best["net_profit"], 0),
              best["transport_cost"], best["mandi_fee"], best["misc_costs"]]
    colors = [GREEN, AMBER_DARK, GREEN_LIGHT, "#C5BFB0"]
    fig, ax = plt.subplots(figsize=(5.5, 3.5))

    def autopct_fn(pct):
        return f"{pct:.0f}%" if pct >= 5 else ""

    wedges, texts, autotexts = ax.pie(
        values, labels=None, colors=colors, autopct=autopct_fn,
        pctdistance=0.75, startangle=90,
        wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2),
    )
    for at in autotexts:
        at.set_fontsize(8)
        at.set_color("white")
        at.set_fontweight("bold")
    ax.legend(labels, loc="center right", bbox_to_anchor=(1.3, 0.5),
              fontsize=8, frameon=False)
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    return _fig_to_img(fig)


def price_comparison_chart(records):
    """Bar — Predicted price per quintal across markets (Matplotlib)."""
    markets = [r["market"] for r in records]
    prices  = [r["predicted_price"] for r in records]
    colors  = [AMBER if i == 0 else GREEN_MID for i in range(len(records))]

    fig, ax = plt.subplots(figsize=(7, 3))
    bars = ax.bar(markets, prices, color=colors, edgecolor="none", width=0.55)
    for bar, val in zip(bars, prices):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(prices) * 0.01,
                f"Rs.{val:,.0f}", ha="center", va="bottom", fontsize=7, color=TEXT_DARK)
    ax.set_ylabel("Price (Rs./quintal)", fontsize=8, color=TEXT_MUTED)
    ax.tick_params(axis="x", labelsize=7, rotation=20, colors=TEXT_DARK)
    ax.tick_params(axis="y", labelsize=8, colors=TEXT_DARK)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    return _fig_to_img(fig)


def distance_vs_profit_scatter(records):
    """Scatter: distance vs net profit — bubble sized by price (Matplotlib)."""
    fig, ax = plt.subplots(figsize=(7, 3.5))
    for i, r in enumerate(records):
        is_best = (i == 0)
        size = max(r["predicted_price"] / 30, 80)
        color = AMBER_DARK if is_best else GREEN_LIGHT
        ax.scatter(r["distance_km"], r["net_profit"], s=size, color=color,
                   edgecolors="white", linewidths=1.5, zorder=3, alpha=0.9)
        ax.annotate(r["market"],
                    xy=(r["distance_km"], r["net_profit"]),
                    xytext=(0, 8), textcoords="offset points",
                    ha="center", fontsize=7, color=TEXT_DARK)
    ax.set_xlabel("Distance from your district (km)", fontsize=8, color=TEXT_MUTED)
    ax.set_ylabel("Net Profit (Rs.)", fontsize=8, color=TEXT_MUTED)
    ax.tick_params(labelsize=8, colors=TEXT_DARK)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_facecolor("#FAFAF8")
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    return _fig_to_img(fig)


# =============================================================================
# STYLED TABLE
# =============================================================================
def style_table(records):
    rows = []
    for r in records:
        rows.append({
            "Market":           r["market"],
            "State":            r["state"],
            "Dist. (km)":       r["distance_km"],
            "Price (Rs./q)":    r["predicted_price"],
            "Transport (Rs.)":  r["transport_cost"],
            "Net Profit (Rs.)": r["net_profit"],
            "Profit/kg (Rs.)":  r["profit_per_kg"],
        })
    df = pd.DataFrame(rows)
    # Format numeric columns as strings for display (no jinja2 needed)
    df["Price (Rs./q)"]    = df["Price (Rs./q)"].apply(lambda x: f"Rs. {x:,.0f}")
    df["Transport (Rs.)"] = df["Transport (Rs.)"].apply(lambda x: f"Rs. {x:,.0f}")
    df["Net Profit (Rs.)"] = df["Net Profit (Rs.)"].apply(lambda x: f"Rs. {x:,.0f}")
    df["Profit/kg (Rs.)"] = df["Profit/kg (Rs.)"].apply(lambda x: f"Rs. {x:.2f}")
    df["Dist. (km)"]       = df["Dist. (km)"].apply(lambda x: f"{x:.0f} km")
    return df


# =============================================================================
# STATIC SECTIONS
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
            <div class="hero-eyebrow">AI-Powered Market Intelligence</div>
            <div class="hero-title">Smarter Selling<br>for Every<br><em>Indian Farmer</em></div>
            <div class="hero-desc">
                Our XGBoost model predicts crop prices at every mandi near you,
                then calculates real transport costs and net profit — so you always
                know where to sell before you load the truck.
            </div>
            <a href="#check-your-best-mandi" class="hero-cta-btn">🌾 Check My Mandi</a>
        </div>
    </div>
    <div style="background:{AMBER};height:5px;width:100%;"></div>
    """, unsafe_allow_html=True)


def render_features_section():
    st.markdown(f"""
    <div style="background:{BG_WHITE};padding:56px 72px;">
        <div class="section-eyebrow">What We Offer</div>
        <div class="section-title">Four Numbers That Change Everything</div>
        <div class="section-sub">
            One query. Real XGBoost predictions. Ranked by actual net profit after all costs.
        </div>
        <div class="feat-grid">
            <div class="feat-card">
                <img src="https://images.unsplash.com/photo-1607457561901-e6ec3a6d16cf?w=500&q=80&fit=crop" />
                <div class="feat-icon-circle">📈</div>
                <div class="feat-card-body">
                    <div class="feat-card-title">Price Prediction</div>
                    <div class="feat-card-desc">XGBoost model trained on 2 years of Agmarknet data predicts the expected modal price for your crop.</div>
                </div>
            </div>
            <div class="feat-card">
                <img src="https://images.unsplash.com/photo-1543076447-215ad9ba6923?w=500&q=80&fit=crop" />
                <div class="feat-icon-circle">🏆</div>
                <div class="feat-card-body">
                    <div class="feat-card-title">Best Mandi Rank</div>
                    <div class="feat-card-desc">We evaluate every reachable mandi and rank them by net profit — not just advertised price.</div>
                </div>
            </div>
            <div class="feat-card">
                <img src="https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=500&q=80&fit=crop" />
                <div class="feat-icon-circle">🚚</div>
                <div class="feat-card-body">
                    <div class="feat-card-title">Transport Cost</div>
                    <div class="feat-card-desc">Haversine distance × 1.3 road correction, then tiered truck rates based on your load size.</div>
                </div>
            </div>
            <div class="feat-card">
                <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500&q=80&fit=crop" />
                <div class="feat-icon-circle">💰</div>
                <div class="feat-card-body">
                    <div class="feat-card-title">Net Profit Estimate</div>
                    <div class="feat-card-desc">Gross revenue minus transport, 2% mandi commission, and misc costs — your real take-home.</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# FORM SECTION
# =============================================================================
def render_form_section():
    # Anchor target so the hero CTA can link here
    st.markdown("""
    <div id="check-your-best-mandi" style="scroll-margin-top:70px;"></div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:{GREEN};padding:60px 100px 0 100px;">
        <div class="section-eyebrow dark">Find Your Market</div>
        <div class="section-title white" style="font-size:2.8rem;">Check Your Best Mandi</div>
        <div class="section-sub white" style="font-size:1.05rem;max-width:680px;">
            Enter your 6-digit pincode and crop details — our XGBoost model instantly
            evaluates every reachable mandi and ranks them by real net profit after all costs.
        </div>
    </div>
    <div style="background:{GREEN};padding:16px 100px 56px 100px;">
    """, unsafe_allow_html=True)

    # Row 1: name + pincode + crop
    c1, c2, c3 = st.columns([2.5, 2.5, 2])
    with c1:
        farmer_name = st.text_input("Farmer Name (optional)", placeholder="e.g. Ramesh Patil", key="fname")
    with c2:
        pincode = st.text_input(
            "Your Pincode *",
            placeholder="e.g. 641001",
            max_chars=6,
            key="pincode"
        )
    with c3:
        # Once a known pincode is typed, only offer crops traded at a mandi in range
        crop_options = CROPS
        pin_loc = geo.lookup_pincode(pincode.strip()) if pincode else {"valid": False}
        if pin_loc["valid"]:
            crop_options = geo.available_crops(pin_loc["lat"], pin_loc["lon"],
                                               MAX_DISTANCE_KM, order=CROPS) or CROPS
        default = crop_options.index("Onion") if "Onion" in crop_options else 0
        commodity = st.selectbox("Crop *", crop_options, index=default, key="crop")

    # Row 2 — same inputs as SMS: qty bucket + month + submit
    #   QTY_MAP {1:250, 2:750, 3:2500, 4:6000}  (identical to sms_handler.py)
    QTY_OPTIONS = {
        "1 — Below 500 kg  (250 kg)": 250,
        "2 — 500-1000 kg   (750 kg)": 750,
        "3 — 1000-5000 kg (2500 kg)": 2500,
        "4 — Above 5000 kg (6000 kg)": 6000,
    }
    c4, c5, c6 = st.columns([2.5, 2.5, 1.8])
    with c4:
        qty_label  = st.selectbox("Quantity *", list(QTY_OPTIONS.keys()), index=1, key="qty")
        quantity_kg = QTY_OPTIONS[qty_label]
    with c5:
        month_name = st.selectbox("Month to Sell *", MONTHS,
                                  index=pd.Timestamp.now().month - 1, key="mon")
    with c6:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        submitted = st.button("🔍 Find Best Mandi", key="submit")

    st.markdown("</div>", unsafe_allow_html=True)

    return {
        "farmer_name": farmer_name.strip() if farmer_name else "",
        "commodity":   commodity,
        "quantity_kg": quantity_kg,          # 250 / 750 / 2500 / 6000
        "pincode":     pincode.strip() if pincode else "",
        "month_num":   MONTHS.index(month_name) + 1,
        "month_name":  month_name,
        "year":        pd.Timestamp.now().year,   # always current year, same as SMS
        "submitted":   submitted,
    }


# =============================================================================
# METRIC CARD HTML
# =============================================================================
def mc(label, value, unit="", variant=""):
    cls = f"mc {variant}".strip()
    return f"""<div class="{cls}">
        <div class="mc-lbl">{label}</div>
        <div class="mc-val">{value}</div>
        <div class="mc-unit">{unit}</div>
    </div>"""


# =============================================================================
# RESULTS SECTION
# =============================================================================
def render_results(inputs):
    pincode = inputs["pincode"]

    # ── Validate pincode ───────────────────────────────────────────
    import re as _re
    if not pincode:
        st.warning("⚠️ Please enter your 6-digit pincode.")
        return
    if not _re.fullmatch(r"\d{6}", pincode):
        st.warning("⚠️ Pincode must be exactly 6 digits. Example: 641001")
        return

    # ── Resolve pincode → canonical district + state + coordinates ──
    loc = geo.lookup_pincode(pincode)
    if not loc["valid"]:
        st.warning(
            f"⚠️ Pincode **{pincode}** was not found in our database. "
            "Please double-check and try again."
        )
        return

    district, state = loc["district"], loc["state"]

    # Show resolved location
    st.info(f"📍 **{district}, {state}** (pincode {pincode})")

    # ── Loading spinner ────────────────────────────────────────────
    with st.spinner(f"🔍 Evaluating mandis for {inputs['commodity']} near {district}…"):
        records, is_dummy = get_recommendations(
            inputs["commodity"], inputs["quantity_kg"], loc,
            inputs["month_num"], inputs["year"],
        )

    if not records:
        st.markdown(f"""
        <div style="background:{BG_OFFWHITE};padding:40px 80px;">
            <div style="background:white;border-radius:4px;padding:32px;text-align:center;color:{TEXT_MUTED};">
                <b>No markets found</b> within {MAX_DISTANCE_KM} km of <b>{district}, {state}</b>.<br><br>
                Try a different crop or month that is traded near your region.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    best = records[0]
    name_str = f"Namaste {inputs['farmer_name']} — " if inputs["farmer_name"] else ""

    # ── Dummy data notice ──────────────────────────────────────────
    if is_dummy:
        st.error(
            "⚠️ We couldn't calculate prices right now — the numbers below are "
            "illustrative only, not real predictions. Please try again later."
        )

    # ── Results header ─────────────────────────────────────────────
    st.markdown(f"""
    <div class="results-header">
        <div class="section-eyebrow">Market Intelligence Report</div>
        <div class="section-title" style="text-align:left;font-size:1.9rem;">
            {name_str}Best Mandis for <em style="color:{AMBER_DARK}">{inputs['commodity']}</em>
        </div>
        <div style="font-size:0.85rem;color:{TEXT_MUTED};margin-top:4px;">
            {inputs['quantity_kg']} kg &nbsp;·&nbsp; {district}, {state}
            &nbsp;·&nbsp; {inputs['month_name']} {inputs['year']}
            &nbsp;·&nbsp; Within {MAX_DISTANCE_KM} km
            &nbsp;·&nbsp; {len(records)} markets found
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='results-body'>", unsafe_allow_html=True)

    # ── KPI cards ──────────────────────────────────────────────────
    st.markdown("<div class='sec-lbl'>Top Market — At a Glance</div>", unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(mc("Best Mandi", best["market"], best["state"]), unsafe_allow_html=True)
    with k2:
        st.markdown(mc("Predicted Price",
                       f"Rs. {best['predicted_price']:,.0f}", "per quintal"), unsafe_allow_html=True)
    with k3:
        st.markdown(mc("Gross Revenue",
                       f"Rs. {best['gross_revenue']:,.0f}",
                       f"for {inputs['quantity_kg']} kg"), unsafe_allow_html=True)
    with k4:
        st.markdown(mc("Total Costs",
                       f"Rs. {best['total_costs']:,.0f}",
                       "transport + fees", "red"), unsafe_allow_html=True)
    with k5:
        st.markdown(mc("Net Profit",
                       f"Rs. {best['net_profit']:,.0f}",
                       f"Rs. {best['profit_per_kg']:.2f}/kg", "amber"), unsafe_allow_html=True)

    # ── Cost breakdown row ─────────────────────────────────────────
    st.markdown("<div class='sec-lbl'>Cost Breakdown — Best Market</div>", unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        st.markdown(mc("Transport Cost",
                       f"Rs. {best['transport_cost']:,.0f}",
                       f"{best['distance_km']} km road distance"), unsafe_allow_html=True)
    with b2:
        st.markdown(mc("Mandi Commission",
                       f"Rs. {best['mandi_fee']:,.0f}", "2% of gross"), unsafe_allow_html=True)
    with b3:
        st.markdown(mc("Misc. Costs",
                       f"Rs. {best['misc_costs']:,.0f}", "handling + misc"), unsafe_allow_html=True)
    with b4:
        st.markdown(mc("Profit/kg",
                       f"Rs. {best['profit_per_kg']:.2f}", "net per kg"), unsafe_allow_html=True)

    # ── Charts row 1: Waterfall + Pie ─────────────────────────────
    st.markdown("<div class='sec-lbl'>Profit Waterfall & Cost Split — Best Market</div>",
                unsafe_allow_html=True)
    ch1, ch2 = st.columns([3, 2])
    with ch1:
        st.markdown(f"<p style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;"
                    f"text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:4px;'>"
                    f"Revenue → Costs → Net Profit</p>", unsafe_allow_html=True)
        st.image(cost_waterfall_chart(best), width="content")
    with ch2:
        st.markdown(f"<p style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;"
                    f"text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:4px;'>"
                    f"Where Does Your Money Go?</p>", unsafe_allow_html=True)
        st.image(cost_pie_chart(best), width="content")

    # ── Charts row 2: Bar (profit) + Bar (price) ──────────────────
    st.markdown("<div class='sec-lbl'>All Markets Compared</div>", unsafe_allow_html=True)
    ch3, ch4 = st.columns(2)
    with ch3:
        st.markdown(f"<p style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;"
                    f"text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:4px;'>"
                    f"Net Profit by Market (Rs.)</p>", unsafe_allow_html=True)
        st.image(profit_bar_chart(records), width="content")
    with ch4:
        st.markdown(f"<p style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;"
                    f"text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:4px;'>"
                    f"Predicted Price per Quintal (Rs.)</p>", unsafe_allow_html=True)
        st.image(price_comparison_chart(records), width="content")

    # ── Scatter: distance vs profit ────────────────────────────────
    st.markdown("<div class='sec-lbl'>Distance vs Profit Trade-off</div>",
                unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;"
                f"text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:4px;'>"
                f"Bubble size = predicted price. Orange = best choice.</p>",
                unsafe_allow_html=True)
    st.image(distance_vs_profit_scatter(records), width="content")

    # ── Ranked table ───────────────────────────────────────────────
    st.markdown("<div class='sec-lbl'>Full Market Rankings</div>", unsafe_allow_html=True)
    st.dataframe(style_table(records), width="stretch", hide_index=True)

    # ── Recommendation summary (SMS-style ranked list) ─────────────
    qty_kg = inputs["quantity_kg"]
    # Build SMS-style market lines for top markets (same format as sms_handler.py)
    top_markets = records[:3]
    market_lines = ""
    for i, r in enumerate(top_markets, 1):
        market_lines += (
            f'<div style="margin-bottom:14px;">'
            f'<div style="font-size:1.05rem;font-weight:700;color:{AMBER};">{i}. {r["market"]}</div>'
            f'<div style="font-size:0.92rem;margin-top:3px;">'
            f'Rs.{r["predicted_price"]:,.0f}/qtl'
            f' &nbsp;·&nbsp; Transport: Rs.{r["transport_cost"]:,.0f}'
            f' &nbsp;·&nbsp; Net: <strong>Rs.{r["net_profit"]:,.0f}</strong>'
            f' &nbsp;(Rs.{r["profit_per_kg"]:.1f}/kg)'
            f'</div></div>'
        )

    st.markdown(f"""
    <div class="reco-box">
        <div class="reco-lbl">Fasal-to-Faida Results</div>
        <div style="font-size:1.0rem;font-weight:600;margin-bottom:4px;">
            {inputs['commodity']} &nbsp;|&nbsp; {qty_kg} kg
        </div>
        <div style="font-size:0.85rem;opacity:0.75;margin-bottom:18px;">
            Sell: {inputs['month_name']} {inputs['year']} &nbsp;|&nbsp; {district}, {state}
        </div>
        {market_lines}
        <div style="font-size:0.78rem;opacity:0.6;margin-top:6px;">
            Send #PINCODE via SMS to query from your phone
        </div>
    </div>
    <p style='font-size:0.72rem;color:{TEXT_MUTED};margin-top:10px;'>
    Prices predicted by XGBoost model trained on Agmarknet data (2023–2024).
    Transport costs use haversine × 1.3 road factor with tiered truck rates.
    Results are indicative and actual prices may vary.
    </p>
    """, unsafe_allow_html=True)

    # ── AI Summary (any OpenAI-compatible provider, see llm_summary.py) ──
    from llm_summary import generate_summary, load_llm_config
    llm_config = load_llm_config(st.secrets)

    if llm_config and not is_dummy:
        with st.spinner("🤖 Generating AI summary…"):
            summary, err = generate_summary(records, inputs, district, state, llm_config)
        if summary:
            # LLM output is untrusted text: escape it before putting it in HTML
            summary = html.escape(summary)
            st.markdown(f"""
            <div style="background:#EDF7EE;border-left:5px solid {GREEN_MID};
                        border-radius:6px;padding:20px 26px;margin-top:16px;
                        box-shadow:0 2px 10px rgba(27,67,50,0.12);">
                <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.13em;
                            text-transform:uppercase;color:{GREEN_MID};margin-bottom:10px;">
                    🤖 AI Market Advisory
                </div>
                <div style="font-size:0.95rem;line-height:1.75;color:{TEXT_DARK};">{summary}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            log.error("AI summary failed: %s", err)
            st.warning("⚠️ AI summary is unavailable right now.")
    elif not llm_config:
        log.info("AI advisory skipped: no [llm] section with base_url, model and api_key in secrets")

    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# FOOTER
# =============================================================================
def render_footer():
    st.markdown(f"""
    <div class="site-footer">
        <strong>Fasal-to-Faida</strong> &nbsp;|&nbsp; Bech Sahi, Kamaao Zyada &nbsp;|&nbsp;
        Powered by XGBoost · Agmarknet Data 
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# MAIN
# =============================================================================
def main():
    inject_css()
    render_navbar()
    render_hero()
    render_features_section()
    inputs = render_form_section()
    if inputs["submitted"]:
        render_results(inputs)
    render_footer()


if __name__ == "__main__":
    main()