# AIOps Intelligence Platform — Project Progress & Restart Runbook

> **Progress snapshot: November 5, 2026.** This section documents the hands-on work verified in the project screenshots. The original ML design and model-selection notes are preserved below.

## Current implementation status

| Area | Status | Evidence / notes |
|---|---|---|
| Flask application | Completed | `/`, `/health`, `/metrics`, `/simulate-error` routes created |
| Prometheus instrumentation | Completed | `prometheus-client` counters and latency histogram exposed |
| Docker image | Completed | `aiops-incident-prediction:v2` built and loaded into Minikube |
| Kubernetes deployment | Completed | `aiops-app` rollout successful; new Pod reported Running |
| Kubernetes Service | Completed | `aiops-app-services`, NodePort `32008`, port `5000` |
| Prometheus monitoring stack | Completed | kube-prometheus-stack installed in `monitoring` namespace |
| ServiceMonitor integration | Completed | Prometheus target reported **UP** |
| Prometheus query validation | Completed | `http_requests_total` returned time series |
| Grafana dashboards | Completed | HTTP requests/sec and HTTP 5xx error-rate panels plotted |
| Grafana alert rule | Completed | `AIOps - High HTTP 5xx Error Rate` transitioned to **Firing** during simulation |
| Slack/contact-point notifications | **Deferred** | Alert fired, but contact point showed `empty` |
| Telemetry dataset / ML training | Not started | Next session begins with metrics collector |
| SHAP, RCA, RAG, LLM | Planned | Architecture only; not yet implemented |

## Implementation walkthrough — what we completed

### Step 1 — Flask application and health endpoint

- Created `src/app/app.py` with a Flask web application running on port `5000`.
- `GET /` responds with an AIOps application message.
- `GET /health` returns `{"status":"healthy"}` so we can verify the application responds.
- `GET /simulate-error` deliberately returns HTTP **500** for controlled incident testing. **This is a test endpoint, not a real production failure.**
- Added `Flask` and `prometheus-client` to `src/app/requirements.txt`.

**Why:** A small instrumented service provides a reproducible target for deployment, monitoring, and simulated incidents.

### Step 2 — Prometheus metrics in Flask

- Created `http_requests_total` as a Counter labeled by HTTP method, endpoint, and status.
- Created `http_request_duration_seconds` as a Histogram labeled by method and endpoint.
- Used Flask `before_request` and `after_request` hooks to measure request processing time and update metrics.
- Excluded `/metrics` from application request measurements to avoid counting Prometheus scrapes as user traffic.
- Exposed `GET /metrics` using `generate_latest()` and the Prometheus content type.
- Verified locally that `/health` returned healthy JSON and `/metrics` exposed metric samples.

**Why:** Prometheus requires a scrapeable metrics endpoint; the counter supports traffic and error-rate queries, while the histogram supports latency analysis.

### Step 3 — Docker packaging

- Dockerfile: `src/app/Dockerfile`; base image `python:3.12-slim`.
- Dockerfile installs requirements, copies `app.py`, exposes `5000`, and runs `python app.py`.
- Built a new version after adding instrumentation:

```powershell
docker build -t aiops-incident-prediction:v2 .\src\app
docker images
```

**Why:** The image packages the app and dependencies for consistent Kubernetes execution. The host virtual environment is not copied into the image.

### Step 4 — Minikube and Kubernetes deployment

- Used Minikube with the Docker driver on Windows.
- Loaded the image into Minikube:

```powershell
minikube image load aiops-incident-prediction:v2
minikube image ls
```

- Deployment manifest: `kubernetes/deployment.yaml`, deployment `aiops-app`, image `aiops-incident-prediction:v2`, `imagePullPolicy: Never` for the locally loaded image.
- Applied the manifest and verified the rollout:

```powershell
kubectl apply -f .\kubernetes\deployment.yaml
kubectl rollout status deployment/aiops-app --timeout=120s
kubectl get pods
```

- The new Pod was **1/1 Running**. An older Pod from a prior ReplicaSet was also visible with a `Terminating` status; that is normal during a rollout if it subsequently disappears.

**Why:** Kubernetes maintains the desired number of application Pods and replaces them during deployments.

### Step 5 — Kubernetes Service and access

- Manifest: `kubernetes/service.yaml`.
- Service: `aiops-app-services` in the `default` namespace, type `NodePort`.
- Selector `app: aiops-app` routes traffic to matching Pods.
- Named service port `http-metrics`: TCP `5000` -> target `5000`; NodePort `32008`.

