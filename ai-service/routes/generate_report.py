from flask import Blueprint, request, jsonify
from pathlib import Path
from datetime import datetime, timezone
from time import perf_counter
from services.groq_client import generate_text
import json


generate_report_bp = Blueprint("generate_report", __name__)

PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "generate_report_prompt.txt"


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


def is_non_empty_string_list(value) -> bool:
    return (
        isinstance(value, list) and
        len(value) > 0 and
        all(isinstance(item, str) and item.strip() for item in value)
    )


@generate_report_bp.route("/generate-report", methods=["POST"])
def generate_report():
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
        return jsonify({"error": "generate report prompt file not found"}), 500

    final_prompt = prompt_template.replace("{input_text}", input_text)

    try:
        generated_text_response = generate_text(final_prompt)
        report = json.loads(generated_text_response)

        required_keys = {"title", "summary", "overview", "key_items", "recommendations"}
        if not isinstance(report, dict) or not required_keys.issubset(report.keys()):
            raise ValueError("AI output must contain title, summary, overview, key_items, and recommendations")

        if not isinstance(report["title"], str) or not report["title"].strip():
            raise ValueError("title must be a non-empty string")

        if not isinstance(report["summary"], str) or not report["summary"].strip():
            raise ValueError("summary must be a non-empty string")

        if not isinstance(report["overview"], str) or not report["overview"].strip():
            raise ValueError("overview must be a non-empty string")

        if not is_non_empty_string_list(report["key_items"]):
            raise ValueError("key_items must be a non-empty list of strings")

        if not is_non_empty_string_list(report["recommendations"]):
            raise ValueError("recommendations must be a non-empty list of strings")

        response_time_ms = round((perf_counter() - start_time) * 1000, 2)

        return jsonify({
            "report": report,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "response_time_ms": response_time_ms,
            "is_fallback": False
        }), 200

    except Exception:
        fallback_report = {
            "title": "Audit Risk Report",
            "summary": "The submitted audit matter indicates control weaknesses requiring immediate review.",
            "overview": "This issue suggests missing documentation, weak approval controls, or monitoring gaps that may expose the organisation to compliance and operational risks.",
            "key_items": [
                "Supporting documents were incomplete or missing.",
                "Approval control may not have been consistently applied.",
                "The issue increases the risk of undetected process failures."
            ],
            "recommendations": [
                "Strengthen documentation verification before transaction processing.",
                "Apply mandatory approval checks for sensitive transactions.",
                "Schedule periodic monitoring to identify control gaps early."
            ]
        }

        response_time_ms = round((perf_counter() - start_time) * 1000, 2)

        return jsonify({
            "report": fallback_report,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "response_time_ms": response_time_ms,
            "is_fallback": True
        }), 200