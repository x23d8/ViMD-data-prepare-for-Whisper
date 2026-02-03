# 🎧 Audio & Transcript Editor cho ViMD Dataset

Công cụ dựa trên Gradio dùng để xử lý và chỉnh sửa dữ liệu **audio và transcript** được lưu dưới định dạng Parquet, phục vụ cho môn học **DAT301m**, sử dụng bộ dữ liệu **nguyendv02/ViMD_Dataset**.

Công cụ hỗ trợ chuẩn bị dữ liệu cho các mô hình nhận dạng giọng nói như **Whisper**, vốn chỉ hỗ trợ audio đầu vào có thời lượng tối đa **30 giây**.


## 📌 Tổng quan

Trong bộ dữ liệu ViMD, một số file audio có thời lượng vượt quá giới hạn 30 giây của Whisper. Repository này cung cấp:

1. Công cụ **tự động phát hiện và tách audio dài** khỏi bộ dữ liệu gốc.
2. Một giao diện chỉnh sửa cho phép **cắt audio và chỉnh sửa transcript thủ công**.
3. Quy trình chỉnh sửa **không làm thay đổi dữ liệu gốc**.

Mục tiêu là hỗ trợ chuẩn bị dữ liệu huấn luyện một cách thuận tiện, đồng thời vẫn cho phép người dùng chỉnh sửa khi cần thiết.


## 🎯 Tính năng chính

### 📝 Chỉnh sửa Transcript
- Xem và chỉnh sửa nội dung transcript
- Hiển thị metadata:
  - Region
  - Province
  - Speaker ID
  - Gender
- Khôi phục văn bản gốc
- Lưu thay đổi văn bản

### 🎵 Chỉnh sửa Audio
- Phát audio gốc và audio đã chỉnh sửa
- Cắt audio theo khoảng thời gian (milliseconds)
- Khôi phục audio ban đầu
- Lưu audio sau khi chỉnh sửa

### 🔄 Điều hướng dữ liệu
- Di chuyển giữa các mẫu dữ liệu
- Hiển thị chỉ số mẫu hiện tại
- Đánh dấu các mẫu đã chỉnh sửa

### 💾 Lưu dữ liệu
- Lưu tất cả thay đổi vào file Parquet mới
- Giữ nguyên dữ liệu gốc
- Tự động tạo thư mục lưu dữ liệu chỉnh sửa


## 📦 Cài đặt

Cài đặt các thư viện cần thiết:

```bash
pip install -r requirements.txt
````


## 🚀 Cách sử dụng

Khởi chạy ứng dụng:

```bash
python app.py
```

Sau khi chạy, giao diện sẽ mở tại:

```
http://localhost:7860
```

---

## 🧭 Quy trình sử dụng

### Bước 0 — Chuẩn bị dữ liệu

* Notebook `prepare.ipynb` chứa các bước tải và tiền xử lý dữ liệu.
* Các audio dài hơn 30 giây sẽ được tách ra.
* Dữ liệu sạch được lưu trong thư mục `data/`.
* Các audio dài được lưu trong `long_audio/`.
* Sau khi chỉnh sửa, dữ liệu được lưu trong `long_audio_edited/`.

### Bước 1 — Xem mẫu dữ liệu

Mẫu đầu tiên được tải tự động khi ứng dụng khởi động.

### Bước 2 — Di chuyển giữa các mẫu

Sử dụng:

* `⬅️ Previous Sample`
* `Next Sample ➡️`

để chuyển đổi giữa các mẫu dữ liệu.

### Bước 3 — Chỉnh sửa transcript

* Chỉnh sửa nội dung trực tiếp.
* Nhấn **Save Text** để lưu thay đổi.
* Nhấn **Restore Text** để quay về nội dung gốc.

### Bước 4 — Cắt audio

* Phát audio để xác định đoạn cần giữ.
* Điều chỉnh thời gian bắt đầu và kết thúc.
* Nhấn **Trim Audio** để cắt.
* Có thể khôi phục audio gốc nếu cần.

### Bước 5 — Lưu toàn bộ thay đổi

Nhấn **SAVE ALL CHANGES** khi hoàn tất chỉnh sửa.

---

## 🗂 Định dạng dữ liệu hỗ trợ

File Parquet cần chứa các cột:

| Cột           | Mô tả                         |
| ------------- | ----------------------------- |
| region        | Vùng miền                     |
| province_code | Mã tỉnh/thành                 |
| province_name | Tên tỉnh/thành                |
| filename      | Tên file gốc                  |
| text          | Transcript                    |
| speakerID     | ID người nói                  |
| gender        | 1 = Nam, 0 = Nữ               |
| audio         | Audio WAV lưu dưới dạng bytes |

---

## 📁 Cơ chế lưu dữ liệu

* File dữ liệu gốc **không bị thay đổi**.
* File chỉnh sửa được lưu trong thư mục `data_edited/`.
* File đầu ra có hậu tố `_edited.parquet`.

---

## ⚠ Lưu ý

* Audio phải ở định dạng WAV trong file Parquet.
* Việc chỉnh sửa thủ công giúp đảm bảo transcript khớp với nội dung audio.
* Công cụ được thiết kế cho mục đích tiền xử lý dữ liệu.

---

## 📚 Mục đích sử dụng

* Chuẩn bị dữ liệu cho Whisper
* Làm sạch dữ liệu giọng nói
* Hiệu chỉnh transcript
* Cắt và chuẩn hóa audio