```powershell
kubectl apply -f .\kubernetes\service.yaml
kubectl get svc aiops-app-services
minikube service aiops-app-services --url
```

**Why:** A Service provides a stable network endpoint even if a Pod is replaced. On Windows with the Docker driver, `minikube service --url` may start a tunnel that must remain open.

### Step 6 — Prometheus stack

- Installed the Helm-based kube-prometheus-stack release `monitoring-stack` in namespace `monitoring`.
- Verified Prometheus, operator, Grafana, node exporter, and related monitoring workloads.
- Prometheus custom resource: `monitoring-stack-kube-prom-prometheus`; its status showed one available replica.

```powershell
kubectl get pods -n monitoring
kubectl get prometheus -n monitoring
kubectl get svc -n monitoring
```

**Why:** Prometheus stores time-series telemetry, while the operator configures monitoring resources using Kubernetes custom resources.

### Step 7 — ServiceMonitor discovery

- Manifest: `monitoring/aiops-servicemonitor.yaml`.
- Created `ServiceMonitor` named `aiops-servicemonitor` in namespace `monitoring` with label `release: monitoring-stack`.
- Selected Service label `app: aiops-app` in namespace `default`.
- Configured endpoint port `http-metrics`, path `/metrics`, scrape interval `15s`.

```powershell
kubectl apply -f .\monitoring\aiops-servicemonitor.yaml
kubectl get servicemonitor -n monitoring
```

- In Prometheus **Status > Target health**, target `serviceMonitor/monitoring/aiops-servicemonitor/0` showed **1/1 UP**.

**Why:** A ServiceMonitor tells the Prometheus Operator which Kubernetes Service endpoint to scrape. A target marked UP verifies scraping, not necessarily that every app operation is healthy.

### Step 8 — PromQL validation and Grafana dashboards

- In Prometheus, querying `http_requests_total` returned labeled time series, including HTTP 200 and 404 requests.
- In Grafana, created an **HTTP Requests per Second** panel:

```promql
sum(rate(http_requests_total{job="aiops-app-services"}[5m]))
```

- Created an **HTTP 5xx Error Rate** panel:

```promql
sum(rate(http_requests_total{job="aiops-app-services",status=~"5.."}[5m]))
```

- Both charts displayed traffic/error activity after test requests.

**Important:** The 5xx panel measures **errors per second**, not the percentage of requests failing. For an actual 5xx *ratio*, use a numerator/denominator query and handle zero traffic explicitly.

### Step 9 — Grafana alert rule and simulated failure

- Created rule `AIOps - High HTTP 5xx Error Rate` in folder `AIOps-Incident-Monitoring` and evaluation group `aiops-alert-group`.
- PromQL query used the 5xx errors/second expression above.
- Threshold: **above 0.1 errors/second**; evaluation every **30 seconds**; pending period **30 seconds**; keep firing **0 seconds**.
- Triggered requests to `/simulate-error` to generate HTTP 500 responses.
- Verified rule changed from **Normal** to **Firing** and the metric crossed the threshold.
- The notification contact point was **empty**. Alert detection works, but **Slack/email delivery is not configured or verified**.

**Why:** This is a complete test of the metrics-to-alert detection path. Delivery of notifications is a separate configuration step.

---

## Next session — planned ML work (not completed yet)

1. Create `src/collect_metrics.py` and query the Prometheus HTTP API for time-series data.
2. Save timestamped observations in `data/` and validate time windows, missing values, and sampling intervals.
3. Add features such as requests/sec, 5xx errors/sec, error ratio, latency quantiles, CPU/memory usage, and restart counts **only when their metrics are available**.
4. Run controlled incident simulations, log experiment IDs and ground-truth incident labels, and avoid leaking related windows between training and testing.
5. Train an Isolation Forest anomaly-detection baseline; then benchmark supervised incident classifiers as outlined in the original ML plan below.
6. Later implement SHAP explanations, probable RCA, RAG/LLM guidance, and notification delivery.

**Checkpoint to resume:** Infrastructure monitoring and a Grafana alert are working; the immediate next task is **Prometheus telemetry collection into a dataset**. Slack contact-point setup is intentionally postponed.

---

# Original ML architecture and model plan (preserved)

# Machine Learning Models & Algorithms

## AIOps Intelligence Platform
### AI-Powered DevOps Incident Prediction, Anomaly Detection & Root Cause Analysis

