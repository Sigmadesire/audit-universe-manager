from flask import Flask, jsonify
from datetime import datetime, timezone
from routes.describe import describe_bp
from routes.recommend import recommend_bp
from routes.generate_report import generate_report_bp

app = Flask(__name__)

app.register_blueprint(describe_bp)
app.register_blueprint(recommend_bp)
app.register_blueprint(generate_report_bp)

START_TIME = datetime.now(timezone.utc)
MODEL_NAME = "llama-3.3-70b-versatile"
AVG_RESPONSE_TIME_MS = 1200


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; "
        "frame-ancestors 'none'; "
        "base-uri 'none'; "
        "form-action 'none';"
    )
    return response


@app.route("/health", methods=["GET"])
def health():
    uptime_seconds = int((datetime.now(timezone.utc) - START_TIME).total_seconds())

    return jsonify({
        "status": "UP",
        "service": "ai-service",
        "model": MODEL_NAME,
        "avg_response_time_ms": AVG_RESPONSE_TIME_MS,
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "AI Service is running"
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)