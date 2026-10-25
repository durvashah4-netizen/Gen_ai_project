from typing import Any


SAFETY_DEMO: dict[str, Any] = {
    "safety_score": 72,
    "overall_status": "Needs attention",
    "ppe_detection": [
        {"item": "Helmet", "status": "Partially visible", "confidence": 0.66, "notes": "Check all workers at close range."},
        {"item": "High-visibility vest", "status": "Unclear", "confidence": 0.51, "notes": "Visibility varies by worker and image."},
        {"item": "Steel-toe boots", "status": "Not verifiable", "confidence": 0.18, "notes": "Footwear protection cannot be confirmed from this view."},
        {"item": "Safety harness", "status": "Not verifiable", "confidence": 0.22, "notes": "Applicability depends on the work-at-height context."},
    ],
    "hazards": [
        {"hazard": "Unprotected work area", "severity": "Medium", "location": "Example observation", "corrective_action": "Inspect the area, establish barriers, and confirm the site-specific control plan."}
    ],
    "summary": "Sample report for interface demonstration only; no image was analyzed.",
}

CRACK_DEMO: dict[str, Any] = {
    "defect_type": "Hairline",
    "estimated_width_mm": 0.3,
    "severity": "Low",
    "probable_causes": ["Example only: drying shrinkage or surface movement; confirm on site."],
    "recommended_repairs": ["Record and monitor the defect; have an engineer assess before repair selection."],
    "urgency": "Routine inspection",
    "engineer_review_required": True,
    "observations": "Sample report for interface demonstration only; no image was analyzed.",
}

SAFETY_SCHEMA = {
    "type": "object",
    "properties": {
        "safety_score": {"type": "integer"},
        "overall_status": {"type": "string"},
        "ppe_detection": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item": {"type": "string"},
                    "status": {"type": "string"},
                    "confidence": {"type": "number"},
                    "notes": {"type": "string"},
                },
                "required": ["item", "status", "confidence", "notes"],
            },
        },
        "hazards": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hazard": {"type": "string"},
                    "severity": {"type": "string", "enum": ["Low", "Medium", "High", "Critical"]},
                    "location": {"type": "string"},
                    "corrective_action": {"type": "string"},
                },
                "required": ["hazard", "severity", "location", "corrective_action"],
            },
        },
        "summary": {"type": "string"},
    },
    "required": ["safety_score", "overall_status", "ppe_detection", "hazards", "summary"],
}

CRACK_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "defect_type": {
            "type": "string",
            "enum": ["Hairline", "Settlement", "Structural Shear", "Thermal Expansion", "Spalling", "Unclear"],
        },
        "estimated_width_mm": {"type": ["number", "null"]},
        "severity": {"type": "string", "enum": ["Low", "Medium", "High", "Critical", "Unclear"]},
        "probable_causes": {"type": "array", "items": {"type": "string"}},
        "recommended_repairs": {"type": "array", "items": {"type": "string"}},
        "urgency": {"type": "string"},
        "engineer_review_required": {"type": "boolean"},
        "observations": {"type": "string"},
    },
    "required": [
        "defect_type", "estimated_width_mm", "severity", "probable_causes",
        "recommended_repairs", "urgency", "engineer_review_required", "observations",
    ],
}


def validate_safety_report(report: Any) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise ValueError("Safety response must be a JSON object.")
    required = {"safety_score", "overall_status", "ppe_detection", "hazards", "summary"}
    if not required.issubset(report):
        raise ValueError("Safety response is missing required fields.")
    if isinstance(report["safety_score"], bool) or not isinstance(report["safety_score"], int) or not 0 <= report["safety_score"] <= 100:
        raise ValueError("Safety score must be an integer from 0 to 100.")
    if not all(isinstance(report[field], str) for field in ("overall_status", "summary")):
        raise ValueError("Overall status and summary must be strings.")
    if not isinstance(report["ppe_detection"], list) or not isinstance(report["hazards"], list):
        raise ValueError("PPE detections and hazards must be JSON arrays.")
    for item in report["ppe_detection"]:
        if not isinstance(item, dict) or not {"item", "status", "confidence", "notes"}.issubset(item):
            raise ValueError("Each PPE entry must include item, status, confidence, and notes.")
        if isinstance(item["confidence"], bool) or not isinstance(item["confidence"], (int, float)) or not 0 <= item["confidence"] <= 1:
            raise ValueError("PPE confidence must be between 0 and 1.")
        if not all(isinstance(item[field], str) for field in ("item", "status", "notes")):
            raise ValueError("PPE item, status, and notes must be strings.")
    for hazard in report["hazards"]:
        if not isinstance(hazard, dict) or not {"hazard", "severity", "location", "corrective_action"}.issubset(hazard):
            raise ValueError("Each hazard must include hazard, severity, location, and corrective_action.")
        if hazard["severity"] not in {"Low", "Medium", "High", "Critical"}:
            raise ValueError("Hazard severity must be Low, Medium, High, or Critical.")
        if not all(isinstance(hazard[field], str) for field in ("hazard", "location", "corrective_action")):
            raise ValueError("Hazard details must be strings.")
    return report


def validate_crack_report(report: Any) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise ValueError("Crack response must be a JSON object.")
    required = {
        "defect_type", "estimated_width_mm", "severity", "probable_causes",
        "recommended_repairs", "urgency", "engineer_review_required", "observations",
    }
    if not required.issubset(report):
        raise ValueError("Crack response is missing required fields.")
    width = report["estimated_width_mm"]
    if width is not None and (not isinstance(width, (int, float)) or width < 0):
        raise ValueError("Estimated width must be a non-negative number or null.")
    if report["defect_type"] not in {"Hairline", "Settlement", "Structural Shear", "Thermal Expansion", "Spalling", "Unclear"}:
        raise ValueError("Unknown defect type.")
    if report["severity"] not in {"Low", "Medium", "High", "Critical", "Unclear"}:
        raise ValueError("Unknown crack severity.")
    if not isinstance(report["probable_causes"], list) or not isinstance(report["recommended_repairs"], list):
        raise ValueError("Causes and repair recommendations must be JSON arrays.")
    if not all(isinstance(value, str) for value in report["probable_causes"] + report["recommended_repairs"]):
        raise ValueError("Causes and repair recommendations must contain strings.")
    if not isinstance(report["engineer_review_required"], bool):
        raise ValueError("engineer_review_required must be a boolean.")
    if not all(isinstance(report[field], str) for field in ("urgency", "observations")):
        raise ValueError("Urgency and observations must be strings.")
    return report