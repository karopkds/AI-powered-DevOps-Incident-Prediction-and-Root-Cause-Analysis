
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

NORMAL_FILE = ROOT / "data/raw/normal_traffic_telemetry.csv"
LOW_TRAFFIC_FILE = (
    ROOT / "data/raw/low_traffic_telemetry.csv"
)
EXPERIMENT_FILE = ROOT / "data/processed/experiment_02_labeled.csv"
FAULT_FILE = ROOT / "data/fault_injection_log.csv"

OUTPUT_FILE = ROOT / "data/processed/normal_training_data.csv"

normal = pd.read_csv(NORMAL_FILE)
low_traffic = pd.read_csv(LOW_TRAFFIC_FILE)
experiment = pd.read_csv(EXPERIMENT_FILE)
faults = pd.read_csv(FAULT_FILE)

# Identify the exact fault for Experiment 2
experiment_id = experiment["experiment_id"].iloc[0]

matching = faults[
    faults["experiment_id"] == experiment_id
]

if len(matching) != 1:
    raise ValueError("Expected exactly one matching fault record")

fault_start = pd.to_datetime(
    matching.iloc[0]["start_time_utc"],
    utc=True
)

experiment["timestamp_utc"] = pd.to_datetime(
    experiment["timestamp_utc"],
    utc=True
)

# Select only observations before fault injection
idle = experiment[
    experiment["timestamp_utc"] < fault_start
].copy()

# Select common telemetry columns
columns = [
    "timestamp_utc",
    "pod",
    "scrape_interval_seconds",
    "request_rate",
    "error_5xx_rate",
    "avg_latency_seconds",
]

normal = normal[columns].copy()
idle = idle[columns].copy()
low_traffic = low_traffic[columns].copy()

normal["operating_mode"] = "normal_traffic"
idle["operating_mode"] = "idle"
low_traffic["operating_mode"] = "low_traffic"

# Combine the two normal operating conditions
combined = pd.concat(
    [normal, idle, low_traffic],
    ignore_index=True
)

combined["timestamp_utc"] = pd.to_datetime(
    combined["timestamp_utc"],
    utc=True
)

combined = combined.sort_values("timestamp_utc")

# Prevent duplicate observations
combined = combined.drop_duplicates(
    subset=["timestamp_utc", "pod"]
)

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

combined.to_csv(OUTPUT_FILE, index=False)

print("Normal training dataset created!")
print("Total observations:", len(combined))

print("\nOperating mode distribution:")
print(combined["operating_mode"].value_counts())

print("\nRequest rate statistics:")
print(combined["request_rate"].describe())

print("\nSaved to:", OUTPUT_FILE)
