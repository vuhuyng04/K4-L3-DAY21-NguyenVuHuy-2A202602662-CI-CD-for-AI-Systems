# Báo Cáo Lab Day 21 - CI/CD cho AI Systems

| | |
|---|---|
| Họ và tên | ___ |
| MSSV | ___ |
| Lớp / Khóa | K4 |
| Repo GitHub | https://github.com/vuhuyng04/K4-L3L4-Track2-Day21-CI-CD-for-AI-Systems |
| Ngày nộp | ___ |

---

## 1. Bộ Siêu Tham Số Đã Chọn và Lý Do

| Lần chạy | n_estimators | learning_rate | max_depth | f1_score | accuracy |
|---|---|---|---|---|---|
| 1 | 100 | 0.1 | 3 | 0.7109 | **0.8780** |
| 2 | 50 | 0.05 | 2 | 0.6051 | 0.8460 |
| 3 | 200 | 0.1 | 5 | 0.7149 | 0.8740 |
| 4 | 200 | 0.05 | 3 | 0.7014 | 0.8740 |
| 5 | 100 | 0.2 | 5 | **0.7207** | 0.8760 |

**Bộ siêu tham số đã chọn:** `n_estimators=100`, `learning_rate=0.2`, `max_depth=5`.

**Lý do:** Lần chạy 5 có f1_score cao nhất (0,7207) và vượt ngưỡng 0,65. Lần có accuracy cao nhất lại là lần 1 (0,878), nhưng f1 của nó thấp hơn: accuracy chỉ dao động trong khoảng 0,846–0,878, còn f1 chênh tới 0,115, nên accuracy không phân biệt được mô hình tốt và mô hình kém trên lớp thiểu số. Lần 2 vẫn đạt accuracy 0,846 nhưng f1 chỉ 0,605, dưới ngưỡng. Về đánh đổi, giảm `learning_rate` từ 0,1 xuống 0,05 phải tăng `n_estimators` lên 200 (lần 4) mà vẫn chưa bằng lần 1; cây sâu hơn (`max_depth=5`) cùng `learning_rate` lớn hơn hội tụ nhanh nhất với 100 cây.

---

## 2. Vì Sao Ngưỡng Chất Lượng Đặt Trên F1 Chứ Không Phải Accuracy

Chỉ 24,8% mẫu thuộc lớp thu nhập > 50K, nên một mô hình luôn trả lời "thu nhập thấp" đã đạt accuracy 0,752 dù không nhận ra được người thu nhập cao nào (f1 = 0). Accuracy bị lớp đa số chi phối nên con số cao dễ gây hiểu nhầm là mô hình tốt. F1 của lớp dương là trung bình điều hòa giữa precision và recall của chính lớp thu nhập cao, vì vậy nó chỉ cao khi mô hình vừa tìm được phần lớn người thu nhập cao vừa ít báo nhầm. Không dùng `average="weighted"` hay `"macro"` vì lớp đa số sẽ kéo điểm lên: với mô hình đã chọn, weighted F1 là 0,87 trong khi F1 lớp dương chỉ 0,72, và ngưỡng 0,65 sẽ mất tác dụng chặn mô hình kém.

---

## 3. Khó Khăn Gặp Phải và Cách Giải Quyết

| Khó khăn | Nguyên nhân | Cách giải quyết |
|---|---|---|
| `pip install` thất bại trên máy cá nhân. | Python mặc định là 3.14, không có wheel cho scikit-learn 1.4.2 và pandas 2.2.2. | Dùng `uv` cài Python 3.10 và tạo `.venv`, khớp với phiên bản trong CI. |
| `import mlflow` báo thiếu `pkg_resources`. | Môi trường mới không có setuptools mà mlflow 2.13 cần. | Thêm `setuptools<81` vào `requirements.txt`. |
| Hướng dẫn viết cho GCP nhưng em dùng AWS. | Lab cho chọn provider. | Đổi sang `dvc[s3]` + `boto3`, hạ tầng (S3, IAM, EC2) viết bằng Terraform trong `infra/`. |

---

## 4. So Sánh Bước 2 và Bước 3 (bắt buộc, 2 - 3 câu)

| | f1_score | accuracy |
|---|---|---|
| Bước 2 (chỉ `train_batch1`) | ___ | ___ |
| Bước 3 (thêm `train_batch2`) | ___ | ___ |

**Nhận xét:** ___

---

## 5. Phần Bonus Đã Thực Hiện (nếu có)

- [ ] Bonus 1 - Tracking MLflow từ xa với DagsHub: `train.py` và `cicd.yml` đã đọc `MLFLOW_TRACKING_URI` từ secrets, chưa cấu hình tài khoản DagsHub.
- [x] Bonus 2 - Điều chỉnh ngưỡng quyết định: ngưỡng tốt nhất 0,30 cho F1 0,7463, cao hơn F1 0,7207 tại ngưỡng 0,5, vì hạ ngưỡng giúp bắt thêm người thu nhập cao (recall đang thấp).
- [x] Bonus 3 - Báo cáo precision / recall tự động: `outputs/detail.txt` (lớp cao: precision 0,82, recall 0,65); nếu dùng để xét hỗ trợ tài chính thì gán nhầm người thu nhập thấp thành cao (precision thấp) tốn kém hơn vì họ bị loại khỏi diện hỗ trợ.
- [x] Bonus 4 - Hoàn trả về phiên bản trước: Quality Gate so f1 mới với `artifacts/current/report.json`, chỉ promote model từ `artifacts/candidate/` khi f1 mới >= f1 cũ.
- [x] Bonus 5 - Cảnh báo lệch lạc dữ liệu: `train.py` in `::warning::` khi tỷ lệ lớp dương lệch quá 5 điểm % so với 24,8% và ghi `train_positive_rate` vào `report.json`.
