# Airflow Dockerfile for TechPulse VN
FROM apache/airflow:2.8.0-python3.10

USER root

# Install Docker CLI (for DockerOperator)
RUN apt-get update && \
    apt-get install -y docker.io && \
    rm -rf /var/lib/apt/lists/*

USER airflow

# Copy DAG files
COPY dags/ /opt/airflow/dags/

# Set environment variables
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__CORE__DAGBAG_IMPORT_TIMEOUT=300
ENV AIRFLOW__CORE__FERNET_KEY=46BKJoQYlPPOexq0OhDZnIl8epQ9uPFKL_e5GzQ1-5g=

# Initialize database on container start
COPY entrypoint.sh /entrypoint.sh
USER root
RUN chmod +x /entrypoint.sh
USER airflow

ENTRYPOINT ["/entrypoint.sh"]
