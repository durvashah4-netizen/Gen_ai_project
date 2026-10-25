import base64
import base64
import json
from typing import Any

from domain import (
    CRACK_DEMO,
    CRACK_SCHEMA,
    SAFETY_DEMO,
    SAFETY_SCHEMA,
    validate_crack_report,
    validate_safety_report,
)


def analyze_image(
    analysis_type: str,
    image_bytes: bytes,
    mime_type: str,
    api_key: str,
    model: str,
) -> dict[str, Any]:
    if not api_key:
        return dict(SAFETY_DEMO if analysis_type == "safety" else CRACK_DEMO)
    if analysis_type not in {"safety", "crack"}:
        raise ValueError("Unknown image analysis type.")

    from groq import Groq

    safety_prompt = """
Analyze only visible evidence in this construction-site photo. Never claim compliance certification.
Use OSHA construction guidance and applicable Indian construction-site safety rules only as general reference points; do not claim legal compliance from an image. IS 456 concerns plain and reinforced concrete design, not PPE requirements; mention it only when discussing relevant concrete/structural context, not as a safety standard.
If an item is obscured, say Not verifiable. Do not infer steel-toe protection from ordinary footwear.
Return the requested JSON only. Use score 0-100 as a visual triage aid, not a compliance score; status should be Needs attention, Review required, or No obvious issue.
PPE must include helmet, high-visibility vest, steel-toe boots, and safety harness. List visible hazards with severity Low, Medium, High, or Critical and a practical corrective action. Include a concise uncertainty-aware summary.
"""
    crack_prompt = """
Describe only the visible surface evidence in this photo. Image-only width and cause estimates are uncertain; use null width if it cannot be estimated. Never decide that a structure is safe. Recommend professional review for potentially structural or unclear damage. Return JSON only, classify defect_type as Hairline, Settlement, Structural Shear, Thermal Expansion, Spalling, or Unclear. Include severity, probable_causes, recommended_repairs, urgency, engineer_review_required, and observations. Repairs are options for engineer review, not instructions to apply without assessment.
"""
    schema = SAFETY_SCHEMA if analysis_type == "safety" else CRACK_SCHEMA
    image_data = base64.b64encode(image_bytes).decode("ascii")
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Return only a JSON object matching this schema. Do not use markdown fences.\n"
                    f"{json.dumps(schema)}"
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": safety_prompt if analysis_type == "safety" else crack_prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
                    },
                ],
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    response_text = response.choices[0].message.content
    if not response_text:
        raise ValueError("The model returned an empty response.")
    result = json.loads(response_text)
    return validate_safety_report(result) if analysis_type == "safety" else validate_crack_report(result)


def estimate_project(structure: str, area_sqft: int, tier: str, completion_pct: int) -> dict[str, float]:
    base_cost_per_sqft = {
        "Residential": {"Tier 1": 2800, "Tier 2": 2300, "Tier 3": 1900},
        "Commercial": {"Tier 1": 3600, "Tier 2": 3000, "Tier 3": 2500},
        "Industrial": {"Tier 1": 2400, "Tier 2": 2050, "Tier 3": 1750},
    }
    market_value_per_sqft = {
        "Residential": {"Tier 1": 7600, "Tier 2": 5100, "Tier 3": 3400},
        "Commercial": {"Tier 1": 9800, "Tier 2": 6800, "Tier 3": 4500},
        "Industrial": {"Tier 1": 5100, "Tier 2": 3700, "Tier 3": 2600},
    }
    steel_kg_per_sqft = {"Residential": 4.2, "Commercial": 5.0, "Industrial": 3.8}
    cement_bags_per_sqft = {"Residential": 0.40, "Commercial": 0.45, "Industrial": 0.35}
    if structure not in base_cost_per_sqft or tier not in base_cost_per_sqft[structure]:
        raise ValueError("Unsupported structure type or location tier.")
    if area_sqft <= 0 or not 0 <= completion_pct <= 100:
        raise ValueError("Area must be positive and completion must be between 0 and 100.")
    total_budget = area_sqft * base_cost_per_sqft[structure][tier]
    return {
        "total_budget_inr": total_budget,
        "capex_incurred_inr": total_budget * completion_pct / 100,
        "market_value_inr": area_sqft * market_value_per_sqft[structure][tier],
        "steel_kg": area_sqft * steel_kg_per_sqft[structure],
        "cement_bags": area_sqft * cement_bags_per_sqft[structure],
    }


