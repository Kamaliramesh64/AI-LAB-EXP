"""PDF report for the NIDS dashboard (uses matplotlib only, no extra libraries)."""
import io, json
from datetime import datetime
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch
from common import CLASSES

ROOT = Path(__file__).parent
NAVY, BLUE, TEAL, RED, AMBER, MUTED, LIGHT, INK = "#0E2340", "#1E66AA", "#2FBECD", "#D64545", "#E0902E", "#5A6E82", "#EBF3FA", "#23303E"
COLORS = {"Normal": TEAL, "DoS": RED, "Probe": AMBER, "R2L": "#7A5BC0", "U2R": "#B8327A"}
RISK = {"High": RED, "Medium": AMBER, "Low": TEAL}
W, H = 8.27, 11.69   # A4 portrait, inches

def _page(title, subtitle, n):
    fig = plt.figure(figsize=(W, H)); fig.patch.set_facecolor("white")
    fig.text(0.07, 0.962, title, fontsize=18, fontweight="bold", color=NAVY, va="top")
    if subtitle: fig.text(0.07, 0.932, subtitle, fontsize=8.5, color=MUTED, va="top")
    fig.text(0.5, 0.02, f"AI-Based Network Intrusion Detection System  |  Page {n}", fontsize=7.5, color=MUTED, ha="center")
    return fig

def _table(ax, df, widths=None, fs=7.5, scale=1.55):
    ax.axis("off")
    t = ax.table(cellText=df.values.tolist(), colLabels=list(df.columns), loc="upper center", cellLoc="center", colWidths=widths)
    t.auto_set_font_size(False); t.set_fontsize(fs); t.scale(1, scale)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor("#D5E0EA")
        if r == 0: cell.set_facecolor(NAVY); cell.get_text().set_color("white"); cell.get_text().set_fontweight("bold")
        else: cell.set_facecolor(LIGHT if r % 2 == 0 else "white"); cell.get_text().set_color(INK)
    return t

def _kpi(fig, x, y, w, h, label, value, color=INK):
    ax = fig.add_axes([x, y, w, h]); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.08", fc=LIGHT, ec="#D5E0EA", transform=ax.transAxes))
    ax.text(0.5, 0.70, label, ha="center", va="center", fontsize=7, color=MUTED, transform=ax.transAxes)
    ax.text(0.5, 0.33, value, ha="center", va="center", fontsize=15, fontweight="bold", color=color, transform=ax.transAxes)

def _style(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=7.5); ax.grid(axis="y", alpha=0.25)

def _wrap(fig, text, y, width=105, fs=8.5, color=INK):
    import textwrap
    fig.text(0.07, y, "\n".join(textwrap.fill(p, width) for p in text.split("\n")), fontsize=fs, color=color, va="top", linespacing=1.5)

