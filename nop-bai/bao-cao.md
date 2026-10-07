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

**Lý do:** Lần 5 có f1_score cao nhất (0,7207), vượt ngưỡng 0,65. Lần có accuracy cao nhất là lần 1, không trùng với lần có f1 cao nhất: accuracy chỉ dao động 0,846–0,878 trong khi f1 chênh tới 0,115, nên accuracy không phân biệt được mô hình tốt trên lớp thiểu số. Về đánh đổi, giảm `learning_rate` xuống 0,05 phải tăng lên 200 cây (lần 4) mà vẫn kém lần 1.

---

## 2. Vì Sao Ngưỡng Chất Lượng Đặt Trên F1 Chứ Không Phải Accuracy

Chỉ 24,8% mẫu có thu nhập > 50K, nên mô hình luôn đoán "thu nhập thấp" vẫn đạt accuracy 0,752 dù không nhận ra người thu nhập cao nào. Lần chạy kiểm chứng của em (ảnh 07) cho đúng kết quả này: accuracy 0,752, f1 = 0, và Quality Gate đã chặn Release. F1 của lớp dương kết hợp precision và recall của chính lớp thu nhập cao, nên chỉ cao khi mô hình vừa tìm được nhiều người thu nhập cao vừa ít báo nhầm. Không dùng `average="weighted"`/`"macro"` vì lớp đa số kéo điểm lên: với mô hình đã chọn, weighted F1 là 0,87 còn F1 lớp dương chỉ 0,72.

---

## 3. Khó Khăn Gặp Phải và Cách Giải Quyết

| Khó khăn | Nguyên nhân | Cách giải quyết |
|---|---|---|
| `pip install` thất bại trên máy. | Python 3.14 không có wheel cho scikit-learn 1.4.2. | Dùng `uv` tạo `.venv` Python 3.10, khớp với CI. |
| `dvc push` và tạo EC2 bị `AccessDenied`. | IAM user hằng ngày thiếu quyền S3/EC2. | Viết hạ tầng bằng Terraform (`infra/`), apply bằng tài khoản quản trị; CI dùng user chỉ có quyền trên bucket. |
| Hướng dẫn viết cho GCP. | Em chọn AWS. | Dùng `dvc[s3]` + `boto3`; model mới vào `artifacts/candidate/`, chỉ promote sang `artifacts/current/` khi qua Quality Gate. |

---

## 4. So Sánh Bước 2 và Bước 3 (bắt buộc, 2 - 3 câu)

| | f1_score | accuracy |
|---|---|---|
| Bước 2 (chỉ `train_batch1`) | 0.7207 | 0.876 |
| Bước 3 (thêm `train_batch2`) | 0.7297 | 0.880 |

**Nhận xét:** Gấp đôi dữ liệu chỉ làm f1 tăng 0,009, tương đương khoảng một dự đoán đúng thêm trên holdout 500 mẫu. Hai nửa dữ liệu được chia ngẫu nhiên từ cùng một nguồn (tỷ lệ lớp dương đều 24,8%) nên dữ liệu mới gần như không mang thông tin mới. Điều Bước 3 chứng minh là quy trình: một commit file `.dvc` tự kích hoạt cả 4 job và VM tự phục vụ model mới.

---

## 5. Phần Bonus Đã Thực Hiện (nếu có)

- [ ] Bonus 1 - DagsHub: code đã đọc `MLFLOW_TRACKING_URI` từ secrets, chưa cấu hình tài khoản DagsHub.
- [x] Bonus 2 - Ngưỡng quyết định: ngưỡng 0,30 cho F1 0,7463 (ngưỡng 0,5: 0,7207), vì hạ ngưỡng giúp tăng recall lớp thu nhập cao.
- [x] Bonus 3 - Precision/recall: `outputs/detail.txt` (lớp cao: precision 0,82, recall 0,65); nếu dùng để xét hỗ trợ tài chính thì gán nhầm người thu nhập thấp thành cao tốn kém hơn vì họ mất quyền hỗ trợ.
- [x] Bonus 4 - Rollback guard: so f1 mới với `artifacts/current/report.json` (Bước 3: 0,7297 vs 0,7207), chỉ triển khai khi f1 mới >= f1 cũ.
- [x] Bonus 5 - Lệch lạc dữ liệu: cảnh báo khi tỷ lệ lớp dương lệch > 5 điểm % so với 24,8%, ghi `train_positive_rate` vào `report.json`.
