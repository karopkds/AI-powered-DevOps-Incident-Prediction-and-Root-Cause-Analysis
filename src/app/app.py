
from flask import Flask, Response, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

# Count HTTP requests by method, endpoint and status code.
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

# Measure HTTP request processing time.
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)


@app.before_request
def start_timer():
    if request.path != "/metrics":
        request.start_time = time.perf_counter()


@app.after_request
def record_metrics(response):
    if request.path != "/metrics":
        duration = time.perf_counter() - request.start_time

        endpoint = (
            request.url_rule.rule
            if request.url_rule
            else "unmatched"
        )

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(response.status_code)
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)

    return response


@app.route("/")
def home():
    return "AIOps Incident Prediction Application"


@app.route("/health")
def health():
    return {"status": "healthy"}


@app.route("/metrics")
def metrics():
    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST
    )

@app.route("/simulate-error")
def simulate_error():
    return {"error": "Simulated internal server error"}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
