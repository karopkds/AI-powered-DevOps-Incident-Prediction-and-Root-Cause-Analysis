
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TELEMETRY_FILE = PROJECT_ROOT / "data" / "raw" / "telemetry.csv"
FAULT_LOG_FILE = PROJECT_ROOT / "data" / "fault_injection_log.csv"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "figures"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load actual telemetry measurements
df = pd.read_csv(TELEMETRY_FILE)
df["timestamp_utc"] = pd.to_datetime(
    df["timestamp_utc"], utc=True
)

df["error_5xx_rate"] = pd.to_numeric(
    df["error_5xx_rate"], errors="coerce"
)

df = df.sort_values("timestamp_utc")

# Load the most recent fault experiment
faults = pd.read_csv(FAULT_LOG_FILE)
fault = faults.iloc[-1]

fault_start = pd.to_datetime(
    fault["start_time_utc"], utc=True
)
fault_end = pd.to_datetime(
    fault["end_time_utc"], utc=True
)

# Plot actual measured 5xx error rate
fig, ax = plt.subplots(figsize=(12, 5))

ax.plot(
    df["timestamp_utc"],
    df["error_5xx_rate"],
    label="Measured HTTP 5xx error rate",
    linewidth=2
)

# Highlight the recorded fault injection period
ax.axvspan(
    fault_start,
    fault_end,
    alpha=0.25,
    label="Fault injection period"
)

ax.axvline(
    fault_start,
    linestyle="--",
    label="Fault start"
)

ax.set_title(
    "AIOps: Normal vs HTTP 500 Fault Experiment"
)
ax.set_xlabel("Time (UTC)")
ax.set_ylabel("HTTP 5xx Errors per Second")

ax.legend()
ax.grid(True, alpha=0.3)

fig.autofmt_xdate()
plt.tight_layout()

OUTPUT_FILE = OUTPUT_DIR / "normal_vs_incident.png"

plt.savefig(OUTPUT_FILE, dpi=200)
plt.show()

print(f"Plot saved to: {OUTPUT_FILE}")
