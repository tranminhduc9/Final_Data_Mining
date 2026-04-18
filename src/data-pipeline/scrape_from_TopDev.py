#Còn phần thẻ nội dung bài viết

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import time
import json
import os
from datetime import datetime

driver = webdriver.Chrome()

#source_url = "https://topdev.vn/blog/category/cong-nghe/"  # 100

source_url = "https://topdev.vn/blog/category/lap-trinh/"  # 100

driver.get(source_url)
time.sleep(3)  # Chờ trang load xong

source_platform = "TopDev-Việc làm IT hàng đầu Việt Nam"

scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Mục tiêu ~100 bài; dừng khi đạt ngưỡng đủ gần (không cần đúng 100)
ENOUGH = 100
max_scroll_rounds = 150

data = {
    "source_platform": source_platform,
    "source_url": source_url,
    "scraped_at": scraped_at,
    "post_detail": []
}

wait = WebDriverWait(driver, 10)

posts_info = []
seen_links = set()
processed_links = set()
def collect_articles():
    articles = driver.find_elements(By.CSS_SELECTOR, "div.td-animation-stack")
    for article in articles:
        if len(data["post_detail"]) >= ENOUGH:
            break
        try:
            title_els = article.find_elements(By.CSS_SELECTOR, "h3.td-module-title")

            link_els = article.find_elements(By.CSS_SELECTOR, "h3.td-module-title a")

            title = title_els[0].text if title_els else ""
            link = link_els[0].get_attribute("href") if link_els else ""

            if not link:
                continue
            if "eclick" in link:
                continue
            if link in seen_links:
                continue
            seen_links.add(link)
            posts_info.append({
                "title": title,
                "link": link
            })
        except StaleElementReferenceException:
            continue
    
    for idx, post in enumerate(posts_info):
        if post["link"] in processed_links:
            continue
        print(f"\nĐang xử lý bài {idx + 1}/{len(posts_info)}: {post['title'][:50]}...")
        
        driver.get(post['link'])
        
        try:
            article = driver.find_element(By.ID, "fck_detail_gallery")
            paragraphs = article.find_elements(By.CSS_SELECTOR, "p.Normal")
            content = "\n\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
        except NoSuchElementException:
            print(f"  ⚠ Không tìm thấy nội dung bài viết, bỏ qua.")
            continue

        # Thêm thông tin bài viết vào data
        post_detail = {
            "title": post['title'],
            "content": content,
        }
        data["post_detail"].append(post_detail)
        processed_links.add(post["link"])

prev_len = None
stuck = 0
for i in range(max_scroll_rounds):
    collect_articles()
    n = len(data["post_detail"])
    if n >= ENOUGH:
        print(f"Đã cào khoảng đủ mục tiêu (~100 bài, hiện {n}) sau {i + 1} lần cuộn.")
        break
    if prev_len is not None and n == prev_len:
        stuck += 1
        if stuck >= 3:
            print(f"Hết bài mới sau {i + 1} lần cuộn (hiện có {n} bài).")
            break
    else:
        stuck = 0
    prev_len = n
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
else:
    if len(data["post_detail"]) < ENOUGH:
        print(f"Đã hết {max_scroll_rounds} lần cuộn, thu được {len(data['post_detail'])} bài (chưa tới ~100).")

driver.quit()

os.makedirs("raw_data", exist_ok=True)
output_file = os.path.join("raw_data", "titles_TopDev2.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nĐã lưu dữ liệu vào file: {output_file}")
print(f"Tổng số tiêu đề: {len(data['post_detail'])}")