def format_inr(value: float) -> str:
    if value >= 10_000_000:
        return f"Rs {value / 10_000_000:,.2f} Cr"
    if value >= 100_000:
        return f"Rs {value / 100_000:,.2f} L"
    return f"Rs {value:,.0f}"


def build_concept_prompt(structure: str, area_sqft: int, tier: str) -> str:
    return (
        f"Conceptual architectural visualization of a {structure.lower()} construction project, "
        f"approximately {area_sqft:,} square feet, in a {tier} Indian city. Show a realistic site context, "
        "clear building massing, daylight, practical materials, no text, no logos, illustrative only."
    )


def get_weather_advisory(condition: str) -> dict[str, Any]:
    advisories = {
        "Normal": {
            "title": "Routine operations",
            "summary": "Continue planned work under the site's standard controls and current forecast.",
            "actions": ["Check toolbox-talk attendance and equipment inspections.", "Maintain housekeeping, access routes, and hydration breaks."],
        },
        "High Wind": {
            "title": "Wind exposure / reassess lifting work",
            "summary": "Wind can destabilize loads, access equipment, temporary works, and elevated work.",
            "actions": ["Pause crane and hoist work when wind exceeds the equipment or lift-plan limit.", "Secure loose materials and inspect scaffolds, formwork, and edge protection.", "Use the site wind-measurement and restart procedure."],
        },
        "Heavy Rain": {
            "title": "Rain / water and electrical controls",
            "summary": "Rain can reduce traction, hide openings, affect excavation stability, and create electrical hazards.",
            "actions": ["Inspect excavations, drainage, access paths, and temporary supports before entry.", "Protect electrical equipment and isolate damaged or water-exposed circuits for competent inspection.", "Review concrete placement and curing plans against the mix and site specifications."],
        },
        "Extreme Heat": {
            "title": "Heat stress / adjust work-rest controls",
            "summary": "Heat exposure can escalate quickly, especially for strenuous work and workers in PPE.",
            "actions": ["Apply the site's heat-stress plan, acclimatization, shaded recovery, and scheduled water breaks.", "Shift strenuous tasks to cooler periods where feasible and use a buddy check.", "Escalate symptoms promptly and follow the site's emergency response procedure."],
        },
    }
    if condition not in advisories:
        raise ValueError("Unknown weather condition.")
    return advisories[condition]


def assistant_reply(
    question: str,
    weather: str,
    history: list[dict[str, str]],
    api_key: str,
    model: str,
) -> str:
    if not api_key:
        if weather == "High Wind":
            return "For today's high-wind conditions, check crane and hoist limits in the lift plan, secure loose materials, and follow the site's measured-wind stop/restart procedure. I cannot determine safe operating limits without the equipment documentation and site conditions."
        return "Demo mode is active, so I cannot provide a project-specific engineering answer yet. Add a Groq API key for model-backed assistance. For decisions affecting structural safety, quantities, or code compliance, verify against approved drawings and a qualified professional."
    from groq import Groq

    recent_history = history[-12:]
    transcript = "\n".join(f"{item['role'].upper()}: {item['content']}" for item in recent_history)
    prompt = (
        "You are a cautious construction planning assistant. Give concise, practical general guidance, "
        "state assumptions, and ask for missing project details. Do not certify code compliance or structural safety; "
        "direct high-consequence decisions to qualified professionals and approved documents. "
        f"Today's selected weather is {weather}.\nConversation:\n{transcript}"
    )
    response = Groq(api_key=api_key).chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = response.choices[0].message.content
    if not response_text:
        raise ValueError("The assistant returned an empty response.")
    return response_text