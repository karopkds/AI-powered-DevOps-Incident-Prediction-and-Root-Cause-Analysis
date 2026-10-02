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
