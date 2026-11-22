"""Module 3: real-time alerts and dashboard (Streamlit), version 2.

Replays records from KDDTest+ through the trained model to simulate live traffic.
Run:  streamlit run app.py
"""
import json, subprocess, sys
from datetime import datetime
from pathlib import Path
import altair as alt
import joblib, numpy as np, pandas as pd, streamlit as st
from common import CLASSES, load
from report import build_pdf

ROOT = Path(__file__).parent
LOG = ROOT / "logs/alerts_log.csv"
SEVERITY = {"Probe": 1, "DoS": 2, "R2L": 2, "U2R": 3}
COLORS = {"Normal": "#2FBECD", "DoS": "#D64545", "Probe": "#E0902E", "R2L": "#7A5BC0", "U2R": "#B8327A"}
RISK_COLORS = {"High": "#D64545", "Medium": "#E0902E", "Low": "#2FBECD"}
SCALE = alt.Scale(domain=list(COLORS), range=list(COLORS.values()))
DESC = {"Normal": "Ordinary, harmless traffic.",
        "DoS": "Denial of Service: floods a server with requests until it stops responding (e.g. neptune, smurf).",
        "Probe": "Scanning or surveillance: looks for open ports and weak points (e.g. portsweep, nmap).",
        "R2L": "Remote to Local: an outsider tries to gain access, e.g. guessing passwords.",
        "U2R": "User to Root: a normal user tries to gain administrator rights."}

st.set_page_config(page_title="NIDS Dashboard", page_icon="🛡️", layout="wide")

@st.cache_resource
def get_model():
    """Load the saved model. If it was saved with different library versions (or is missing), retrain once."""
    path = ROOT / "models/nids_pipeline.pkl"
    try:
        return joblib.load(path)
    except Exception:
        with st.spinner("The saved model does not match the installed libraries. Retraining it now (about 1-2 minutes)..."):
            subprocess.run([sys.executable, str(ROOT / "train.py")], cwd=ROOT, check=True, capture_output=True)
        return joblib.load(path)

@st.cache_data
def get_stream():
    return load(ROOT / "data/KDDTest+.txt").sample(frac=1.0, random_state=7).reset_index(drop=True)

@st.cache_data
def get_train():
    return load(ROOT / "data/KDDTrain+.txt")

@st.cache_data
def get_tradeoff():
    f = ROOT / "results/threshold_tradeoff.csv"
    if not f.exists(): return None, None
    summ = ROOT / "results/threshold_summary.json"
    return pd.read_csv(f), (json.loads(summ.read_text()) if summ.exists() else {})

@st.cache_data
def get_results_files():
    comp = pd.read_csv(ROOT / "results/model_comparison.csv")
    meta = json.loads((ROOT / "results/metrics.json").read_text())
    return comp, meta

def risk_level(cls: str, conf: float) -> str:
    sev = SEVERITY[cls]
    if sev == 3: return "High"
    if sev == 2: return "High" if conf >= 0.8 else "Medium"
    return "Medium" if conf >= 0.8 else "Low"

bundle, stream = get_model(), get_stream()
pipe, FEATURES = bundle["pipeline"], bundle["features"]

if "pos" not in st.session_state:
    st.session_state.pos, st.session_state.batch, st.session_state.results = 0, 0, pd.DataFrame()
    LOG.parent.mkdir(exist_ok=True)
    LOG.write_text("time,predicted,risk,confidence,protocol,service,src_bytes,dst_bytes,true_label\n")

