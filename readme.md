# Introduction


This is a tool for data processing in the DAT301m with the dataset:nguyendv02/ViMD_Dataset
# Audio & Transcript Editor

A Gradio application for editing audio and text transcripts stored in a Parquet file.
# Purpose of this repo 
As the Whisper model currently supports input audio with a maximum duration of 30 seconds, some audio samples in the ViMD dataset do not meet this requirement. To address this issue, this repository provides a tool to automatically identify and separate audio files exceeding the limit from the original dataset and store them in a separate location.

For users who wish to retain these longer audio samples, the included app.py application allows manual audio trimming and transcript editing to make them compatible with the model. However, this process requires user interaction to ensure proper segmentation and transcript adjustment.


## Features

### 📝 Text Editing

* View and edit transcripts
* Display metadata (region, province, speaker ID, gender)
* Restore original text
* Save text changes

### 🎵 Audio Editing

* Play both the current and original audio
* Trim audio using time ranges (milliseconds)
* Restore original audio
* Save audio changes

### 🔄 Navigation

* Move between samples
* Display the current sample index
* Mark edited samples

### 💾 Saving

* Save all changes to a new Parquet file
* Preserve the original file structure
* Automatically create a `data_edited` directory for edited files

## Installation

```bash
pip install -r requirements.txt
````

---

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

