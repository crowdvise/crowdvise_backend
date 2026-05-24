def build_insight_prompt(
    product_description: str,
    stage_insights: list[dict],
    overall_stats: dict,
    delayed_segment: list[dict],
) -> str:
    dominant = overall_stats.get("dominant_pattern", "mixed")

    delay_guidance = ""
    if overall_stats.get("delayed", 0) > 0:
        delay_guidance = f"""
DELAYED SEGMENT (critical — do not ignore):
{overall_stats.get("delayed")} of {overall_stats.get("total_agents")} agents ({overall_stats.get("delayed_rate"):.0%}) ended "delayed" — interested but stalled, NOT dropped.
Delayed agents are recoverable demand. At least ONE of your 3 insights MUST focus on this segment: why they hesitated, which stage stalled them, and the single highest-leverage change to convert hesitators.

Delayed agent details:
{delayed_segment}
"""
    if dominant == "delay_epidemic":
        delay_guidance += """
Dominant pattern: DELAY EPIDEMIC — conversion is low but dropout may also be low. Lead with this reframe:
"Your dropout rate is X% but conversion is Y% — Z% of the panel is hesitating, not lost. Here's what unstalls them."
Do NOT write three dropout-only insights when delay dominates the panel.
"""

    return f"""
You are a senior UX researcher and behavioural economist analysing simulation results.

Product tested: {product_description}

Overall results (conversion + dropout + delayed are separate outcomes — they must sum to 100% of the panel):
{overall_stats}

Stage breakdown (includes delay_rate = agents showing "delaying" behaviour at that stage):
{stage_insights}
{delay_guidance}

Generate exactly 3 specific, actionable insights a product team can implement immediately. Each insight must:
- Name the specific problem precisely (dropout, delay/hesitation, or conversion success)
- Reference the data (conversion rate, dropout rate, delayed rate, stage delay_rate, friction trigger, agent segment)
- Give one concrete recommendation to fix it

Insight mix rules:
- If delayed_rate >= 0.3 OR dominant_pattern is "delay_epidemic": at least 1 insight must target hesitators and how to unstall them
- If dropout_rate >= 0.3: at least 1 insight must target hard drop-offs
- If conversion_rate >= 0.3: at least 1 insight should reinforce what is working for converters (Cialdini/success path)

Return a JSON object:
{{
  "top_insights": ["insight 1", "insight 2", "insight 3"]
}}

Return ONLY the JSON object. No explanation, no markdown.
"""
