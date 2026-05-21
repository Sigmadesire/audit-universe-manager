from flask import Blueprint, request, jsonify
from pathlib import Path
from datetime import datetime, timezone
from time import perf_counter
from services.groq_client import generate_text
import json


recommend_bp = Blueprint("recommend", __name__)

PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "recommend_prompt.txt"


def is_prompt_injection(text: str) -> bool:
    risky_patterns = [
        "ignore previous instructions",
        "ignore all previous instructions",
        "system prompt",
        "developer message",
        "reveal prompt",
        "jailbreak",
        "pretend you are",
        "disregard instructions",
        "<script",
        "</script>"
    ]
    lowered = text.lower()
    return any(pattern in lowered for pattern in risky_patterns)


@recommend_bp.route("/recommend", methods=["POST"])
def recommend():
    start_time = perf_counter()
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    input_text = data.get("input_text")

    if input_text is None:
        return jsonify({"error": "input_text is required"}), 400

    if not isinstance(input_text, str):
        return jsonify({"error": "input_text must be a string"}), 400

    input_text = input_text.strip()

    if not input_text:
        return jsonify({"error": "input_text cannot be empty"}), 400

    if len(input_text) > 5000:
        return jsonify({"error": "input_text is too long"}), 400

    if is_prompt_injection(input_text):
        return jsonify({"error": "input_text contains blocked content"}), 400

    try:
        prompt_template = PROMPT_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return jsonify({"error": "recommend prompt file not found"}), 500

    final_prompt = prompt_template.replace("{input_text}", input_text)

    try:
        generated_text_response = generate_text(final_prompt)
        recommendations = json.loads(generated_text_response)

        if not isinstance(recommendations, list) or len(recommendations) != 3:
            raise ValueError("AI output must be a list of 3 recommendations")

        valid_priorities = {"High", "Medium", "Low"}

        for item in recommendations:
            if not isinstance(item, dict):
                raise ValueError("Each recommendation must be an object")

            if not all(key in item for key in ("actiontype", "description", "priority")):
                raise ValueError("Each recommendation must contain actiontype, description, and priority")

            if not isinstance(item["actiontype"], str) or not item["actiontype"].strip():
                raise ValueError("actiontype must be a non-empty string")

            if not isinstance(item["description"], str) or not item["description"].strip():
                raise ValueError("description must be a non-empty string")

            if item["priority"] not in valid_priorities:
                raise ValueError("priority must be High, Medium, or Low")

        response_time_ms = round((perf_counter() - start_time) * 1000, 2)

        return jsonify({
            "recommendations": recommendations,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "response_time_ms": response_time_ms,
            "is_fallback": False
        }), 200

    except Exception:
        fallback_recommendations = [
            {
                "actiontype": "Control Improvement",
                "description": "Strengthen document verification before processing transactions.",
                "priority": "High"
            },
            {
                "actiontype": "Compliance",
                "description": "Introduce mandatory approval checks for high-risk audit areas.",
                "priority": "High"
            },
            {
                "actiontype": "Monitoring",
                "description": "Schedule periodic reviews to detect control gaps early.",
                "priority": "Medium"
            }
        ]

        response_time_ms = round((perf_counter() - start_time) * 1000, 2)

        return jsonify({
            "recommendations": fallback_recommendations,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "response_time_ms": response_time_ms,
            "is_fallback": True
        }), 200