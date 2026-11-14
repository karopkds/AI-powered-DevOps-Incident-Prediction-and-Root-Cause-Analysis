
import csv
import time
from pathlib import Path
from datetime import datetime, timezone

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "data" / "fault_injection_log.csv"

APP_URL = "http://localhost:5051/simulate-error"
FAULT_REQUESTS = 100
DELAY_SECONDS = 0.2


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    experiment_id = f"FAULT-{int(time.time())}"
    start_time = utc_now()

    successful_fault_requests = 0
    unexpected_responses = 0
    connection_errors = 0

    print(f"Experiment: {experiment_id}")
    print(f"Fault started: {start_time}")

    for _ in range(FAULT_REQUESTS):
        try:
            response = requests.get(APP_URL, timeout=5)

            if response.status_code == 500:
                successful_fault_requests += 1
            else:
                unexpected_responses += 1

        except requests.RequestException:
            connection_errors += 1

        time.sleep(DELAY_SECONDS)

    end_time = utc_now()

    record = {
        "experiment_id": experiment_id,
        "fault_type": "HTTP_500_ERROR",
        "start_time_utc": start_time,
        "end_time_utc": end_time,
        "expected_requests": FAULT_REQUESTS,
        "http_500_responses": successful_fault_requests,
        "unexpected_responses": unexpected_responses,
        "connection_errors": connection_errors,
    }

    file_exists = OUTPUT_FILE.exists()

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=record.keys())

        if not file_exists or OUTPUT_FILE.stat().st_size == 0:
            writer.writeheader()

        writer.writerow(record)

    print(f"Fault ended: {end_time}")
    print(f"HTTP 500 responses: {successful_fault_requests}")
    print(f"Connection errors: {connection_errors}")
    print(f"Experiment log saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