def build_pdf(results, threshold=0.5, model_name="XGBoost") -> bytes:
    """results: the dashboard's session results DataFrame (may be empty)."""
    r = results if results is not None else pd.DataFrame()
    comp = pd.read_csv(ROOT / "results/model_comparison.csv")
    meta = json.loads((ROOT / "results/metrics.json").read_text())
    tf = ROOT / "results/threshold_tradeoff.csv"; tdf = pd.read_csv(tf) if tf.exists() else None
    ts = ROOT / "results/threshold_summary.json"; tsum = json.loads(ts.read_text()) if ts.exists() else {}
    sub = f"Model: {model_name}   |   Dataset: NSL-KDD (KDDTest+ replay)   |   Alert threshold: {threshold:.2f}   |   Generated: {datetime.now():%d %b %Y, %H:%M}"
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        # ---------- page 1: session summary
        fig = _page("Network Intrusion Detection: Results Report", sub, 1)
        fig.text(0.07, 0.895, "1. Traffic analysed in this session", fontsize=12, fontweight="bold", color=BLUE, va="top")
        if r.empty:
            fig.text(0.07, 0.85, "No traffic has been processed yet. Click 'Process next batch' on the dashboard, then create the report again.", fontsize=9, color=MUTED, va="top")
        else:
            total = len(r); att = r[r["predicted"] != "Normal"]; high = int((att["risk"] == "High").sum())
            for i, (lab, val, col) in enumerate([("Total flows", f"{total:,}", INK), ("Normal", f"{total - len(att):,}", TEAL), ("Suspected attacks", f"{len(att):,}", RED),
                                                 ("Attack rate", f"{len(att) / total:.0%}", INK), ("High-risk alerts", f"{high:,}", AMBER), ("Avg. confidence", f"{r['confidence'].mean():.2f}", INK)]):
                _kpi(fig, 0.07 + i * 0.1445, 0.79, 0.132, 0.065, lab, val, col)
            ax = fig.add_axes([0.10, 0.53, 0.38, 0.20]); _style(ax)
            c = r["predicted"].value_counts().reindex(CLASSES).fillna(0)
            ax.bar(CLASSES, c.values, color=[COLORS[k] for k in CLASSES]); ax.set_title("Traffic by predicted class", fontsize=9, color=NAVY, loc="left")
            for i, v in enumerate(c.values): ax.text(i, v, f"{int(v):,}", ha="center", va="bottom", fontsize=7)
            ax = fig.add_axes([0.60, 0.53, 0.33, 0.20]); _style(ax)
            rk = att["risk"].value_counts().reindex(["High", "Medium", "Low"]).fillna(0)
            ax.bar(rk.index, rk.values, color=[RISK[k] for k in rk.index]); ax.set_title("Alerts by risk level", fontsize=9, color=NAVY, loc="left")
            for i, v in enumerate(rk.values): ax.text(i, v, f"{int(v):,}", ha="center", va="bottom", fontsize=7)
            fig.text(0.07, 0.475, f"Predictions matching the dataset labels: {r['correct'].mean():.1%}  (possible only because the replayed data is labelled)", fontsize=8.5, color=INK, va="top")
            ms = r[~r["correct"]].groupby(["actual", "predicted"]).size().reset_index(name="flows").sort_values("flows", ascending=False).head(6)
            fig.text(0.07, 0.435, "Most common mistakes", fontsize=10, fontweight="bold", color=BLUE, va="top")
            if len(ms): _table(fig.add_axes([0.07, 0.30, 0.55, 0.12]), pd.DataFrame({"Actual": ms["actual"], "Predicted": ms["predicted"], "Flows": ms["flows"]}), fs=8)
            else: fig.text(0.07, 0.41, "No mistakes in this session.", fontsize=8.5, color=MUTED, va="top")
            sv = att["service"].value_counts().head(5)
            fig.text(0.68, 0.435, "Most targeted services", fontsize=10, fontweight="bold", color=BLUE, va="top")
            if len(sv): _table(fig.add_axes([0.68, 0.30, 0.25, 0.12]), pd.DataFrame({"Service": sv.index, "Alerts": sv.values}), fs=8)
        _wrap(fig, "Alerts are suggestions for analyst review. No traffic is blocked automatically. Traffic here is replayed from the labelled NSL-KDD test file to simulate live monitoring.", 0.20, 100, 8, MUTED)
        pdf.savefig(fig); plt.close(fig)

        # ---------- page 2: model performance
        fig = _page("Model performance", sub, 2)
        fig.text(0.07, 0.895, "2. Comparison on the official test file (22,544 records)", fontsize=12, fontweight="bold", color=BLUE, va="top")
        t = comp[["model", "test_accuracy", "test_f1_macro", "test_false_positive_rate", "test_detection_rate", "latency_ms_per_record"]].copy()
        t.columns = ["Model", "Accuracy", "F1 (macro)", "False positive rate", "Attack detection", "Latency (ms)"]
        for k in ["Accuracy", "False positive rate", "Attack detection"]: t[k] = t[k].map("{:.1%}".format)
        t["F1 (macro)"] = t["F1 (macro)"].map("{:.3f}".format); t["Latency (ms)"] = t["Latency (ms)"].map("{:.1f}".format)
        _table(fig.add_axes([0.07, 0.76, 0.86, 0.11]), t, fs=8)
        fig.text(0.07, 0.745, f"Selected model: {meta['best_model']}, chosen on a validation split and tested once on KDDTest+.", fontsize=8, color=MUTED, va="top")
        cm = np.array(meta["confusion_matrix"]); ax = fig.add_axes([0.14, 0.40, 0.42, 0.30])
        ax.imshow(cm, cmap="Blues"); ax.set_xticks(range(5), CLASSES, fontsize=7.5); ax.set_yticks(range(5), CLASSES, fontsize=7.5)
        ax.set_xlabel("Predicted", fontsize=8); ax.set_ylabel("Actual", fontsize=8); ax.set_title("Confusion matrix", fontsize=9, color=NAVY, loc="left")
        for i in range(5):
            for j in range(5): ax.text(j, i, int(cm[i, j]), ha="center", va="center", fontsize=7.5, color="white" if cm[i, j] > cm.max() / 2 else INK)
        prec = [cm[j, j] / max(1, cm[:, j].sum()) for j in range(5)]; rec = [cm[i, i] / max(1, cm[i, :].sum()) for i in range(5)]
        pc = pd.DataFrame({"Class": CLASSES, "Records": [f"{int(x):,}" for x in cm.sum(1)], "Precision": [f"{p:.2f}" for p in prec], "Recall": [f"{x:.2f}" for x in rec]})
        fig.text(0.62, 0.69, "Per-class results", fontsize=10, fontweight="bold", color=BLUE, va="top")
        _table(fig.add_axes([0.62, 0.50, 0.32, 0.17]), pc, fs=7.5)
        _wrap(fig, "R2L and U2R attacks are mostly missed (low recall). The test file contains attack types that never appear in the training file, so scores are lower than on the validation split.", 0.33, 105, 8.5, RED)
        _wrap(fig, "Selected features (30 of 41, by mutual information):\n" + ", ".join(meta["selected_features"]), 0.27, 120, 7.5, MUTED)
        pdf.savefig(fig); plt.close(fig)

        # ---------- page 3: trade-off
        fig = _page("Alert sensitivity trade-off", sub, 3)
        fig.text(0.07, 0.895, "3. Detection rate versus false alarms (KDDTest+)", fontsize=12, fontweight="bold", color=BLUE, va="top")
        if tdf is not None:
            ax = fig.add_axes([0.10, 0.62, 0.82, 0.24]); _style(ax)
            ax.plot(tdf["threshold"], tdf["test_detection_rate"] * 100, "o-", color=RED, ms=3, label="Attack detection rate")
            ax.plot(tdf["threshold"], tdf["test_false_positive_rate"] * 100, "o-", color=AMBER, ms=3, label="False positive rate")
            ax.axvline(threshold, ls="--", color=MUTED, lw=1); ax.text(threshold, 3, " current", fontsize=7, color=MUTED)
            ax.set_xlabel("Alert threshold on P(attack)", fontsize=8); ax.set_ylabel("%", fontsize=8); ax.legend(fontsize=7.5, frameon=False, loc="center right")
            sh = tdf[tdf["threshold"].round(2).isin([0.1, 0.3, 0.5, 0.7, 0.9])][["threshold", "test_detection_rate", "test_false_positive_rate", "test_precision", "test_recall_R2L"]].copy()
            sh.columns = ["Threshold", "Attacks caught", "False alarms", "Alert precision", "R2L caught"]; sh["Threshold"] = sh["Threshold"].map("{:.1f}".format)
            for k in sh.columns[1:]: sh[k] = sh[k].map("{:.1%}".format)
            _table(fig.add_axes([0.07, 0.40, 0.86, 0.15]), sh, fs=8)
            lo, hi = tdf[tdf.threshold.round(2) == 0.5].iloc[0], tdf[tdf.threshold.round(2) == 0.1].iloc[0]
            _wrap(fig, f"Lowering the threshold from 0.5 to 0.1 raises attack detection from {lo.test_detection_rate:.1%} to {hi.test_detection_rate:.1%} while false alarms go from {lo.test_false_positive_rate:.1%} to {hi.test_false_positive_rate:.1%}. "
                       f"Most R2L attacks are still missed at every setting, so the threshold helps a little but does not fix unseen attack types.\n"
                       f"Area under the ROC curve (attack vs normal): {tsum.get('test_auc_attack_vs_normal', float('nan')):.3f} on KDDTest+ and {tsum.get('val_auc_attack_vs_normal', float('nan')):.3f} on the validation split.", 0.35, 105, 8.5)
            _wrap(fig, "These thresholds were evaluated on KDDTest+ itself, so this is a sensitivity analysis and not a tuned result. The headline numbers use the default threshold of 0.5.", 0.24, 105, 8, MUTED)
        else:
            fig.text(0.07, 0.85, "Run train.py to create the trade-off results.", fontsize=9, color=MUTED, va="top")
        fig.text(0.07, 0.17, "Limits", fontsize=10, fontweight="bold", color=BLUE, va="top")
        _wrap(fig, "- NSL-KDD is an older benchmark, so results on modern networks may differ.\n- Traffic is replayed from a file, not captured live.\n- Rare attack types (R2L, U2R) are detected poorly.", 0.145, 105, 8.5)
        pdf.savefig(fig); plt.close(fig)

        # ---------- page 4: alerts
        fig = _page("Recent alerts", sub, 4)
        fig.text(0.07, 0.895, "4. Latest alerts from this session", fontsize=12, fontweight="bold", color=BLUE, va="top")
        att = r[r["predicted"] != "Normal"] if not r.empty else r
        if len(att):
            a = att.tail(30).iloc[::-1][["time", "predicted", "risk", "confidence", "protocol", "service", "src_bytes", "true_label"]].copy()
            a.columns = ["Time", "Predicted", "Risk", "Conf.", "Protocol", "Service", "Src bytes", "Dataset label"]; a["Conf."] = a["Conf."].map("{:.2f}".format)
            _table(fig.add_axes([0.07, 0.12, 0.86, 0.75]), a, fs=7, scale=1.45)
            fig.text(0.07, 0.10, f"Showing the latest {len(a)} of {len(att):,} alerts. The full list is in logs/alerts_log.csv.", fontsize=8, color=MUTED, va="top")
        else:
            fig.text(0.07, 0.85, "No alerts in this session yet.", fontsize=9, color=MUTED, va="top")
        pdf.savefig(fig); plt.close(fig)
        d = pdf.infodict(); d["Title"] = "NIDS Results Report"; d["Author"] = "NIDS dashboard"
    return buf.getvalue()
