# Requirements Installation Guide

## 📦 **Three Separate Requirements Files**

### **1. `requirements.txt` - Core Application (REQUIRED)**
**For:** Running HELIOS platform (FastAPI, databases, cloud SDKs)

```bash
pip install -r requirements.txt
```

**Includes:**
- FastAPI + Uvicorn
- PostgreSQL (SQLAlchemy, AsyncPG)
- Redis, Kafka clients
- AWS/GCP/Azure SDKs
- Observability (Prometheus, OpenTelemetry)
- Logging, utilities

**Use when:** Setting up HELIOS for the first time

---

### **2. `requirements-ml.txt` - ML Production (OPTIONAL)**
**For:** Running LSTM anomaly detection in production

```bash
pip install -r requirements-ml.txt
```

**Includes:**
- TensorFlow 2.15.0 (Keras model inference)
- NumPy (array operations)
- scikit-learn (feature scaling)

**Use when:** You want to enable LSTM-based anomaly detection

**Note:** HELIOS works fine without this! It auto-falls back to EWMA statistical detector.

---

### **3. `ml/requirements.txt` - ML Training (KAGGLE ONLY)**
**For:** Training LSTM models on Kaggle (NOT for production!)

```bash
# Don't install locally - use on Kaggle instead
pip install -r ml/requirements.txt
```

**Includes:**
- TensorFlow + tf2onnx
- Pandas (data manipulation)
- Matplotlib/Seaborn (visualization)
- ONNX runtime

**Use when:** Training new models on Kaggle notebook

---

## 🚀 **Recommended Installation**

### **Development Setup:**
```bash
# 1. Core platform
pip install -r requirements.txt

# 2. ML inference (optional, for LSTM)
pip install -r requirements-ml.txt
```

### **Production Setup (Minimal):**
```bash
# Core only (uses EWMA fallback)
pip install -r requirements.txt
```

### **Production Setup (With LSTM):**
```bash
# Core + ML
pip install -r requirements.txt
pip install -r requirements-ml.txt
```

---

## 🎯 **Summary**

| File | Purpose | Size | When to Install |
|------|---------|------|-----------------|
| `requirements.txt` | Core platform | ~50 packages | **Always** |
| `requirements-ml.txt` | LSTM inference | ~3 packages | Optional (production ML) |
| `ml/requirements.txt` | Model training | ~10 packages | **Never** (Kaggle only) |

---

## ⚡ **Quick Commands**

```bash
# Full development setup
pip install -r requirements.txt -r requirements-ml.txt

# Production (no ML)
pip install -r requirements.txt

# Production (with ML)
pip install -r requirements.txt -r requirements-ml.txt
```