def process_batch(n: int):
    s = st.session_state
    chunk = stream.iloc[s.pos:s.pos + n]
    if chunk.empty: return
    proba = pipe.predict_proba(chunk[FEATURES])
    thr = st.session_state.get("thr", 0.5)          # alert sensitivity: alert when P(attack) >= thr
    idx = np.where(1 - proba[:, 0] >= thr, 1 + proba[:, 1:].argmax(1), 0)
    conf = proba[np.arange(len(idx)), idx]
    s.batch += 1
    out = pd.DataFrame({
        "batch": s.batch, "time": datetime.now().strftime("%H:%M:%S"),
        "predicted": [CLASSES[i] for i in idx], "actual": chunk["attack_class"].values, "true_label": chunk["label"].values,
        "confidence": conf.round(3), "protocol": chunk["protocol_type"].values, "service": chunk["service"].values,
        "flag": chunk["flag"].values, "duration": chunk["duration"].values,
        "src_bytes": chunk["src_bytes"].values, "dst_bytes": chunk["dst_bytes"].values,
        "connections": chunk["count"].values})
    out["correct"] = out["predicted"] == out["actual"]
    out["risk"] = [risk_level(c, p) if c != "Normal" else "-" for c, p in zip(out["predicted"], out["confidence"])]
    for j, c in enumerate(CLASSES): out[f"p_{c}"] = proba[:, j].round(3)
    s.results = pd.concat([s.results, out], ignore_index=True)
    s.pos += len(chunk)
    a = out[out["predicted"] != "Normal"]
    if len(a):
        a[["time", "predicted", "risk", "confidence", "protocol", "service", "src_bytes", "dst_bytes", "true_label"]].to_csv(LOG, mode="a", header=False, index=False)

# ---------------- sidebar ----------------
with st.sidebar:
    st.header("Controls")
    batch = st.slider("Records per step", 10, 500, 100, 10)
    st.slider("Alert sensitivity (threshold)", 0.05, 0.95, 0.50, 0.05, key="thr",
              help="An alert is raised when the model's attack probability is at least this value. Lower = catches more attacks but gives more false alarms. Applies to the next batch.")
    if st.button("▶ Process next batch", type="primary", width="stretch"): process_batch(batch)
    auto = st.toggle("Auto-run (every 2 s)")
    if st.button("↺ Reset", width="stretch"):
        for k in ("pos", "batch", "results"): st.session_state.pop(k, None)
        st.rerun()
    st.progress(min(1.0, st.session_state.pos / len(stream)), text=f"Replayed {st.session_state.pos:,} of {len(stream):,}")
    if st.button("📄 Create PDF report", width="stretch"):
        with st.spinner("Building report..."):
            st.session_state.pdf = build_pdf(st.session_state.get("results"), st.session_state.get("thr", 0.5), bundle["model_name"])
    if st.session_state.get("pdf"):
        st.download_button("⬇ Download PDF report", st.session_state.pdf, file_name="NIDS_results_report.pdf", mime="application/pdf", width="stretch")
    st.markdown(f"**Model:** {bundle['model_name']}  \n**Dataset:** NSL-KDD (KDDTest+)  \n**Features used:** 30 of 41")
    st.info("Alerts are suggestions for analyst review. No traffic is blocked automatically.")

st.title("🛡️ Network Intrusion Detection Dashboard")
st.caption("Detect • Classify • Alert  |  Replaying KDDTest+ records to simulate live traffic")
tab1, tab2, tab3, tab4 = st.tabs(["📡 Live monitor", "📈 Model performance", "🗂 Dataset", "ℹ️ How it works"])

