BEHAVIOURAL_FRAMEWORKS = """
Reason about every agent through these five validated lenses:

1. OCEAN (Big Five) — who they are
   - Openness: curiosity, willingness to try new things
   - Conscientiousness: organisation, discipline, reliability
   - Extraversion: social energy, stimulation-seeking
   - Agreeableness: trust, cooperation, empathy
   - Neuroticism: anxiety, emotional reactivity, mood instability

2. Prospect Theory (Kahneman & Tversky) — how pain vs pleasure is weighed
   - Losses feel ~2× as painful as equivalent gains
   - Weight negative/friction reactions accordingly; do not treat costs and benefits symmetrically

3. Cialdini's 6 Principles — what drives positive adoption (not only resistance)
   - Social proof, scarcity, authority, liking, reciprocity, commitment/consistency
   - Use these to explain why agents convert, commit, or feel persuaded — not only why they drop

4. Cognitive Load Theory — when thinking itself causes disengagement
   - Complex language, too many choices, unfamiliar patterns exhaust working memory
   - "cognitive_load" is distinct from price sensitivity or trust — name it when overload causes friction

5. Status Quo Bias — why people delay instead of switching
   - Default options and familiar habits win even when alternatives are better
   - High status_quo_tendency → prefer delaying over changing, even when the new path is objectively better
"""

STAGE_REASONING_BRIEF = """
Apply: OCEAN personality | Prospect Theory (losses ~2× gains) | Cialdini if converting |
cognitive_load if overwhelmed | status_quo_inertia if delaying despite better options.
"""

OCEAN_TO_SENSITIVITY_RULES = """
Derive trigger_sensitivities (0.0–1.0) from OCEAN scores — do NOT assign arbitrarily:
- unexpected_cost: higher with neuroticism and loss-aversion weighting (Prospect Theory)
- trust_violation: higher with low agreeableness and high neuroticism
- cognitive_load: higher with low openness and low conscientiousness
- effort_cost: higher with low conscientiousness and high status_quo_tendency
- value_mismatch: higher with low openness and high conscientiousness (clear expectations)
- status_quo_inertia: higher with status_quo_tendency and low openness

Use the SAME six keys for every profile in the panel. Values must differ and reflect each person's OCEAN + status_quo_tendency.
"""

STANDARD_TRIGGER_KEYS = [
    "unexpected_cost",
    "trust_violation",
    "cognitive_load",
    "effort_cost",
    "value_mismatch",
    "status_quo_inertia",
]
