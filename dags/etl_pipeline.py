import logging
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from datetime import datetime
import os
import sys


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

project_path = '/opt/airflow/'
dags_path = os.path.join(project_path, 'dags')
sql_path = os.path.join(project_path, 'sql_queries')
sys.path.insert(0, dags_path)

from etl_functions import extract_data, transform_data, load_data

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 1, 24),
    'retries': 1,
}

with DAG('etl_pipeline',
         default_args=default_args,
         schedule_interval=None,
         catchup=False,
         template_searchpath=[dags_path]) as dag: 

    extract = PythonOperator(
        task_id='extract',
        python_callable=extract_data,
        op_kwargs={'csv_path': '/opt/airflow/data/users.csv'}
    )

    transform = PythonOperator(
        task_id='transform',
        python_callable=transform_data,
        op_kwargs={
            'input_path': '/opt/airflow/data/extracted',
            'output_path': '/opt/airflow/data/transformed'
        }
    )

    load = PythonOperator(
        task_id='load',
        python_callable=load_data,
        op_kwargs={
            'input_path': '/opt/airflow/data/transformed',
            'conn_id': 'postgres_conn' 
        }
    )

    # SQL Queries Tasks

    query1 = SQLExecuteQueryOperator(
        task_id='query1_count_users_per_day',
        conn_id='postgres_conn', 
        sql='query1_count_users_per_day.sql', 
    )

    query2 = SQLExecuteQueryOperator(
        task_id='query2_unique_email_domains',
        conn_id='postgres_conn',
        sql='query2_unique_email_domains.sql', 
    )

    query3 = SQLExecuteQueryOperator(
        task_id='query3_recent_signups',
        conn_id='postgres_conn', 
        sql='query3_recent_signups.sql', 
    )

    query4 = SQLExecuteQueryOperator(
        task_id='query4_users_with_most_common_domain',
        conn_id='postgres_conn', 
        sql='query4_users_with_most_common_domain.sql',
    )

    query5 = SQLExecuteQueryOperator(
        task_id='query5_delete_unwanted_domains',
        conn_id='postgres_conn', 
        sql='query5_delete_unwanted_domains.sql', 
    )

    # Установка зависимостей между задачами
    extract >> transform >> load >> [query1, query2, query3, query4, query5]
