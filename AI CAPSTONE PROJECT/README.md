# AI-Based Network Intrusion Detection System (NSL-KDD)

Detect • Classify • Alert

## Run
```
pip install -r requirements.txt
python train.py          # Modules 1 and 2: preprocess, select 30 features, train RF / XGBoost / SVM, save best model (~1-2 min)
streamlit run app.py     # Module 3: dashboard that replays KDDTest+ as simulated live traffic
```

## Files
- `common.py`  column names and attack-to-class mapping (Normal, DoS, Probe, R2L, U2R)
- `train.py`   preprocessing, mutual-information feature selection, GridSearchCV for Random Forest, evaluation
- `app.py`     Streamlit dashboard with 4 tabs: Live monitor (KPIs, detections per batch, traffic share, risk, services, protocols, mistakes, filterable alert log, alert inspector), Model performance, Dataset, How it works. Alerts are also saved to `logs/alerts_log.csv`
- `report.py`  builds the PDF report (summary, model results, trade-off, recent alerts) used by the sidebar button "Create PDF report"
- `tradeoff.py` alert-threshold analysis (detection rate vs false alarms), run automatically by `train.py`; powers the sensitivity slider and chart
- `data/`      NSL-KDD KDDTrain+ and KDDTest+ (Tavallaee et al., 2009)
- `results/`   model_comparison.csv, metrics.json, confusion_matrix.png, feature_importance.png, dashboard_screenshot.png

## Method notes
- Scaler, encoder and feature selector are fitted on the training part only (no leakage).
- The best model is chosen on a validation split taken from KDDTrain+, then reported once on KDDTest+.
- KDDTest+ contains attack types not present in training, so scores there are lower than on the validation split.
- Risk level = class severity combined with model confidence. Alerts are for analyst review; nothing is blocked automatically.
