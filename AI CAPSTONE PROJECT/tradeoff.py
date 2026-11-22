"""Alert-threshold trade-off: how detection rate and false alarms change with the alert threshold.

An alert is raised when P(attack) = 1 - P(Normal) >= threshold; its type is the most likely attack class.
Run automatically at the end of train.py, or alone:  python tradeoff.py
Writes results/threshold_tradeoff.csv, results/threshold_summary.json and results/threshold_tradeoff.png
"""
import json
from pathlib import Path
import joblib, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from common import CLASSES, COLS, load

ROOT = Path(__file__).parent
THRESHOLDS = np.round(np.arange(0.05, 0.951, 0.05), 2)

def decide(proba, t):
    """Class index per record: Normal unless P(attack) >= t, then the most likely attack class."""
    p_att = 1 - proba[:, 0]
    return np.where(p_att >= t, 1 + proba[:, 1:].argmax(1), 0)

def sweep(proba, y, prefix):
    atk = y != 0
    rows = []
    for t in THRESHOLDS:
        pred = decide(proba, t); flag = pred != 0
        tp = int((flag & atk).sum()); fp = int((flag & ~atk).sum())
        row = {"threshold": float(t), f"{prefix}_detection_rate": tp / max(1, atk.sum()), f"{prefix}_false_positive_rate": fp / max(1, (~atk).sum()),
               f"{prefix}_precision": tp / max(1, tp + fp), f"{prefix}_accuracy": float((pred == y).mean()),
               f"{prefix}_f1_macro": float(f1_score(y, pred, average="macro", zero_division=0))}
        for k, c in enumerate(CLASSES[1:], start=1):
            row[f"{prefix}_recall_{c}"] = float(((pred == k) & (y == k)).sum() / max(1, (y == k).sum()))
        rows.append(row)
    return pd.DataFrame(rows)

def run():
    b = joblib.load(ROOT / "models/nids_pipeline.pkl"); pipe, feats = b["pipeline"], b["features"]
    cls_idx = {c: i for i, c in enumerate(CLASSES)}
    test = load(ROOT / "data/KDDTest+.txt"); yt = test["attack_class"].map(cls_idx).values
    pt = pipe.predict_proba(test[feats])
    tr = load(ROOT / "data/KDDTrain+.txt").drop_duplicates(subset=COLS[:-1] + ["attack_class"]).reset_index(drop=True)
    _, Xv, _, yv = train_test_split(tr[feats], tr["attack_class"].map(cls_idx).values, test_size=0.2, stratify=tr["attack_class"].map(cls_idx).values, random_state=42)
    pv = pipe.predict_proba(Xv)
    df = sweep(pv, yv, "val").merge(sweep(pt, yt, "test"), on="threshold")
    df.to_csv(ROOT / "results/threshold_tradeoff.csv", index=False)
    summary = {"test_auc_attack_vs_normal": float(roc_auc_score(yt != 0, 1 - pt[:, 0])), "val_auc_attack_vs_normal": float(roc_auc_score(yv != 0, 1 - pv[:, 0]))}
    json.dump(summary, open(ROOT / "results/threshold_summary.json", "w"), indent=2)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    ax[0].plot(df["test_false_positive_rate"] * 100, df["test_detection_rate"] * 100, "o-", color="#1E66AA", label="KDDTest+ (unseen attack types)")
    ax[0].plot(df["val_false_positive_rate"] * 100, df["val_detection_rate"] * 100, "o-", color="#2FBECD", label="Validation split")
    ax[0].set_xlabel("False positive rate (%)"); ax[0].set_ylabel("Attack detection rate (%)"); ax[0].set_title("Detection vs false alarms"); ax[0].legend(); ax[0].grid(alpha=.3)
    for _, r in df.iloc[::3].iterrows(): ax[0].annotate(f"{r.threshold:.2f}", (r.test_false_positive_rate * 100, r.test_detection_rate * 100), textcoords="offset points", xytext=(5, -10), fontsize=7)
    ax[1].plot(df["threshold"], df["test_detection_rate"] * 100, color="#D64545", label="Detection rate"); ax[1].plot(df["threshold"], df["test_false_positive_rate"] * 100, color="#E0902E", label="False positive rate")
    ax[1].set_xlabel("Alert threshold on P(attack)"); ax[1].set_ylabel("%"); ax[1].set_title("KDDTest+: effect of threshold"); ax[1].legend(); ax[1].grid(alpha=.3)
    plt.tight_layout(); plt.savefig(ROOT / "results/threshold_tradeoff.png", dpi=150); plt.close()
    return df, summary

if __name__ == "__main__":
    df, s = run()
    show = df[["threshold", "test_detection_rate", "test_false_positive_rate", "test_precision", "test_accuracy", "test_f1_macro", "test_recall_R2L", "test_recall_U2R", "val_detection_rate", "val_false_positive_rate"]]
    print(show.round(3).to_string(index=False)); print(s)
