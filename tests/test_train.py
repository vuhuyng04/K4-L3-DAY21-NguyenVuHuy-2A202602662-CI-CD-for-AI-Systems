import os
import json
import numpy as np
import pandas as pd
import pytest
from src.train import train


FEATURE_NAMES = [
    "age", "workclass", "education_num", "marital_status", "occupation",
    "relationship", "sex", "capital_gain", "capital_loss", "hours_per_week",
]

SMALL_PARAMS = {"n_estimators": 10, "learning_rate": 0.1, "max_depth": 2}


@pytest.fixture(autouse=True)
def _isolated_mlflow(tmp_path, monkeypatch):
    """Ghi MLflow vao thu muc tam de cac run test khong lan vao mlflow.db that."""
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{(tmp_path / 'mlflow.db').as_posix()}")


def _make_temp_data(tmp_path):
    """
    Tao dataset nho voi cung schema Adult de su dung trong test.

    pytest cung cap `tmp_path` la mot thu muc tam thoi, tu dong xoa sau khi test ket thuc.
    Ham nay dung du lieu ngau nhien nen khong can ket noi cloud storage hay tai file CSV thuc.
    """
    rng = np.random.default_rng(0)
    n = 200

    X = rng.random((n, len(FEATURE_NAMES)))
    # Bai toan nay chi co HAI lop (0 va 1), nen can tren la 2.
    y = rng.integers(0, 2, size=n)

    df = pd.DataFrame(X, columns=FEATURE_NAMES)
    df["target"] = y

    train_path = str(tmp_path / "train.csv")
    eval_path = str(tmp_path / "holdout.csv")
    df.iloc[:160].to_csv(train_path, index=False)
    df.iloc[160:].to_csv(eval_path, index=False)

    return train_path, eval_path


def test_train_returns_float(tmp_path):
    """Kiem tra ham train() tra ve mot so thuc nam trong [0.0, 1.0]."""
    train_path, eval_path = _make_temp_data(tmp_path)

    f1 = train(SMALL_PARAMS, data_path=train_path, eval_path=eval_path)

    assert isinstance(f1, float)
    assert 0.0 <= f1 <= 1.0


def test_report_file_created(tmp_path):
    """Kiem tra file outputs/report.json duoc tao sau khi huan luyen."""
    train_path, eval_path = _make_temp_data(tmp_path)
    train(SMALL_PARAMS, data_path=train_path, eval_path=eval_path)

    assert os.path.exists("outputs/report.json")
    with open("outputs/report.json") as f:
        report = json.load(f)
    assert "f1_score" in report
    assert "accuracy" in report
    # Cac truong bonus 2 va 5
    assert 0.1 <= report["best_threshold"] <= 0.9
    assert 0.0 <= report["train_positive_rate"] <= 1.0


def test_model_file_created(tmp_path):
    """Kiem tra file models/model.joblib duoc tao sau khi huan luyen."""
    train_path, eval_path = _make_temp_data(tmp_path)
    train(SMALL_PARAMS, data_path=train_path, eval_path=eval_path)

    assert os.path.exists("models/model.joblib")


def test_detail_file_created(tmp_path):
    """Bonus 3: kiem tra outputs/detail.txt chua confusion matrix va precision/recall."""
    train_path, eval_path = _make_temp_data(tmp_path)
    train(SMALL_PARAMS, data_path=train_path, eval_path=eval_path)

    with open("outputs/detail.txt", encoding="utf-8") as f:
        detail = f.read()
    assert "Confusion matrix" in detail
    assert "precision" in detail and "recall" in detail
