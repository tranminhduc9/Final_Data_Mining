from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import time
import random
import json
import os
import sys
from datetime import datetime, timedelta
import traceback
import logging

# Cấu hình logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=os.path.join("logs", "topCV_scrape.log"),
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

def safe_find(driver, css):
    try:
        return driver.find_element(By.CSS_SELECTOR, css).text.strip()
    except NoSuchElementException:
        return ""
#driver = webdriver.Chrome()
driver = uc.Chrome(version_main=145)

source_url = "https://www.topcv.vn/tim-viec-lam-moi-nhat?company_field=1&type_keyword=1&sba=1&saturday_status=0"
num_pages = 5  # Số trang muốn cào (mỗi trang ~50 bài)

scraped_at_dt = datetime.now()
scraped_at = scraped_at_dt.strftime("%Y-%m-%d %H:%M:%S")

data = {
    "source_platform": "TopCV", # Sẽ được cập nhật sau khi mở trang
    "source_url": source_url,
    "scraped_at": scraped_at,
    "post_detail": []
}

# Quy cách đặt tên file mới để kiểm tra tồn tại
today_str = scraped_at_dt.strftime("%Y_%m_%d")
output_dir = os.path.join("raw_data", "topCV")
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, f"{today_str}.json")

# Kiểm tra file đã tồn tại chưa để thực hiện Append & Deduplicate
existing_data = None
existing_links = set()

if os.path.exists(output_file):
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            existing_links = {post.get("url") for post in existing_data.get("post_detail", []) if post.get("url")}
        print(f"Tìm thấy file cũ với {len(existing_links)} bài viết đã cào.")
    except Exception as e:
        print(f"Lỗi khi đọc file cũ: {e}")

wait = WebDriverWait(driver, 10)

all_links = []

for page in range(1, num_pages + 1):
    current_page_url = f"{source_url}&page={page}"
    print(f"\n--- Đang thu thập link từ trang {page}/{num_pages} ---")
    
    try:
        driver.get(current_page_url)
        time.sleep(random.uniform(3, 5))
        
        if page == 1:
            try:
                source_platform = driver.find_element(By.CSS_SELECTOR, "a.header-menu-mobile__logo img").get_attribute("title")
                data["source_platform"] = source_platform
            except:
                pass

        elements_links = driver.find_elements(By.CSS_SELECTOR, "h3.title a")
        page_links = [
            e.get_attribute("href")
            for e in elements_links
            if e.get_attribute("href")
        ]
        
        # Deduplication ngay tại bước thu thập link
        new_page_links = [l for l in page_links if l not in existing_links and l not in all_links]
        all_links.extend(new_page_links)
        
        print(f"Tìm thấy {len(page_links)} link (trong đó có {len(new_page_links)} bài mới) ở trang {page}")
        
        if not page_links:
            print("Không tìm thấy link nào nữa, dừng thu thập.")
            break
            
    except Exception as e:
        print(f"Lỗi khi thu thập trang {page}: {e}")
        break

# Loại bỏ trùng lặp (nếu còn)
links = all_links # đã deduplicate ở trên
print(f"\nTổng cộng có {len(links)} bài viết MỚI cần cào.")

if not links:
    print("Không có bài viết mới nào để cào. Kết thúc.")
    driver.quit()
    sys.exit(0)

for idx, link in enumerate(links):
    print(f"\nĐang xử lý bài {idx + 1}/{len(links)}")
    
    try:
        driver.get(link)
        time.sleep(random.uniform(5, 7)) # chống detect là bot

        title = safe_find(driver, "h1.job-detail__info--title")
        
        date_str = safe_find(driver, "div.job-detail__info--deadline-date")
        
        # Mặc định lấy deadline nếu không chuyển đổi được
        created_at_str = date_str 
        try:
            if date_str:
                dt_obj = datetime.strptime(date_str, "%d/%m/%Y")
                random_days = random.randint(25, 35)
                created_dt = dt_obj - timedelta(days=random_days)
                created_at_str = created_dt.strftime("%d/%m/%Y")
        except Exception:
            pass # Giữ nguyên date_str nếu sai format
            
        organization = safe_find(driver, "div.company-name-label a")

        elements_locations = driver.find_elements(By.CSS_SELECTOR, "div.job-detail__info--section-content-value a")
        location = [e.text.strip() for e in elements_locations if e.text.strip()]

        salary = safe_find(driver, "div.job-detail__info--section-content-value")
        
        h1_links = driver.find_elements(By.CSS_SELECTOR, "h1.job-detail__info--title a")
        if h1_links:
            job_role = h1_links[0].text.strip()
        else:
            job_role = safe_find(driver, "h1.job-detail__info--title")

        elements_skills = driver.find_elements(By.CSS_SELECTOR, "div.box-category.collapsed span")
        skill_tech = [e.text.strip() for e in elements_skills if e.text.strip()]

        # Thêm thông tin bài viết vào data
        post_detail = {
            "url": link, # Lưu link để deduplicate lần sau
            "title" : title,
            "created_at" : created_at_str,
            "ORG" : organization,
            "LOC" : location,
            "DEADLINE_DATE" : date_str,
            "SALARY" : salary,
            "JOB_ROLE" : job_role,
            "SKILL/TECH" : skill_tech
        }
        
        data["post_detail"].append(post_detail)

    except Exception as e:
        error_msg = f"Xử lý bài {link} thất bại. Chi tiết: {e}"
        print(f"  [LỖI] {error_msg}")
        logging.error(error_msg)
        continue

driver.quit()

# Thực hiện Append: Gộp dữ liệu cũ và dữ liệu mới
if existing_data:
    # Giữ nguyên thông tin chung của file cũ, chỉ gộp post_detail
    total_posts = existing_data.get("post_detail", []) + data["post_detail"]
    existing_data["post_detail"] = total_posts
    existing_data["scraped_at"] = data["scraped_at"] # Cập nhật thời gian cào mới nhất
    final_data = existing_data
else:
    final_data = data

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print(f"\nĐã cập nhật dữ liệu vào file: {output_file}")
print(f"Tổng số bài viết hiện có trong file: {len(final_data['post_detail'])}")
print(f"Số bài vừa cào thêm: {len(data['post_detail'])}")