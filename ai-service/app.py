from flask import Flask, jsonify
from routes.describe import describe_bp
from routes.recommend import recommend_bp
from routes.generate_report import generate_report_bp

app = Flask(__name__)

app.register_blueprint(describe_bp)
app.register_blueprint(recommend_bp)
app.register_blueprint(generate_report_bp)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "UP",
        "service": "ai-service"
    }), 200


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "AI Service is running"
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)