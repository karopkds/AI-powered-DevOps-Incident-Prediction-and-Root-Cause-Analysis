
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TELEMETRY_FILE = (
    PROJECT_ROOT / "data" / "raw"
    / "telemetry.csv"
)

FAULT_FILE = (
    PROJECT_ROOT / "data" / "fault_injection_log.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "experiment_02_labeled.csv"
)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Load telemetry
df = pd.read_csv(TELEMETRY_FILE)

df["timestamp_utc"] = pd.to_datetime(
    df["timestamp_utc"], utc=True
)

# Load fault records
faults = pd.read_csv(FAULT_FILE)

faults["start_time_utc"] = pd.to_datetime(
    faults["start_time_utc"], utc=True
)

faults["end_time_utc"] = pd.to_datetime(
    faults["end_time_utc"], utc=True
)

# Use the fault overlapping this experiment
experiment_start = df["timestamp_utc"].min()
experiment_end = df["timestamp_utc"].max()

matching = faults[
    (faults["start_time_utc"] <= experiment_end)
    & (faults["end_time_utc"] >= experiment_start)
]

if len(matching) != 1:
    raise ValueError(
        "Expected exactly one overlapping fault. "
        f"Found {len(matching)}."
    )

fault = matching.iloc[0]

fault_start = fault["start_time_utc"]
fault_end = fault["end_time_utc"]

# Incident-state labels, NOT predictive labels
df["incident_active"] = (
    (df["timestamp_utc"] >= fault_start)
    & (df["timestamp_utc"] <= fault_end)
).astype(int)

df["experiment_id"] = fault["experiment_id"]

# Preserve the prediction objective separately
PREDICTION_HORIZON_MINUTES = 5

df["prediction_horizon_minutes"] = (
    PREDICTION_HORIZON_MINUTES
)

# No validated precursor data yet
df["pre_incident_target"] = pd.NA

df.to_csv(OUTPUT_FILE, index=False)

print("Labelled dataset created successfully!")
print(f"Experiment: {fault['experiment_id']}")
print(f"Total observations: {len(df)}")
print("Incident-active labels:")
print(df["incident_active"].value_counts())
print(f"Saved to: {OUTPUT_FILE}")
