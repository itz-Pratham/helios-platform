# LSTM Training on Kaggle - Step-by-Step Guide

## 🎯 Goal

Train an LSTM model for anomaly detection using **Kaggle's free TPU**.

---

## 📋 Steps

### **1. Create Kaggle Account**

- Go to https://www.kaggle.com/
- Sign up (free)

---

### **2. Create New Notebook**

1. Click **"Code"** → **"New Notebook"**
2. Settings (right sidebar):
   - **Accelerator:** TPU v3-8
   - **Language:** Python
   - **Environment:** Latest

---

### **3. Copy-Paste Training Code**

Copy the **ENTIRE** contents of `kaggle_lstm_training.py` into the Kaggle notebook.

**File location:**
```
ml/kaggle_lstm_training.py
```

**How to copy:**
1. Open `kaggle_lstm_training.py` in your local editor
2. Select all (Cmd+A / Ctrl+A)
3. Copy (Cmd+C / Ctrl+C)
4. Paste into Kaggle notebook

---

### **4. Run the Notebook**

Click **"Run All"** button (or Shift+Enter for each cell)

**Expected runtime:** ~30-45 minutes on TPU

---

### **5. Monitor Progress**

You'll see these sections execute:

1. ✅ **Install Dependencies** (~2 min)
2. ✅ **Generate Dataset** (~5 min) - Creates 10,000 hours of synthetic data
3. ✅ **Visualize Data** (~2 min) - Shows distributions and time series
4. ✅ **Prepare Sequences** (~3 min) - Creates 60-minute windows
5. ✅ **Train Model** (~20-30 min) - LSTM training on TPU
6. ✅ **Evaluate** (~2 min) - Performance metrics
7. ✅ **Export ONNX** (~2 min) - Convert to production format

---

### **6. Expected Output**

When training completes, you should see:

```
============================================================
🎉 TRAINING COMPLETE!
============================================================

📦 Download these files from Kaggle:
   1. anomaly_detector.onnx  (ONNX model)
   2. scaler.pkl             (Feature scaler)
   3. model_config.json      (Model configuration)

📊 Final Performance:
   Accuracy:  95-98%
   Precision: 92-96%
   Recall:    90-95%
   F1 Score:  91-95%
   AUC-ROC:   0.97-0.99
```

---

### **7. Download Files**

In Kaggle notebook, right sidebar:
- Click **"Output"** tab
- Download these 3 files:
  1. `anomaly_detector.onnx` (~5-10 MB)
  2. `scaler.pkl` (~5 KB)
  3. `model_config.json` (~1 KB)

---

### **8. Move Files to HELIOS**

Place downloaded files in:
```
helios-platform/
├── models/
│   ├── anomaly_detector.onnx      ← ONNX model
│   ├── scaler.pkl                 ← Feature scaler
│   └── model_config.json          ← Configuration
```

Create `models/` directory if it doesn't exist:
```bash
mkdir -p models
```

---

## 🎨 Visualizations You'll See

### 1. Metric Distributions
- Histograms comparing normal vs anomaly data
- 8 metrics side-by-side

### 2. Time Series View
- First 1000 minutes of data
- Anomalies highlighted in red

### 3. Confusion Matrix
- True Positives / False Positives
- True Negatives / False Negatives

### 4. ROC Curve
- Shows model discrimination ability
- AUC should be >0.95

### 5. Training History
- Loss over epochs (should decrease)
- AUC over epochs (should increase)

---

## 📊 Dataset Details

**Generated Data:**
- **Duration:** 10,000 hours (~416 days)
- **Samples:** 600,000 minutes (1 sample/minute)
- **Features:** 8 metrics per sample
- **Sequences:** ~599,940 windows (60-minute each)
- **Anomaly Rate:** ~2-3%
- **File Size:** ~100 MB

**Anomaly Types Injected:**
1. **Missing Events** (AWS degradation)
   - Missing rate: 15-30%
   - Duration: 15-45 minutes

2. **Latency Spike** (Network congestion)
   - Latency: 3-5x normal
   - Duration: 10-30 minutes

3. **Duplicate Storm** (Retry storm)
   - Duplicate rate: 5-15%
   - Duration: 5-20 minutes

4. **Inconsistency Spike** (Schema drift)
   - Inconsistent rate: 3-10%
   - Duration: 10-40 minutes

5. **Traffic Surge** (Black Friday)
   - Event rate: 3-5x normal
   - Duration: 20-60 minutes

---

## 🏗️ Model Architecture

```
Input: (batch_size, 60, 8)
  ↓
LSTM(128, return_sequences=True)
  ↓
Dropout(0.3)
  ↓
BatchNormalization
  ↓
LSTM(64)
  ↓
Dropout(0.3)
  ↓
BatchNormalization
  ↓
Dense(32, relu)
  ↓
Dropout(0.2)
  ↓
Dense(1, sigmoid)
  ↓
Output: Anomaly Probability [0-1]
```

**Total Parameters:** ~150K

---

## 🎯 Success Criteria

Your model should achieve:
- ✅ **Accuracy:** >95%
- ✅ **Precision:** >90% (low false positives)
- ✅ **Recall:** >85% (catch most anomalies)
- ✅ **AUC-ROC:** >0.95
- ✅ **ONNX file size:** <50 MB
- ✅ **Inference time:** <100ms (CPU)

---

## 🐛 Troubleshooting

### **TPU Not Available**
```
Error: TPU initialization failed
```
**Fix:** Change accelerator to GPU in settings, model will still train (slower)

### **Out of Memory**
```
ResourceExhaustedError: OOM
```
**Fix:** Reduce batch size from 256 to 128 in training section

### **ONNX Export Fails**
```
Error: Cannot convert model
```
**Fix:** Make sure `tf2onnx` is installed, or just download `.h5` model and convert locally

---

## 📞 Need Help?

If you see any errors, copy-paste:
1. The **error message**
2. The **section number** where it failed
3. Any **warnings** shown

And I'll help you fix it!

---

## 🚀 Next Steps

After downloading files:
1. ✅ Move files to `models/` directory
2. ✅ Run integration script (coming next)
3. ✅ Test ONNX inference locally
4. ✅ Integrate into HELIOS production code

---

**Estimated Total Time:** 45-60 minutes (most is automated training)
