"""Module 1 + 2: preprocessing, feature selection, model training and evaluation (NSL-KDD).

Usage:  python train.py
Outputs: models/nids_pipeline.pkl, results/*.csv|json|png
"""
import json, time, warnings
from pathlib import Path
import joblib, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             precision_recall_fscore_support, f1_score)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import LinearSVC
from xgboost import XGBClassifier
from common import CAT, CLASSES, COLS, load

warnings.filterwarnings("ignore")
ROOT = Path(__file__).parent
SEED, K_FEATURES = 42, 30
(ROOT / "models").mkdir(exist_ok=True); (ROOT / "results").mkdir(exist_ok=True)

# ---------------- Module 1: data preparation ----------------
train_raw = load(ROOT / "data/KDDTrain+.txt")
test = load(ROOT / "data/KDDTest+.txt")
n_before = len(train_raw)
train_raw = train_raw.drop_duplicates(subset=COLS[:-1] + ["attack_class"]).reset_index(drop=True)
print(f"Train rows: {n_before} -> {len(train_raw)} after removing duplicates; missing values: {int(train_raw.isna().sum().sum())}")

FEATURES = [c for c in COLS if c not in ("label", "difficulty")]
NUM = [c for c in FEATURES if c not in CAT]
cls_idx = {c: i for i, c in enumerate(CLASSES)}
X_all, y_all = train_raw[FEATURES], train_raw["attack_class"].map(cls_idx).values
X_test, y_test = test[FEATURES], test["attack_class"].map(cls_idx).values

# hold-out validation split from the TRAIN file (used for model selection); KDDTest+ stays untouched until the end
X_tr, X_val, y_tr, y_val = train_test_split(X_all, y_all, test_size=0.2, stratify=y_all, random_state=SEED)

pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT),
                         ("num", StandardScaler(), NUM)])
Xtr_t = pre.fit_transform(X_tr)                       # fit on training part only -> no leakage
names = pre.get_feature_names_out()
print("Features after encoding:", Xtr_t.shape[1])

rng = np.random.RandomState(SEED)
sub = rng.choice(len(Xtr_t), size=min(30000, len(Xtr_t)), replace=False)
sel = SelectKBest(mutual_info_classif, k=K_FEATURES)
sel.fit(Xtr_t[sub], y_tr[sub])                        # mutual information, fit on training data only
Xtr_s = sel.transform(Xtr_t)
selected = [str(n).split("__", 1)[1] for n in names[sel.get_support()]]
print(f"Selected {K_FEATURES} features:", selected)
scores = pd.Series(sel.scores_, index=[str(n).split("__", 1)[1] for n in names]).sort_values(ascending=False)
scores.head(15).iloc[::-1].plot.barh(color="#1E66AA", figsize=(7, 5)); plt.title("Top 15 features (mutual information)")
plt.tight_layout(); plt.savefig(ROOT / "results/feature_importance.png", dpi=150); plt.close()

# ---------------- Module 2: models ----------------
print("Tuning Random Forest (GridSearchCV, 3-fold)...")
gs = GridSearchCV(RandomForestClassifier(class_weight="balanced_subsample", n_jobs=-1, random_state=SEED),
                  {"n_estimators": [100, 200], "max_depth": [20, None]}, cv=3, scoring="f1_macro", n_jobs=1)
gs.fit(Xtr_s, y_tr)
print("Best RF params:", gs.best_params_)

cw = {i: len(y_tr) / (len(CLASSES) * np.sum(y_tr == i)) for i in range(len(CLASSES))}
sw = np.array([cw[i] for i in y_tr])
models = {
    "Random Forest": gs.best_estimator_,
    "XGBoost": XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.9, colsample_bytree=0.9,
                             objective="multi:softprob", tree_method="hist", n_jobs=-1, random_state=SEED),
    "SVM (linear)": LinearSVC(C=1.0, class_weight="balanced", max_iter=5000, random_state=SEED),
}
for name, m in models.items():
    if name == "XGBoost": m.fit(Xtr_s, y_tr, sample_weight=sw)
    elif name != "Random Forest": m.fit(Xtr_s, y_tr)

def evaluate(pipe, X, y):
    pred = pipe.predict(X)
    p, r, f, _ = precision_recall_fscore_support(y, pred, average="macro", zero_division=0)
    attack_true, attack_pred = y != 0, pred != 0
    fpr = float(np.mean(attack_pred[~attack_true]))                       # normal flagged as attack
    dr = float(np.mean(attack_pred[attack_true]))                         # attack detected as any attack
    return pred, dict(accuracy=accuracy_score(y, pred), precision_macro=p, recall_macro=r, f1_macro=f,
                      f1_weighted=f1_score(y, pred, average="weighted"), false_positive_rate=fpr, detection_rate=dr)

rows, pipes = [], {}
for name, m in models.items():
    pipe = Pipeline([("pre", pre), ("sel", sel), ("clf", m)]); pipes[name] = pipe
    _, v = evaluate(pipe, X_val, y_val)
    _, t = evaluate(pipe, X_test, y_test)
    one = X_test.iloc[:200]
    t0 = time.perf_counter()
    for i in range(len(one)): pipe.predict(one.iloc[[i]])
    lat = (time.perf_counter() - t0) / len(one) * 1000
    rows.append(dict(model=name, **{f"val_{k}": round(v_, 4) for k, v_ in v.items()},
                     **{f"test_{k}": round(v_, 4) for k, v_ in t.items()}, latency_ms_per_record=round(lat, 2)))
    print(f"{name:14s} val F1={v['f1_macro']:.3f} | KDDTest+ acc={t['accuracy']:.3f} F1(macro)={t['f1_macro']:.3f} FPR={t['false_positive_rate']:.3f} DR={t['detection_rate']:.3f} | {lat:.1f} ms/record")
res = pd.DataFrame(rows); res.to_csv(ROOT / "results/model_comparison.csv", index=False)

best = res.sort_values("val_f1_macro", ascending=False).iloc[0]["model"]    # chosen on validation, not on test
print("Best model (by validation macro-F1):", best)
bp = pipes[best]
pred, tm = evaluate(bp, X_test, y_test)
report = classification_report(y_test, pred, target_names=CLASSES, zero_division=0)
print(report); (ROOT / "results/classification_report_test.txt").write_text(f"Model: {best}\n\n{report}")
cm = confusion_matrix(y_test, pred, labels=range(len(CLASSES)))
fig, ax = plt.subplots(figsize=(6, 5)); ax.imshow(cm, cmap="Blues")
ax.set_xticks(range(5), CLASSES); ax.set_yticks(range(5), CLASSES); ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
ax.set_title(f"{best} on KDDTest+")
for i in range(5):
    for j in range(5): ax.text(j, i, cm[i, j], ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "#23303E", fontsize=9)
plt.tight_layout(); plt.savefig(ROOT / "results/confusion_matrix.png", dpi=150); plt.close()

joblib.dump(dict(pipeline=bp, classes=CLASSES, features=FEATURES, model_name=best), ROOT / "models/nids_pipeline.pkl")
json.dump(dict(best_model=best, rf_params=gs.best_params_, selected_features=selected, train_rows=len(train_raw),
               test_rows=len(test), test_metrics=tm, confusion_matrix=cm.tolist()), open(ROOT / "results/metrics.json", "w"), indent=2)
print("Saved model + results.")

from tradeoff import run as run_tradeoff          # alert-threshold trade-off on the saved model
_, _summary = run_tradeoff()
print("Saved results/threshold_tradeoff.csv. AUC (attack vs normal) on KDDTest+: %.3f" % _summary["test_auc_attack_vs_normal"])
