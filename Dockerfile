# Extends the official Airflow image with the Python deps we need inside the
# scheduler/webserver containers: dbt-snowflake (so the dbt DAG can shell out
# to `dbt`) plus our ingestion deps.
FROM apache/airflow:2.8.4-python3.11

USER airflow

RUN pip install --no-cache-dir \
    "dbt-core==1.7.13" \
    "dbt-snowflake==1.7.3" \
    "snowflake-connector-python==3.7.1" \
    "requests==2.32.3" \
    "pandas==2.2.2" \
    "pyarrow==16.1.0" \
    "python-dotenv==1.0.1"