# ---------------- tab 1: live monitor ----------------
with tab1:
    @st.fragment(run_every=2 if auto else None)
    def monitor():
        if auto and st.session_state.pos < len(stream): process_batch(batch)
        r = st.session_state.results
        if r.empty:
            st.info("No traffic yet. Click **Process next batch** in the sidebar, or turn on **Auto-run**.")
            return
        total = len(r); att = r[r["predicted"] != "Normal"]
        high = int((att["risk"] == "High").sum())
        k = st.columns(6)
        k[0].metric("Total flows", f"{total:,}")
        k[1].metric("Normal", f"{total - len(att):,}")
        k[2].metric("Suspected attacks", f"{len(att):,}")
        k[3].metric("Attack rate", f"{len(att) / total:.0%}")
        k[4].metric("High-risk alerts", f"{high:,}")
        k[5].metric("Avg. confidence", f"{r['confidence'].mean():.2f}")

        c1, c2 = st.columns([3, 2])
        with c1:
            st.subheader("Detections per batch")
            tl = r.groupby(["batch", "predicted"]).size().reset_index(name="flows")
            st.altair_chart(alt.Chart(tl).mark_bar().encode(
                x=alt.X("batch:O", title="Batch number"), y=alt.Y("flows:Q", title="Flows"),
                color=alt.Color("predicted:N", scale=SCALE, legend=alt.Legend(title="Predicted")),
                tooltip=["batch", "predicted", "flows"]).properties(height=280), width="stretch")
        with c2:
            st.subheader("Traffic share")
            sh = r["predicted"].value_counts().rename_axis("class").reset_index(name="flows")
            sh["share"] = (sh["flows"] / total).round(3)
            st.altair_chart(alt.Chart(sh).mark_arc(innerRadius=60).encode(
                theta="flows:Q", color=alt.Color("class:N", scale=SCALE, legend=alt.Legend(title=None)),
                tooltip=["class", "flows", alt.Tooltip("share:Q", format=".1%")]).properties(height=280), width="stretch")

        c3, c4, c5 = st.columns(3)
        with c3:
            st.subheader("Alerts by risk")
            rk = att["risk"].value_counts().reindex(["High", "Medium", "Low"]).fillna(0).astype(int).rename_axis("risk").reset_index(name="alerts")
            st.altair_chart(alt.Chart(rk).mark_bar().encode(
                x=alt.X("risk:N", sort=["High", "Medium", "Low"], title=None), y=alt.Y("alerts:Q", title="Alerts"),
                color=alt.Color("risk:N", scale=alt.Scale(domain=list(RISK_COLORS), range=list(RISK_COLORS.values())), legend=None),
                tooltip=["risk", "alerts"]).properties(height=240), width="stretch")
        with c4:
            st.subheader("Services targeted")
            sv = att["service"].value_counts().head(8).rename_axis("service").reset_index(name="alerts")
            st.altair_chart(alt.Chart(sv).mark_bar(color="#1E66AA").encode(
                y=alt.Y("service:N", sort="-x", title=None), x=alt.X("alerts:Q", title="Alerts"),
                tooltip=["service", "alerts"]).properties(height=240), width="stretch")
        with c5:
            st.subheader("Protocol mix")
            pm = r.groupby(["protocol", "predicted"]).size().reset_index(name="flows")
            st.altair_chart(alt.Chart(pm).mark_bar().encode(
                x=alt.X("protocol:N", title=None), y=alt.Y("flows:Q", title="Flows"),
                color=alt.Color("predicted:N", scale=SCALE, legend=None),
                tooltip=["protocol", "predicted", "flows"]).properties(height=240), width="stretch")

        st.subheader("Running check against the true labels")
        a1, a2 = st.columns([1, 2])
        a1.metric("Predictions that match the dataset label", f"{r['correct'].mean():.1%}")
        a1.caption("This is only possible because the replay data is labelled. On real traffic, labels are unknown.")
        miss = r[~r["correct"]].groupby(["actual", "predicted"]).size().reset_index(name="flows").sort_values("flows", ascending=False).head(6)
        a2.write("**Most common mistakes** (actual → predicted)")
        miss["mistake"] = miss["actual"] + " → " + miss["predicted"]
        a2.dataframe(miss[["mistake", "flows"]], hide_index=True, width="stretch")

        st.subheader("Alert log")
        f1, f2, f3 = st.columns([2, 2, 2])
        cls_sel = f1.multiselect("Attack type", [c for c in CLASSES if c != "Normal"], default=[c for c in CLASSES if c != "Normal"])
        risk_sel = f2.multiselect("Risk", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
        min_conf = f3.slider("Minimum confidence", 0.0, 1.0, 0.0, 0.05)
        view = att[att["predicted"].isin(cls_sel) & att["risk"].isin(risk_sel) & (att["confidence"] >= min_conf)]
        st.caption(f"Showing the latest 15 of {len(view):,} matching alerts")
        cols = ["time", "predicted", "risk", "confidence", "protocol", "service", "flag", "duration", "src_bytes", "dst_bytes", "connections", "true_label"]
        st.dataframe(view.tail(15).iloc[::-1][cols], hide_index=True, width="stretch")
        if LOG.exists() and LOG.stat().st_size > 100:
            st.download_button("⬇ Download alert log (CSV)", LOG.read_bytes(), file_name="alerts_log.csv", mime="text/csv")

        if len(view):
            st.subheader("Inspect one alert")
            recent = view.tail(15).iloc[::-1]
            labels = [f"#{i + 1}  {row.time}  {row.predicted}  {row.protocol}/{row.service}" for i, row in enumerate(recent.itertuples())]
            pick = st.selectbox("Choose an alert", labels)
            row = recent.iloc[labels.index(pick)]
            d1, d2 = st.columns([2, 3])
            with d1:
                st.markdown(f"**Predicted:** {row['predicted']} &nbsp;|&nbsp; **Risk:** {row['risk']} &nbsp;|&nbsp; **Confidence:** {row['confidence']:.2f}")
                st.markdown(f"**Dataset label:** `{row['true_label']}` ({row['actual']}) → {'✅ correct' if row['correct'] else '❌ model was wrong'}")
                st.write(DESC[row["predicted"]])
                st.caption(f"Connection: {row['protocol']} / {row['service']}, flag {row['flag']}, {row['duration']} s, "
                           f"{row['src_bytes']:,} bytes sent, {row['dst_bytes']:,} bytes received, {row['connections']} connections to the same host in 2 s.")
            with d2:
                pr = pd.DataFrame({"class": CLASSES, "probability": [row[f"p_{c}"] for c in CLASSES]})
                st.altair_chart(alt.Chart(pr).mark_bar().encode(
                    x=alt.X("probability:Q", scale=alt.Scale(domain=[0, 1]), title="Model probability"),
                    y=alt.Y("class:N", sort=CLASSES, title=None), color=alt.Color("class:N", scale=SCALE, legend=None),
                    tooltip=["class", alt.Tooltip("probability:Q", format=".3f")]).properties(height=200), width="stretch")
    monitor()

# ---------------- tab 2: model performance ----------------
with tab2:
    comp, meta = get_results_files()
    st.subheader("Model comparison on the official test file (22,544 records)")
    tbl = comp[["model", "test_accuracy", "test_precision_macro", "test_recall_macro", "test_f1_macro", "test_false_positive_rate", "test_detection_rate", "latency_ms_per_record"]].copy()
    tbl.columns = ["Model", "Accuracy", "Precision (macro)", "Recall (macro)", "F1 (macro)", "False positive rate", "Attack detection rate", "Latency (ms/record)"]
    st.dataframe(tbl.style.format({c: "{:.1%}" for c in ["Accuracy", "False positive rate", "Attack detection rate"]} |
                                  {c: "{:.3f}" for c in ["Precision (macro)", "Recall (macro)", "F1 (macro)"]} | {"Latency (ms/record)": "{:.1f}"}),
                 hide_index=True, width="stretch")
    st.caption(f"Selected model: **{meta['best_model']}**, chosen on a validation split (macro-F1 {comp.loc[comp.model == meta['best_model'], 'val_f1_macro'].iloc[0]:.3f}), then tested once on KDDTest+.")
    m1, m2 = st.columns(2)
    with m1:
        st.subheader("Scores by model")
        melt = tbl.melt("Model", ["Accuracy", "F1 (macro)", "Attack detection rate"], var_name="metric", value_name="score")
        st.altair_chart(alt.Chart(melt).mark_bar().encode(
            x=alt.X("metric:N", title=None, axis=alt.Axis(labelAngle=0)), xOffset="Model:N", y=alt.Y("score:Q", scale=alt.Scale(domain=[0, 1]), title="Score"),
            color=alt.Color("Model:N", scale=alt.Scale(range=["#5A6E82", "#1E66AA", "#2FBECD"])), tooltip=["Model", "metric", alt.Tooltip("score:Q", format=".3f")]).properties(height=300), width="stretch")
    with m2:
        st.subheader("Confusion matrix (selected model)")
        cm = np.array(meta["confusion_matrix"])
        cmd = pd.DataFrame([{"Actual": CLASSES[i], "Predicted": CLASSES[j], "records": int(cm[i, j])} for i in range(5) for j in range(5)])
        base = alt.Chart(cmd).encode(x=alt.X("Predicted:N", sort=CLASSES, axis=alt.Axis(labelAngle=0)), y=alt.Y("Actual:N", sort=CLASSES))
        st.altair_chart(base.mark_rect().encode(color=alt.Color("records:Q", scale=alt.Scale(scheme="blues"), legend=None), tooltip=["Actual", "Predicted", "records"]) +
                        base.mark_text(fontSize=13).encode(text="records:Q", color=alt.condition(alt.datum.records > 3500, alt.value("white"), alt.value("#23303E"))).properties(height=300), width="stretch")
    st.subheader("Per-class results")
    prec = [cm[j, j] / max(1, cm[:, j].sum()) for j in range(5)]; rec = [cm[i, i] / max(1, cm[i, :].sum()) for i in range(5)]
    f1 = [2 * p * r_ / (p + r_) if (p + r_) else 0 for p, r_ in zip(prec, rec)]
    pc = pd.DataFrame({"Class": CLASSES, "Records in test file": cm.sum(1), "Precision": prec, "Recall": rec, "F1": f1})
    p1, p2 = st.columns([3, 2])
    p1.dataframe(pc.style.format({"Precision": "{:.2f}", "Recall": "{:.2f}", "F1": "{:.2f}", "Records in test file": "{:,}"}), hide_index=True, width="stretch")
    with p2:
        rc = pc.melt("Class", ["Precision", "Recall"], var_name="metric", value_name="score")
        st.altair_chart(alt.Chart(rc).mark_bar().encode(x=alt.X("Class:N", sort=CLASSES, axis=alt.Axis(labelAngle=0), title=None), xOffset="metric:N",
                        y=alt.Y("score:Q", scale=alt.Scale(domain=[0, 1])), color=alt.Color("metric:N", scale=alt.Scale(range=["#1E66AA", "#E0902E"])),
                        tooltip=["Class", "metric", alt.Tooltip("score:Q", format=".2f")]).properties(height=220), width="stretch")
    tdf, tsum = get_tradeoff()
    if tdf is not None:
        st.subheader("Alert sensitivity trade-off (KDDTest+)")
        lo, hi = tdf[tdf.threshold.round(2) == 0.5].iloc[0], tdf[tdf.threshold.round(2) == 0.1].iloc[0]
        t1, t2 = st.columns([5, 4])
        with t1:
            long = tdf.melt("threshold", ["test_detection_rate", "test_false_positive_rate"], var_name="metric", value_name="rate")
            long["metric"] = long["metric"].map({"test_detection_rate": "Attack detection rate", "test_false_positive_rate": "False positive rate"})
            line = alt.Chart(long).mark_line(point=True).encode(
                x=alt.X("threshold:Q", title="Alert threshold on P(attack)"), y=alt.Y("rate:Q", axis=alt.Axis(format="%"), title=None),
                color=alt.Color("metric:N", scale=alt.Scale(range=["#D64545", "#E0902E"]), legend=alt.Legend(title=None, orient="bottom")),
                tooltip=["threshold", "metric", alt.Tooltip("rate:Q", format=".1%")])
            cur = alt.Chart(pd.DataFrame({"threshold": [st.session_state.get("thr", 0.5)]})).mark_rule(strokeDash=[5, 4], color="#5A6E82").encode(x="threshold:Q")
            st.altair_chart((line + cur).properties(height=300), width="stretch")
            st.caption("The dashed line is the sensitivity currently set in the sidebar.")
        with t2:
            show = tdf[tdf.threshold.round(2).isin([0.1, 0.3, 0.5, 0.7, 0.9])][["threshold", "test_detection_rate", "test_false_positive_rate", "test_precision", "test_recall_R2L"]].copy()
            show.columns = ["Threshold", "Attacks caught", "False alarms", "Alert precision", "R2L caught"]
            st.dataframe(show.style.format({"Threshold": "{:.1f}"} | {c: "{:.1%}" for c in show.columns[1:]}), hide_index=True, width="stretch")
        st.markdown(f"Lowering the threshold from 0.5 to 0.1 raises attack detection from **{lo.test_detection_rate:.1%}** to **{hi.test_detection_rate:.1%}** "
                    f"while false alarms go from {lo.test_false_positive_rate:.1%} to {hi.test_false_positive_rate:.1%}. "
                    f"Even at the lowest setting most R2L attacks are still missed, so the threshold helps a little but does not fix unseen attack types. "
                    f"The area under the ROC curve (attack vs normal) is {tsum.get('test_auc_attack_vs_normal', float('nan')):.3f} on KDDTest+ and {tsum.get('val_auc_attack_vs_normal', float('nan')):.3f} on the validation split.")
        st.caption("These thresholds were evaluated on KDDTest+ itself, so read this as a sensitivity analysis, not as a tuned result. The headline numbers above use the default 0.5.")
    st.warning("R2L and U2R attacks are mostly missed (low recall). The test file contains attack types that never appear in the training file, so scores are lower than on the validation split.")
    fi = ROOT / "results/feature_importance.png"
    if fi.exists():
        st.subheader("Most informative features (mutual information)")
        st.image(str(fi), width=560)
    st.caption("Selected features: " + ", ".join(meta["selected_features"]))

# ---------------- tab 3: dataset ----------------
with tab3:
    tr, te = get_train(), get_stream()
    st.subheader("NSL-KDD dataset")
    d = st.columns(4)
    d[0].metric("Training records", f"{len(tr):,}"); d[1].metric("Test records", f"{len(te):,}")
    d[2].metric("Input features", "41"); d[3].metric("Classes", "5")
    both = pd.concat([tr["attack_class"].value_counts().rename("Training"), te["attack_class"].value_counts().rename("Test")], axis=1).reindex(CLASSES).fillna(0).astype(int)
    l, r_ = st.columns(2)
    with l:
        st.subheader("Records per class")
        bm = both.reset_index(names="class").melt("class", var_name="file", value_name="records")
        st.altair_chart(alt.Chart(bm).mark_bar().encode(x=alt.X("class:N", sort=CLASSES, axis=alt.Axis(labelAngle=0), title=None), xOffset="file:N",
                        y=alt.Y("records:Q", title="Records"), color=alt.Color("file:N", scale=alt.Scale(range=["#1E66AA", "#2FBECD"])),
                        tooltip=["class", "file", "records"]).properties(height=300), width="stretch")
        st.caption("Class balance matters: U2R has very few examples, which is why the model struggles with it.")
    with r_:
        st.subheader("Most common specific attacks (test file)")
        sp = te[te["label"] != "normal"]["label"].value_counts().head(10).rename_axis("attack").reset_index(name="records")
        st.altair_chart(alt.Chart(sp).mark_bar(color="#D64545").encode(y=alt.Y("attack:N", sort="-x", title=None), x=alt.X("records:Q", title="Records"),
                        tooltip=["attack", "records"]).properties(height=300), width="stretch")
    unseen = sorted(set(te["label"]) - set(tr["label"]))
    n_unseen = int(te["label"].isin(unseen).sum())
    st.info(f"**{len(unseen)} attack types appear only in the test file** ({n_unseen:,} records, {n_unseen / len(te):.0%} of the test set), for example: {', '.join(unseen[:8])}. "
            "This is why accuracy on KDDTest+ is lower than on the validation split.")
    st.subheader("What each class means")
    st.table(pd.DataFrame({"Class": CLASSES, "Meaning": [DESC[c] for c in CLASSES]}))
    st.caption("Source: M. Tavallaee et al., 'A Detailed Analysis of the KDD CUP 99 Data Set', 2009.")

# ---------------- tab 4: how it works ----------------
with tab4:
    st.subheader("How the system works")
    st.markdown("""
1. **Traffic data:** each record describes one network connection (protocol, service, bytes sent, error rates and so on).
2. **Preprocessing:** duplicates are removed, categories are encoded as numbers, numeric values are scaled, and the 30 most informative features are kept.
3. **Classifier:** an XGBoost model, trained on labelled records, predicts Normal, DoS, Probe, R2L or U2R and a confidence value.
4. **Risk level:** attack severity is combined with model confidence to give High, Medium or Low.
5. **Alerts:** suspected attacks appear on this dashboard and are saved to `logs/alerts_log.csv` for review.
6. **Human decision:** alerts are suggestions. A security analyst confirms them, and nothing is blocked automatically.
""")
    st.subheader("Risk rules")
    st.table(pd.DataFrame({"Attack type": ["U2R", "DoS, R2L", "Probe"], "Risk": ["High", "High if confidence is 0.8 or more, otherwise Medium", "Medium if confidence is 0.8 or more, otherwise Low"]}))
    st.subheader("Limits")
    st.markdown("- NSL-KDD is an older benchmark, so results on modern networks may differ.\n- Here the traffic is replayed from a file, not captured live.\n- Rare attack types (R2L, U2R) are detected poorly.")
