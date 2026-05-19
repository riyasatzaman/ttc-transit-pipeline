"""Airflow DAG: hourly dbt build of the TTC analytics warehouse.

Layers are run sequentially in their own tasks so failures show up at the
layer they actually happen at — easier to debug from the Airflow UI than
a single monolithic `dbt build`.

Pipeline:
    dbt_run_staging  ->  dbt_run_intermediate  ->  dbt_run_marts  ->  dbt_test

Credentials: the docker-compose stack already passes SNOWFLAKE_* env vars
from the host .env into the scheduler container, and dbt_ttc/profiles.yml
reads them via env_var(). BashOperator inherits those vars from the parent
process, so no `dotenv run` wrapper is required inside the container.
"""
from __future__ import annotations

import pendulum
from airflow.decorators import dag
from airflow.operators.bash import BashOperator

DBT_PROJECT_DIR = "/opt/airflow/dbt_ttc"
# Prepended to every dbt command. Keeps the cd and DBT_PROFILES_DIR override
# in one place so individual tasks read cleanly.
DBT_BASE = (
    f"cd {DBT_PROJECT_DIR} && "
    f"DBT_PROFILES_DIR={DBT_PROJECT_DIR} "
)


@dag(
    dag_id="ttc_dbt_dag",
    description="Hourly dbt build of the TTC analytics warehouse.",
    schedule="0 * * * *",
    start_date=pendulum.datetime(2026, 5, 17, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "riyasat",
        "retries": 1,
        "retry_delay": pendulum.duration(minutes=5),
    },
    tags=["ttc", "dbt", "analytics"],
)
def ttc_dbt_dag():

    dbt_run_staging = BashOperator(
        task_id="dbt_run_staging",
        bash_command=f"{DBT_BASE}dbt run --select staging",
    )

    dbt_run_intermediate = BashOperator(
        task_id="dbt_run_intermediate",
        bash_command=f"{DBT_BASE}dbt run --select intermediate",
    )

    dbt_run_marts = BashOperator(
        task_id="dbt_run_marts",
        bash_command=f"{DBT_BASE}dbt run --select marts",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"{DBT_BASE}dbt test",
    )

    dbt_run_staging >> dbt_run_intermediate >> dbt_run_marts >> dbt_test


ttc_dbt_dag()
