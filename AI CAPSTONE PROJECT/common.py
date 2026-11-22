"""Shared constants and helpers for the NIDS project (NSL-KDD)."""
import pandas as pd

COLS = ["duration","protocol_type","service","flag","src_bytes","dst_bytes","land","wrong_fragment","urgent",
 "hot","num_failed_logins","logged_in","num_compromised","root_shell","su_attempted","num_root","num_file_creations",
 "num_shells","num_access_files","num_outbound_cmds","is_host_login","is_guest_login","count","srv_count",
 "serror_rate","srv_serror_rate","rerror_rate","srv_rerror_rate","same_srv_rate","diff_srv_rate",
 "srv_diff_host_rate","dst_host_count","dst_host_srv_count","dst_host_same_srv_rate","dst_host_diff_srv_rate",
 "dst_host_same_src_port_rate","dst_host_srv_diff_host_rate","dst_host_serror_rate","dst_host_srv_serror_rate",
 "dst_host_rerror_rate","dst_host_srv_rerror_rate","label","difficulty"]
CAT = ["protocol_type", "service", "flag"]
CLASSES = ["Normal", "DoS", "Probe", "R2L", "U2R"]

DOS = {"back","land","neptune","pod","smurf","teardrop","apache2","udpstorm","processtable","mailbomb","worm"}
PROBE = {"satan","ipsweep","nmap","portsweep","mscan","saint"}
R2L = {"guess_passwd","ftp_write","imap","phf","multihop","warezmaster","warezclient","spy","xlock","xsnoop",
       "snmpguess","snmpgetattack","httptunnel","sendmail","named"}
U2R = {"buffer_overflow","loadmodule","rootkit","perl","sqlattack","xterm","ps"}

def to_class(label: str) -> str:
    if label == "normal": return "Normal"
    if label in DOS: return "DoS"
    if label in PROBE: return "Probe"
    if label in R2L: return "R2L"
    if label in U2R: return "U2R"
    raise ValueError(f"unknown attack label: {label}")

def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, header=None, names=COLS)
    df["attack_class"] = df["label"].map(to_class)
    return df
