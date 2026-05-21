from flask import Blueprint, request, jsonify
from pathlib import Path
from datetime import datetime, timezone
from services.groq_client import generate_text
import json

generate_report_bp = Blueprint("generate_report", __name__)

PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "generate_report_prompt.txt"


@generate_report_bp.route("/generate-report", methods=["POST"])
def generate_report():
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

    try:
        prompt_template = PROMPT_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return jsonify({"error": "generate report prompt file not found"}), 500

    final_prompt = prompt_template.replace("{input_text}", input_text)

    try:
        generated_text = generate_text(final_prompt)
        report = json.loads(generated_text)

        required_keys = {"title", "summary", "overview", "key_items", "recommendations"}
        if not isinstance(report, dict) or not required_keys.issubset(report.keys()):
            raise ValueError("AI output must contain title, summary, overview, key_items, and recommendations")

        if not isinstance(report["key_items"], list):
            raise ValueError("key_items must be a list")

        if not isinstance(report["recommendations"], list):
            raise ValueError("recommendations must be a list")

        return jsonify({
            "report": report,
            "generated_at": datetime.now(timezone.utc).isoformat(),
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

        return jsonify({
            "report": fallback_report,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "is_fallback": True
        }), 200