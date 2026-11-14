
import time
import random
import requests
from datetime import datetime, timezone

APP_URL = "http://localhost:5051/"
DURATION_SECONDS = 600  # 10 minutes

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def main():
    start = time.monotonic()
    total_requests = 0
    successful_requests = 0
    failed_requests = 0

    print(f"Normal traffic started: {utc_now()}")

    while time.monotonic() - start < DURATION_SECONDS:
        # Vary traffic between approximately 1 and 5 requests/sec
        delay = random.uniform(0.2, 1.0)

        try:
            response = requests.get(APP_URL, timeout=5)
            total_requests += 1

            if response.status_code == 200:
                successful_requests += 1
            else:
                failed_requests += 1

        except requests.RequestException:
            failed_requests += 1

        time.sleep(delay)

    print(f"Normal traffic ended: {utc_now()}")
    print(f"Total requests: {total_requests}")
    print(f"HTTP 200 responses: {successful_requests}")
    print(f"Failed requests: {failed_requests}")

if __name__ == "__main__":
    main()
