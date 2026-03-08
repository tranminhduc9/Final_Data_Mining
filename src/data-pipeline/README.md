Hướng dẫn sử dụng

0. Cài đặt thư viện trong requirements.txt

1. Chạy terminal: python scrape_from_VN-EP.py
--> Tạo file raw_data_VN-EP.json

2. Chạy terminal: python clean_data_nlp.py raw_data_VN-EP.json
--> Tạo file cleaned_data_VN-EP.json

3. Chạy terminal: python filter_data.py cleaned_data_VN-EP.json
--> Tạo file filtered_data_VN-EP.json

4. Chạy terminal: python ner_articles.py filtered_data_VN-EP.json
--> Tạo file ner_data_VN-EP.json
