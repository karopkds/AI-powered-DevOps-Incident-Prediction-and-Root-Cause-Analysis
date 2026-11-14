
import csv
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

PROMETHEUS_URL = "http://localhost:9090"

METRICS = {
    "request_rate": 'sum by (pod) (rate(http_requests_total{job="aiops-app-services"}[2m]))',
    "error_5xx_rate": 'sum by (pod) (rate(http_requests_total{job="aiops-app-services",status=~"5.."}[2m]))',
    "avg_latency_seconds": 'sum by (pod) (rate(http_request_duration_seconds_sum{job="aiops-app-services"}[2m])) / sum by (pod) (rate(http_request_duration_seconds_count{job="aiops-app-services"}[2m]))',
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "data" / "raw" / "telemetry.csv"
SCRAPE_INTERVAL_SECONDS = 15
COLLECTION_INTERVAL_SECONDS = 15
SAMPLES = 45


def query_prometheus(promql):
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": promql},
        timeout=10,
    )
    response.raise_for_status()

    payload = response.json()
    if payload["status"] != "success":
        raise RuntimeError(payload)

    return payload["data"]["result"]


def collect_sample():
    values = {}

    for metric_name, query in METRICS.items():
        results = query_prometheus(query)

        for result in results:
            pod = result["metric"].get("pod", "unknown")
            value = float(result["value"][1])
            values.setdefault(pod, {})[metric_name] = value

    timestamp = datetime.now(timezone.utc).isoformat()

    rows = []
    for pod, metrics in values.items():
        rows.append({
            "timestamp_utc": timestamp,
            "pod": pod,
            "scrape_interval_seconds": SCRAPE_INTERVAL_SECONDS,
            "request_rate": metrics.get("request_rate"),
            "error_5xx_rate": metrics.get("error_5xx_rate", 0.0),
            "avg_latency_seconds": metrics.get("avg_latency_seconds"),
        })

    return rows


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "timestamp_utc",
        "pod",
        "scrape_interval_seconds",
        "request_rate",
        "error_5xx_rate",
        "avg_latency_seconds",
    ]

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)

        if file.tell() == 0:
            writer.writeheader()

        for sample_number in range(SAMPLES):
            rows = collect_sample()

            for row in rows:
                writer.writerow(row)

            file.flush()

            print(
                f"Sample {sample_number + 1}/{SAMPLES}: "
                f"{len(rows)} pod(s) collected"
            )

            if sample_number < SAMPLES - 1:
                time.sleep(COLLECTION_INTERVAL_SECONDS)

    print(f"Telemetry saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
