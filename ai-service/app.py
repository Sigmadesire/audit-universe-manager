from flask import Flask, jsonify
from datetime import datetime, timezone
from routes.describe import describe_bp
from routes.recommend import recommend_bp
from routes.generate_report import generate_report_bp

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None


app = Flask(__name__)

app.register_blueprint(describe_bp)
app.register_blueprint(recommend_bp)
app.register_blueprint(generate_report_bp)

START_TIME = datetime.now(timezone.utc)
MODEL_NAME = "llama-3.3-70b-versatile"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
AVG_RESPONSE_TIME_MS = 1200

embedding_model = None
embedding_model_status = "not_loaded"
embedding_model_error = None


def preload_embedding_model():
    global embedding_model, embedding_model_status, embedding_model_error

    if SentenceTransformer is None:
        embedding_model_status = "unavailable"
        embedding_model_error = "sentence-transformers is not installed"
        return

    try:
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        embedding_model.encode(["startup warmup"])
        embedding_model_status = "loaded"
        embedding_model_error = None
    except Exception as exc:
        embedding_model = None
        embedding_model_status = "failed"
        embedding_model_error = str(exc)


preload_embedding_model()


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

    payload = {
        "status": "UP",
        "service": "ai-service",
        "model": MODEL_NAME,
        "embedding_model": EMBEDDING_MODEL_NAME,
        "embedding_model_status": embedding_model_status,
        "avg_response_time_ms": AVG_RESPONSE_TIME_MS,
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    if embedding_model_error:
        payload["embedding_model_error"] = embedding_model_error

    return jsonify(payload), 200


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "AI Service is running"
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)