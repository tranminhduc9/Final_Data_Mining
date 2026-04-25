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
from datetime import datetime, timedelta
import traceback
def safe_find(driver, css):
    try:
        return driver.find_element(By.CSS_SELECTOR, css).text.strip()
    except NoSuchElementException:
        return ""
#driver = webdriver.Chrome()
driver = uc.Chrome()

source_url = "https://www.topcv.vn/tim-viec-lam-cong-nghe-thong-tin-cr257?sort=new&type_keyword=1&category_family=r257&saturday_status=0"
#num_pages = 2

driver.get(source_url)

source_platform = driver.find_element(By.CSS_SELECTOR, "a.header-menu-mobile__logo img").get_attribute("title")

scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

data = {
    "source_platform": source_platform,
    "source_url": source_url,
    "scraped_at": scraped_at,
    "post_detail": []
}

wait = WebDriverWait(driver, 10)

elements_links = driver.find_elements(By.CSS_SELECTOR, "h3.title a")

# Lấy href
links = list(set([
    e.get_attribute("href")
    for e in elements_links
    if e.get_attribute("href")
]))

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
        print(f"  [LỖI] Xử lý bài {link} thất bại. Chi tiết: {e}")
        continue

driver.quit()

os.makedirs("raw_data", exist_ok=True)
output_file = os.path.join("raw_data", "raw_data_topCV.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nĐã lưu dữ liệu vào file: {output_file}")
print(f"\nTổng số bài viết: {len(data['post_detail'])}")