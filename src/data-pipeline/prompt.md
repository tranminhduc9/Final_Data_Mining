# Prompt: Cập nhật Data Pipeline cho TopCV

Hãy thực hiện các chỉnh sửa sau trong folder `data-pipeline` để cập nhật nguồn dữ liệu và API Key mới:

### 1. Cập nhật `scrape_from_topCV.py`
- Thay đổi `source_url` tại dòng 22 thành:
  `"https://www.topcv.vn/tim-viec-lam-moi-nhat?company_field=1&type_keyword=1&sba=1&saturday_status=0"`
- Đảm bảo script vẫn sử dụng `undetected_chromedriver` để tránh bị chặn.
- Kiểm tra xem các selector CSS như `h3.title a`, `h1.job-detail__info--title`, `div.company-name-label a` có còn hoạt động với URL mới không. Nếu cấu trúc trang thay đổi, hãy điều chỉnh selector tương ứng.

### 2. Cập nhật `filter_data.py`
- Cập nhật `API_KEY` (dòng 30) sử dụng key mới: `AIzaSyDUsgEvbMQaQfrGl59i4mArs1jJwTVfomM`.
- Khuyến khích sử dụng file `.env` bằng cách thêm/sửa dòng sau trong `.env`:
  `GEMINI_API_KEY=AIzaSyDUsgEvbMQaQfrGl59i4mArs1jJwTVfomM`

### 3. Quy cách đặt tên file lưu dữ liệu
- **Scrape**: Trong `scrape_from_topCV.py`, bên trong folder `raw_data/`, tạo 1 folder `topCV/` thay đổi tên file lưu `raw_data_topCV.json` thành:
  `YYYY_MM_DD.json` và lưu vào folder topCV/.
- **Clean/Filter/Extract**: Đảm bảo tất cả các file kết quả ở các bước sau đều tạo 1 folder `topCV` bên trong `cleaned_data`, `filtered_data`, `extracted_data` và đều giữ nguyên phần hậu tố `YYYY_MM_DD.json` từ file đầu vào:
  - `cleaned_data/topCV/YYYY_MM_DD.json`
  - `filtered_data/topCV/YYYY_MM_DD.json`
  - `extracted_data/topCV/YYYY_MM_DD.json`

### 4. Điều chỉnh các phần bổ sung
- **Clean Data**: Trong `clean_data.py`, đảm bảo hàm `normalize_datetime` xử lý được định dạng ngày tháng từ URL mới nếu có thay đổi.
- **Filter Keyword**: Cập nhật `WHITELIST` trong `filter_data.py` nếu cần thiết để phù hợp với các tin tuyển dụng mới nhất từ link "Việc làm mới nhất".
- **Error Handling**: Thêm logging trong `scrape_from_topCV.py` để ghi lại các link bài viết bị lỗi hoặc không crawl được nội dung chi tiết.

### 5. Quy trình chạy lại
Sau khi chỉnh sửa, hãy chạy pipeline theo thứ tự:
1. `python scrape_from_topCV.py`
2. `python clean_data.py`
3. `python filter_data.py`
4. `python extract_data_topCV.py`
