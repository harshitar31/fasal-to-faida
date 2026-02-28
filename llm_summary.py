# =============================================================================
# llm_summary.py — Featherless.ai natural-language summary for Fasal-to-Faida
# =============================================================================
from __future__ import annotations


def generate_summary(
    records: list[dict],
    inputs: dict,
    district: str,
    state: str,
    api_key: str,
    model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct",
) -> tuple[str | None, str | None]:
    """
    Call featherless.ai to generate a 3-4 sentence farmer-friendly summary.

    Returns
    -------
    (summary_text, error_message)
    - On success : (text, None)
    - On failure : (None, error_message)
    """
    try:
        from openai import OpenAI
    except ImportError:
        return None, "openai package not installed. Run: pip install openai"

    if not api_key or not api_key.strip():
        return None, "No API key provided."

    # ── Build compact description of top results ──────────────────────
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
    markets_text = "\n".join(market_lines)
    best = top[0]

    system_prompt = (
        "You are an agricultural market advisor who helps Indian farmers make "
        "better selling decisions. Write clear, concise, actionable advice in "
        "simple English. Do not use bullet points or markdown — write flowing "
        "prose of 3-4 sentences. Focus on which market to choose, the expected "
        "profit, transport trade-offs, and one practical tip."
    )

    user_prompt = (
        f"A farmer in {district}, {state} wants to sell {inputs['quantity_kg']} kg "
        f"of {inputs['commodity']} in {inputs['month_name']} {inputs['year']}. "
        f"The model evaluated nearby mandis and ranked them:\n\n"
        f"{markets_text}\n\n"
        f"The best market is {best['market']} with a net profit of "
        f"Rs.{best['net_profit']:,.0f}. "
        f"Write a 3-4 sentence plain-English advisory: which market to choose, "
        f"why, and a practical tip about timing or transport."
    )

    try:
        client = OpenAI(
            api_key=api_key.strip(),
            base_url="https://api.featherless.ai/v1",
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        text = response.choices[0].message.content.strip()
        return text, None
    except Exception as exc:
        return None, str(exc)
