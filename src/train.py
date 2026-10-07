import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import yaml
import json
import joblib
import os
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# Nguong chat luong cua lab nay la f1_score, KHONG phai accuracy.
# Ly do: bo du lieu Adult co ty le lop 75/25. Mot mo hinh doan bua
# "thu nhap thap" cho moi mau da dat accuracy 0.75 ma khong hoc duoc gi.
F1_THRESHOLD = 0.65

# Bonus 5: ty le lop duong tham chieu va do lech toi da cho phep (diem phan tram)
REFERENCE_POSITIVE_RATE = 0.248
DRIFT_TOLERANCE = 0.05


def check_drift(y_train: pd.Series) -> float:
    """Bonus 5: tinh ty le lop duong va canh bao neu lech qua 5 diem % so voi 24.8%."""
    positive_rate = float(y_train.mean())
    drift = positive_rate - REFERENCE_POSITIVE_RATE
    if abs(drift) > DRIFT_TOLERANCE:
        print(
            f"::warning::[DATA DRIFT] Ty le lop duong {positive_rate:.1%} lech "
            f"{drift * 100:+.1f} diem % so voi tham chieu {REFERENCE_POSITIVE_RATE:.1%}"
        )
    else:
        print(f"[DATA DRIFT] OK: ty le lop duong {positive_rate:.1%} (tham chieu {REFERENCE_POSITIVE_RATE:.1%})")
    return positive_rate


def tune_threshold(y_eval: pd.Series, proba: np.ndarray) -> tuple[float, float]:
    """Bonus 2: quet nguong quyet dinh 0.10 -> 0.90 (buoc 0.05), tra ve (nguong, f1) tot nhat."""
    best_threshold, best_f1 = 0.5, -1.0
    for threshold in np.round(np.arange(0.10, 0.90 + 1e-9, 0.05), 2):
        f1_at = f1_score(y_eval, (proba >= threshold).astype(int), zero_division=0)
        if f1_at > best_f1:
            best_threshold, best_f1 = float(threshold), float(f1_at)
    return best_threshold, best_f1


def write_detail(y_eval: pd.Series, preds: np.ndarray, path: str = "outputs/detail.txt") -> dict:
    """Bonus 3: confusion matrix va precision/recall tung lop, ghi ra file van ban."""
    tn, fp, fn, tp = confusion_matrix(y_eval, preds, labels=[0, 1]).ravel()
    per_class = {
        "precision_0": precision_score(y_eval, preds, pos_label=0, zero_division=0),
        "recall_0": recall_score(y_eval, preds, pos_label=0, zero_division=0),
        "precision_1": precision_score(y_eval, preds, pos_label=1, zero_division=0),
        "recall_1": recall_score(y_eval, preds, pos_label=1, zero_division=0),
    }
    lines = [
        "Confusion matrix (hang = thuc te, cot = du doan)",
        "                     pred_thap  pred_cao",
        f"thuc_te_thap (0)     {tn:>9}  {fp:>8}",
        f"thuc_te_cao  (1)     {fn:>9}  {tp:>8}",
        "",
        f"Lop 0 (thu_nhap_thap): precision={per_class['precision_0']:.4f}  recall={per_class['recall_0']:.4f}",
        f"Lop 1 (thu_nhap_cao) : precision={per_class['precision_1']:.4f}  recall={per_class['recall_1']:.4f}",
        "",
        classification_report(
            y_eval, preds, labels=[0, 1], target_names=["thu_nhap_thap", "thu_nhap_cao"], zero_division=0
        ),
    ]
    text = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return {k: float(v) for k, v in per_class.items()}


def train(
    params: dict,
    data_path: str = "data/train_batch1.csv",
    eval_path: str = "data/holdout.csv",
) -> float:
    """
    Huan luyen mo hinh va ghi nhan ket qua vao MLflow.

    Tham so:
        params     : dict chua cac sieu tham so cho GradientBoostingClassifier.
        data_path  : duong dan den file du lieu huan luyen.
        eval_path  : duong dan den file du lieu danh gia (holdout).

    Tra ve:
        f1 (float): diem F1 cua lop duong (thu nhap > 50K) tren tap holdout.
    """
    # Mac dinh ghi vao SQLite cuc bo; dat MLFLOW_TRACKING_URI de dung server tu xa (Bonus 1: DagsHub)
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI") or "sqlite:///mlflow.db")

    df_train = pd.read_csv(data_path)
    df_eval = pd.read_csv(eval_path)

    X_train = df_train.drop(columns=["target"])
    y_train = df_train["target"]
    X_eval = df_eval.drop(columns=["target"])
    y_eval = df_eval["target"]

    positive_rate = check_drift(y_train)

    with mlflow.start_run():
        mlflow.log_params(params)
        mlflow.log_param("train_rows", len(df_train))

        model = GradientBoostingClassifier(**params, random_state=42)
        model.fit(X_train, y_train)

        preds = model.predict(X_eval)
        f1 = float(f1_score(y_eval, preds))  # lop duong, KHONG dung average
        acc = float(accuracy_score(y_eval, preds))

        best_threshold, best_f1 = tune_threshold(y_eval, model.predict_proba(X_eval)[:, 1])

        os.makedirs("outputs", exist_ok=True)
        per_class = write_detail(y_eval, preds)

        mlflow.log_metric("f1_score", f1)
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("best_threshold", best_threshold)
        mlflow.log_metric("best_threshold_f1", best_f1)
        mlflow.log_metric("train_positive_rate", positive_rate)
        mlflow.log_metrics(per_class)
        mlflow.log_artifact("outputs/detail.txt")
        mlflow.sklearn.log_model(model, "model")

        print(f"F1: {f1:.4f} | Accuracy: {acc:.4f}")
        print(f"Nguong tot nhat: {best_threshold:.2f} -> F1 {best_f1:.4f} (nguong 0.50 -> F1 {f1:.4f})")

        report = {
            "f1_score": f1,
            "accuracy": acc,
            "best_threshold": best_threshold,
            "best_threshold_f1": best_f1,
            "train_positive_rate": positive_rate,
            "train_rows": len(df_train),
            **per_class,
        }
        with open("outputs/report.json", "w") as f:
            json.dump(report, f, indent=2)

        os.makedirs("models", exist_ok=True)
        joblib.dump(model, "models/model.joblib")

    return f1


if __name__ == "__main__":
    with open("params.yaml") as f:
        params = yaml.safe_load(f)
    train(params)
