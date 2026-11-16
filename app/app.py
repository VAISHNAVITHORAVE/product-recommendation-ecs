import json
import os

import redis
from flask import Flask, jsonify

app = Flask(__name__)

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
    socket_connect_timeout=2
)

PRODUCTS = [
    {"id": 1, "name": "Laptop", "category": "Electronics"},
    {"id": 2, "name": "Headphones", "category": "Electronics"},
    {"id": 3, "name": "Smartphone", "category": "Electronics"},
    {"id": 4, "name": "Running Shoes", "category": "Fashion"},
    {"id": 5, "name": "T-Shirt", "category": "Fashion"}
]


@app.route("/")
def home():
    return jsonify({
        "message": "Product Recommendation API",
        "status": "running"
    })


@app.route("/health")
def health():
    try:
        redis_client.ping()
        return jsonify({
            "status": "healthy",
            "redis": "connected"
        }), 200
    except redis.RedisError:
        return jsonify({
            "status": "unhealthy",
            "redis": "disconnected"
        }), 503


@app.route("/recommendations/<int:user_id>")
def recommendations(user_id):
    cache_key = f"recommendations:user:{user_id}"

    try:
        cached_data = redis_client.get(cache_key)

        if cached_data:
            return jsonify({
                "user_id": user_id,
                "source": "redis_cache",
                "recommendations": json.loads(cached_data)
            })

        recommended_products = PRODUCTS[:3]

        redis_client.setex(
            cache_key,
            60,
            json.dumps(recommended_products)
        )

        return jsonify({
            "user_id": user_id,
            "source": "generated",
            "recommendations": recommended_products
        })

    except redis.RedisError:
        return jsonify({
            "user_id": user_id,
            "source": "fallback",
            "recommendations": PRODUCTS[:3]
        })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
