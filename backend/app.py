from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import json
import logging
import mysql.connector
import requests
import time

app = Flask(__name__)
limiter = Limiter(key_func=get_remote_address, app=app)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')

DB_HOST = os.getenv('DB_HOST', 'db')
DB_USER = os.getenv('DB_USER', 'ifeanyi9')
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_NAME = os.getenv('DB_NAME', 'appdb')

#timer
@app.before_request
def start_request_timer():
    request.request_started_at = time.perf_counter()


@app.after_request
def log_request(response):
    elapsed_ms = (time.perf_counter() - request.request_started_at) * 1000
    logger.info(json.dumps({
        'event': 'http_request',
        'method': request.method,
        'path': request.path,
        'status': response.status_code,
        'duration_ms': round(elapsed_ms, 2),
    }))
    return response


@app.get('/api/health')
def health():
    return {'status': 'ok'}


@app.get('/api/status')
def status():
    return {'message': 'Backend API is running'}


@app.get('/api/ready')
def ready():
    return {'status': 'ready'}


FINNA = "https://api.finna.fi/api/v1/search"
CACHE, TTL = {}, 300



@app.get('/api/db')

def testt():
    """Simple endpoint that greets from DB."""
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
)
    cur = conn.cursor()
    cur.execute("SELECT 'Hello from MySQL via Flask!'")
    row = cur.fetchone()
    cur.close(); conn.close()
    return jsonify(message=row[0])


@app.get("/api")
@limiter.limit("10/minute")

def search():
    q = request.args.get("q", "").strip()
    if not q or len(q) > 100:
        return jsonify(error="q is required (max 100 chars)"), 400

    hit = CACHE.get(q)
    if hit and time.time() - hit[0] < TTL:
        return jsonify(hit[1])

    try:
        r = requests.get(
            FIANNA,
            params={"lookfor": q, "type": "AllFields", "limit": 10,
                    "field[]": ["id", "title"]},
            headers={"User-Agent": "my-app/1.0"},
            timeout=5,
        )
        r.raise_for_status()
        data = r.json()
    except requests.RequestException:
        return jsonify(error="Upstream service unavailable"), 502

    result = {"count": data.get("resultCount", 0),
              "records": data.get("records", [])}
    CACHE[q] = (time.time(), result)
    return jsonify(result)



if __name__ == '__main__':
    # Dev-only fallback
    app.run(host='0.0.0.0', port=8000, debug=True)


