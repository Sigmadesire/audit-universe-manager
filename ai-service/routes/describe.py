from flask import Blueprint, request, jsonify
from pathlib import Path
from datetime import datetime, timezone
from time import perf_counter
from services.groq_client import generate_text


describe_bp = Blueprint("describe", __name__)

PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "describe_prompt.txt"


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


@describe_bp.route("/describe", methods=["POST"])
def describe():
    start_time = perf_counter()
    data = request.get_json(silent=True)

    if not data:
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
        return jsonify({"error": "describe prompt file not found"}), 500

    final_prompt = prompt_template.replace("{input_text}", input_text)

    try:
        generated_description = generate_text(final_prompt)
        response_time_ms = round((perf_counter() - start_time) * 1000, 2)

        return jsonify({
            "description": generated_description,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "response_time_ms": response_time_ms,
            "is_fallback": False
        }), 200

    except Exception:
        response_time_ms = round((perf_counter() - start_time) * 1000, 2)

        return jsonify({
            "description": "AI description is temporarily unavailable.",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "response_time_ms": response_time_ms,
            "is_fallback": True
        }), 200