## 1. Overview

The AIOps Intelligence Platform uses multiple machine-learning algorithms because the project solves two main ML problems:

1. **Anomaly Detection** — determine whether current infrastructure behaviour is normal or abnormal.
2. **Incident Classification** — if behaviour resembles a known failure, determine the incident category.

## 2. ML Architecture

```text
Kubernetes Infrastructure
          |
          v
Prometheus Telemetry
          |
          v
Data Preprocessing
          |
          v
Feature Engineering
          |
          +---------------------------+
          |                           |
          v                           v
 Isolation Forest              Classification Model
 Anomaly Detection             XGBoost / Random Forest
          |                           |
          v                           v
 Normal / Anomalous             Incident Category
          |                           |
          +-------------+-------------+
                        |
                        v
                      SHAP
                        |
                        v
               Explainable Prediction
                        |
                        v
               Root-Cause Analysis
                        |
                        v
                   RAG + LLM
                        |
                        v
              Incident Explanation
             + Recommended Action
```

## 3. Primary Models

| Component | Algorithm | Learning Type | Purpose |
|---|---|---|---|
| Anomaly Detection | Isolation Forest | Unsupervised | Detect unusual infrastructure behaviour |
| Incident Classification | XGBoost | Supervised | Classify known incident categories |
| Classification Comparison | Random Forest | Supervised | Benchmark against XGBoost |
| Baseline Classification | Logistic Regression | Supervised | Establish a simple baseline |
| Baseline Classification | Decision Tree | Supervised | Establish an interpretable tree baseline |
| Explainability | SHAP | Explainable AI | Explain individual predictions |
| Advanced Anomaly Detection | Autoencoder | Deep Learning | Compare with Isolation Forest |

The final production classifier will be selected from experimental results rather than assuming one algorithm is best.

## 4. Isolation Forest — Anomaly Detection

Isolation Forest is the primary unsupervised anomaly-detection algorithm.

It answers:

> **Is the current infrastructure behaviour unusual?**

Example telemetry:

```text
CPU Usage       : 96%
Memory Usage    : 74%
Latency         : 920 ms
HTTP Error Rate : 13%
Pod Restarts    : 2
```

The model may identify this combination as anomalous compared with the healthy operating baseline.

### Why Isolation Forest?

- Designed specifically for anomaly detection.
- Does not require labels for every possible abnormal condition.
- Suitable for multivariate numerical telemetry.
- Computationally practical for the initial real-time pipeline.
- Provides an anomaly score that can be incorporated into the incident workflow.

## 5. XGBoost — Incident Classification

XGBoost is the primary candidate for supervised incident classification.

It answers:

> **What known incident does this telemetry most closely represent?**

Target classes may include:

```text
NORMAL
CPU_OVERLOAD
MEMORY_PRESSURE
TRAFFIC_SPIKE
HIGH_LATENCY
APPLICATION_FAILURE
HTTP_5XX_ERROR
RESOURCE_THROTTLING
```

Example input:

```text
CPU Usage       : 96%
Memory Usage    : 73%
Latency         : 850 ms
HTTP 5xx Rate   : 8%
Request Rate    : 250/sec
Pod Restarts    : 0
CPU Throttling  : High
```

Example prediction:

```text
Predicted Incident: CPU_OVERLOAD
```

## 6. Classification Model Comparison

The project will not assume XGBoost is automatically the best classifier.

Candidate models:

```text
Logistic Regression
        |
Decision Tree
        |
Random Forest
        |
XGBoost
```

They will be compared using:

- Precision
- Recall
- F1-score
- Macro F1
- Weighted F1
- Confusion matrix
- ROC-AUC / PR-AUC where appropriate
- Inference characteristics

The classifier with the strongest validated performance and suitable operational characteristics will be selected.

## 7. Random Forest

Random Forest is included as a strong tree-based comparison model.

Reasons for inclusion:

- Handles nonlinear relationships.
- Works well with tabular telemetry.
- Supports multiclass classification.
- Provides feature importance.
- Requires relatively little preprocessing.
- Provides a useful comparison with boosted trees.

## 8. Logistic Regression

Logistic Regression provides a simple supervised baseline.

A baseline is important because the project needs to demonstrate whether more complex models provide measurable improvements.

## 9. Decision Tree

A Decision Tree provides another interpretable baseline.

It can help illustrate rules learned from telemetry, such as relationships among CPU usage, latency, errors and restart behaviour.

