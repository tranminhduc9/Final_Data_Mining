Hướng dẫn sử dụng

0. Cài đặt thư viện trong requirements.txt
Trong filter_data và extract_data, dán API Key vào YOUR_API_KEY_HERE

1. Chạy scrape_from_DT.py và scrape_from_VN-EP.py
--> cào data từ các website

2. Chạy clean_data.py (làm sạch toàn bộ) 
hoặc chạy terminal: python clean_data.py raw_data_DT.json (làm sạch cố định)
--> chuẩn hoá format, xoá icon, kí tự,...

3. Chạy filter_data.py (lọc toàn bộ) 
hoặc chạy terminal: python filter_data.py raw_data_DT.json (lọc cố định)
--> lọc những bài liên quan đến IT --> dán nhãn true

4. Chạy extract_data.py (toàn bộ) 
hoặc chạy terminal: python extract_data.py raw_data_DT.json (cố định)
--> chọn những bài nhãn true --> chuyển title + description từ text sang NER
