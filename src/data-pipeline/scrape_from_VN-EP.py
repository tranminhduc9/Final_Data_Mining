from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import json
from datetime import datetime

driver = webdriver.Chrome()

# Gán link tìm kiếm
source_url = "https://vnexpress.net/khoa-hoc-cong-nghe"
num_pages = 2  # Số trang muốn cào

driver.get(source_url)

# Lấy tên nền tảng nguồn tin
source_platform = driver.find_element(By.CSS_SELECTOR, "a.logo").get_attribute("title")
# Lấy thời gian hiện tại
scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Khởi tạo cấu trúc dữ liệu
data = {
    "source_platform": source_platform,
    "source_url": source_url,
    "scraped_at": scraped_at,
    "post_detail": []
}

wait = WebDriverWait(driver, 10)

# Duyệt qua từng trang
posts_info = []
seen_links = set()  # Tránh trùng bài khi cùng bài xuất hiện nhiều trang
for page in range(1, num_pages + 1):
    print(f"{'='*40}\n")
    print(f"Đang cào trang {page}")
    
    base_url = source_url.rstrip("/")
    if '-p' in base_url:
        base_url = base_url.rsplit("-p", 1)[0]
    page_url = base_url if page == 1 else f"{base_url}-p{page}"
    driver.get(page_url)
    
    time.sleep(2)
    
    articles = driver.find_elements(By.CSS_SELECTOR, "article.item-news.item-news-common.thumb-left:not(.hidden)")

    added_this_page = 0 # Số bài đã thêm
    not_found_link = 0 # Số bài không tìm thấy link
    # Duyệt qua từng article để lấy thông tin tiêu đề, mô tả và link
    for article in articles:
        # Lấy tiêu đề (thử cả h3 và h4)
        title_els = article.find_elements(By.CSS_SELECTOR, 'h3.title-news, h4.title-news')

        # Lấy mô tả
        description_els = article.find_elements(By.CSS_SELECTOR, 'p.description')

        # Lấy link từ tiêu đề (thử cả h3 và h4)
        link_els = article.find_elements(By.CSS_SELECTOR, 'h3.title-news a, h4.title-news a')

        # Kiểm tra và lấy thông tin tiêu đề, mô tả và link
        title = title_els[0].text if title_els else ""
        description = description_els[0].text if description_els else ""
        link = link_els[0].get_attribute("href") if link_els else ""
        
        if not link: # Nếu không có link thì bỏ qua
            not_found_link += 1 
            continue 
        if "eclick" in link: # Nếu link là quảng cáo thì bỏ qua
            continue 
        if link in seen_links: # Nếu link đã được xử lý thì bỏ qua
            continue
        seen_links.add(link) # Thêm link vào set để tránh trùng bài
        posts_info.append({ # Thêm thông tin bài viết vào list
            "title": title,
            "description": description,
            "link": link
        })
        added_this_page += 1 # Tăng số bài đã thêm
    
    print(f"  Tìm thấy {len(articles)} phần tử, thêm {added_this_page} bài (bỏ qua {not_found_link} bài không tìm thấy link)") 

print(f"\nTổng cộng {len(posts_info)} bài viết từ {num_pages} trang")

#Duyệt qua từng bài viết để lấy chi tiết
for idx, post in enumerate(posts_info):
    print(f"\nĐang xử lý bài {idx + 1}/{len(posts_info)}: {post['title'][:50]}...")
    
    driver.get(post['link'])
    
    # Lấy ngày đăng bài viết
    date_elements = driver.find_elements(By.CSS_SELECTOR, "span.date")
    created_at = date_elements[0].text if date_elements else ""
    
    # Thêm thông tin bài viết vào data
    post_detail = {
        "title": post['title'],
        "description": post['description'],
        "created_at": created_at,    
    }
    
    data["post_detail"].append(post_detail)
    
driver.quit()

# Lưu dữ liệu vào file JSON
output_file = "raw_data_VN-EP.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nĐã lưu dữ liệu vào file: {output_file}")
print(f"\nTổng số bài viết: {len(data['post_detail'])}")