## 10. SHAP — Explainable AI

SHAP is not the primary prediction model.

It is used to explain why the selected classifier produced a prediction.

Example:

```text
Prediction: CPU_OVERLOAD

Major contributors:
CPU Usage       -> Strong positive contribution
CPU Throttling  -> Strong positive contribution
Latency         -> Moderate positive contribution
Memory          -> Small contribution
```

This allows the system to provide evidence instead of only returning an incident label.

## 11. Root-Cause Analysis

Incident classification and root-cause analysis are different tasks.

For example:

```text
Observed symptom:
HIGH_LATENCY
```

Possible underlying causes could include:

```text
CPU saturation
Memory pressure
Traffic spike
Network delay
Application dependency
```

The RCA component will combine:

- ML prediction
- SHAP evidence
- telemetry relationships
- temporal behaviour
- service context
- known incident patterns

The result will be presented as a **probable root cause**, not as guaranteed causation.

## 12. Autoencoder — Advanced Experiment

An Autoencoder may be implemented as an advanced anomaly-detection experiment.

The purpose is to compare a deep-learning approach with Isolation Forest.

Conceptually:

```text
Normal Telemetry
      |
      v
   Encoder
      |
      v
Compressed Representation
      |
      v
   Decoder
      |
      v
Reconstructed Telemetry
```

If reconstruction error becomes unusually high, the observation may be considered anomalous.

The Autoencoder is an enhancement, not a dependency for the minimum viable project.

## 13. Complete Intelligence Pipeline

```text
Kubernetes
     |
     v
Prometheus
     |
     v
Telemetry Collector
     |
     v
Preprocessing
     |
     v
Feature Engineering
     |
     v
Isolation Forest
"Is it abnormal?"
     |
     v
Anomaly Detected
     |
     v
XGBoost / Selected Classifier
"What known incident is it?"
     |
     v
Incident Prediction
     |
     v
SHAP
"Why did the model predict this?"
     |
     v
RCA
"What is the probable cause?"
     |
     v
RAG
"What relevant runbook/documentation applies?"
     |
     v
LLM
"How can the evidence be communicated clearly?"
     |
     v
Incident Explanation + Investigation Guidance
```

## 14. Evaluation Strategy

### Incident Classification

The following metrics will be used:

- Precision
- Recall
- F1-score
- Macro F1
- Weighted F1
- Confusion Matrix
- ROC-AUC / PR-AUC where appropriate

### Anomaly Detection

Evaluation will include:

- Precision
- Recall
- F1-score
- False-positive rate
- False-negative rate
- Detection latency

Example:

```text
Incident injected : 14:20:00
Anomaly detected  : 14:20:30

Detection latency : 30 seconds
```

## 15. Preventing Data Leakage

Telemetry observations from the same fault-injection experiment can be highly similar.

Therefore, where appropriate, train/test splitting will be performed by:

- experiment ID
- incident run
- time window

rather than blindly performing a random row-level split.

## 16. Final Model Selection

The planned architecture is:

```text
Anomaly Detection:
Isolation Forest
        +
Optional Autoencoder Comparison

Incident Classification:
Logistic Regression
        vs
Decision Tree
        vs
Random Forest
        vs
XGBoost
```

The final classifier will be selected only after experimental evaluation.

## 17. Viva / Interview Answer

If asked **"Which ML models are you using?"**, the concise answer is:

> Our AIOps platform uses Isolation Forest for unsupervised anomaly detection and a supervised tree-based classifier for known incident classification. XGBoost is our primary candidate, but we benchmark it against Logistic Regression, Decision Tree and Random Forest before selecting the final model. We use SHAP for explainability and may compare Isolation Forest with an Autoencoder as an advanced anomaly-detection experiment. RAG and the LLM operate downstream for grounded incident explanation and troubleshooting guidance; they are not the primary incident-detection models.

## 18. Summary

```text
Isolation Forest
      |
      +--> Detect abnormal behaviour

XGBoost / Selected Classifier
      |
      +--> Identify known incident type

SHAP
      |
      +--> Explain model prediction

RCA
      |
      +--> Estimate probable cause

RAG
      |
      +--> Retrieve relevant operational knowledge

LLM
      |
      +--> Generate grounded, human-readable guidance
```

The core design principle is:

> **Detect with ML → Explain with XAI → Investigate with RCA → Retrieve with RAG → Communicate with an LLM.**
