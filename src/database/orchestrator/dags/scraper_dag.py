"""
Airflow DAG - TechPulse VN Scraper Pipeline
Schedule: 22:00 Việt Nam (15:00 UTC) hàng ngày
Timeout: 2 giờ cho toàn bộ pipeline
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.utils.dates import days_ago


default_args = {
    "owner": "techpulse",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    # Timeout cho mỗi task: 2 giờ
    "execution_timeout": timedelta(hours=2),
}

dag = DAG(
    dag_id="techpulse_daily_pipeline",
    default_args=default_args,
    description="Daily scraping pipeline for TechPulse VN - 22:00 VN time, 2h timeout",
    # 22:00 Việt Nam = 15:00 UTC (GMT+7)
    schedule_interval="0 15 * * *",
    start_date=days_ago(1),
    catchup=False,
    # Timeout cho toàn bộ DAG: 2.5 giờ (để có buffer)
    dagrun_timeout=timedelta(hours=2, minutes=30),
    tags=["techpulse", "scraper", "daily"],
    max_active_runs=1,  # Chỉ chạy 1 instance tại một thời điểm
)

# Task 1: Crawl VNExpress với timeout 2h
scrape_vnexpress = BashOperator(
    task_id="scrape_vnexpress",
    bash_command=(
        "timeout 2h docker exec crawler-vnexpress python /app/VNExpress.py || true"
    ),
    dag=dag,
)

# Task 2: Crawl GenK với timeout 2h
scrape_genk = BashOperator(
    task_id="scrape_genk",
    bash_command=(
        "timeout 2h docker exec crawler-genk python /app/GenK.py || true"
    ),
    dag=dag,
)

# Task 3: Crawl Dân Trí với timeout 2h
scrape_dantri = BashOperator(
    task_id="scrape_dantri",
    bash_command=(
        "timeout 2h docker exec crawler-dantri python /app/DanTri.py || true"
    ),
    dag=dag,
)

# Task 4: Trigger processing pipeline (sau khi crawl xong)
run_processing = BashOperator(
    task_id="run_processing_pipeline",
    bash_command=(
        "docker exec orchestrator /app/orchestrator || true"
    ),
    dag=dag,
)

# Flow: Crawl tất cả nguồn song song, sau đó chạy processing
[scrape_vnexpress, scrape_genk, scrape_dantri] >> run_processing