# =============================================================================
# llm_summary.py — optional natural-language advisory for Fasal-to-Faida
#
# Works with any OpenAI-compatible chat API (Groq, Google Gemini, OpenRouter,
# ...). Configure it in .streamlit/secrets.toml — see secrets.toml.example:
#
#   [llm]
#   base_url = "https://api.groq.com/openai/v1"
#   model    = "<a model id listed in your provider's console>"
#   api_key  = "..."
#
# If the section is missing or incomplete the app simply skips the advisory.
# =============================================================================
from __future__ import annotations

TIMEOUT_SECONDS = 10      # never let a slow provider hang the results page
TEMPERATURE = 0.2         # low: stay close to the numbers, don't get creative
MAX_TOKENS = 300


def load_llm_config(secrets) -> dict | None:
    """Read the [llm] section from Streamlit secrets (or any mapping).
    Returns None unless base_url, model and api_key are all set."""
    try:
        section = secrets["llm"]
        cfg = {k: str(section.get(k, "")).strip() for k in ("base_url", "model", "api_key")}
    except Exception:
        return None
    return cfg if all(cfg.values()) else None


def _build_prompts(records, inputs, district, state):
    top = records[:3]
    market_lines = []
    for i, r in enumerate(top, 1):
        market_lines.append(
            f"  {i}. {r['market']} ({r.get('state', '')}): "
            f"Price Rs.{r['predicted_price']:,.0f}/quintal, "
            f"Distance {r['distance_km']:.0f} km, "
            f"Transport Rs.{r['transport_cost']:,.0f}, "
            f"Net Profit Rs.{r['net_profit']:,.0f} "
            f"(Rs.{r['profit_per_kg']:.1f}/kg)"
        )
    best = top[0]

    system_prompt = (
        "You are an agricultural market advisor who helps Indian farmers make "
        "better selling decisions. Write clear, concise, actionable advice in "
        "simple English. Do not use bullet points or markdown — write flowing "
        "prose of 3-4 sentences. Focus on which market to choose, the expected "
        "profit, transport trade-offs, and one practical tip. "
        "Use only the numbers given to you; never invent prices, distances, "
        "dates or market names. These are estimates, so do not promise outcomes."
    )
    user_prompt = (
        f"A farmer in {district}, {state} wants to sell {inputs['quantity_kg']} kg "
        f"of {inputs['commodity']} in {inputs['month_name']} {inputs['year']}. "
        f"The model evaluated nearby mandis and ranked them:\n\n"
        + "\n".join(market_lines) +
        f"\n\nThe best market is {best['market']} with a net profit of "
        f"Rs.{best['net_profit']:,.0f}. "
        f"Write a 3-4 sentence plain-English advisory: which market to choose, "
        f"why, and a practical tip about timing or transport."
    )
    return system_prompt, user_prompt


def generate_summary(
    records: list[dict],
    inputs: dict,
    district: str,
    state: str,
    config: dict,
) -> tuple[str | None, str | None]:
    """
    Generate a 3-4 sentence farmer-friendly summary.

    config: {"base_url", "model", "api_key"} from load_llm_config().

    Returns (summary_text, None) on success, (None, error_message) on failure.
    The error message is for server logs only; never show it to users.
    """
    if not records:
        return None, "No results to summarise."
    if not config:
        return None, "LLM not configured."
    try:
        from openai import OpenAI
    except ImportError:
        return None, "openai package not installed. Run: pip install openai"

    system_prompt, user_prompt = _build_prompts(records, inputs, district, state)
    try:
        client = OpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"],
            timeout=TIMEOUT_SECONDS,
            max_retries=1,
        )
        response = client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        text = (response.choices[0].message.content or "").strip()
        if not text:
            return None, "Empty response from LLM."
        return text, None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
