"""Demo: rate-limit a Flask endpoint to 10 requests per minute per IP."""
from flask import Flask, request, jsonify

from ratelimit_redis import Limiter

app = Flask(__name__)
limiter = Limiter(
    redis_url="redis://localhost:6379/0",
    capacity=10,
    refill_per_sec=10 / 60,  # 10 tokens per minute
)


@app.route("/")
def index():
    key = request.remote_addr or "anon"
    allowed, remaining = limiter.check(key)
    if not allowed:
        return jsonify(error="rate limited", remaining=remaining), 429
    return jsonify(ok=True, remaining=remaining)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
