import re
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import to_date, col, udf
from pyspark.sql.types import StringType, BooleanType
from sqlalchemy import create_engine, Column, Integer, String, Date, MetaData, Table
from sqlalchemy.dialects.postgresql import insert
import logging
from airflow.hooks.base import BaseHook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_data(csv_path, output_path="data/extracted"):
    try:
        logger.info(f"Starting extraction from {csv_path}")
        spark = SparkSession.builder.appName("ETL_Extract").getOrCreate()
        df = spark.read.csv(csv_path, header=True, inferSchema=True)
        df.write.parquet(output_path, mode="overwrite")
        spark.stop()
        logger.info(f"Extraction completed. Data saved to {output_path}")
    except Exception as e:
        logger.error(f"Error during extraction: {e}")
        raise


def transform_data(input_path="data/extracted", output_path="data/transformed"):
    try:
        logger.info(f"Starting transformation from {input_path}")
        spark = SparkSession.builder.appName("ETL_Transform").getOrCreate()
        df = spark.read.parquet(input_path)

        # Преобразование поля signup_date в формат YYYY-MM-DD
        df = df.withColumn(
            "signup_date", to_date(col("signup_date"), "yyyy-MM-dd HH:mm:ss")
        )

        # Фильтрация некорректных email
        email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        is_valid_email = udf(
            lambda email: re.match(email_regex, email) is not None, BooleanType()
        )
        df = df.filter(is_valid_email(col("email")))

        # Добавление столбца domain
        extract_domain = udf(
            lambda email: email.split("@")[1] if "@" in email else None, StringType()
        )
        df = df.withColumn("domain", extract_domain(col("email")))

        df.write.parquet(output_path, mode="overwrite")
        spark.stop()
        logger.info(f"Transformation completed. Data saved to {output_path}")
    except Exception as e:
        logger.error(f"Error during transformation: {e}")
        raise


def load_data(input_path="data/transformed", conn_id="postgres_conn"):
    """
    Загрузка данных в PostgreSQL с использованием SQLAlchemy и Airflow Connections.
    """
    try:
        # Получение строки подключения из Airflow Connection
        connection = BaseHook.get_connection(conn_id)
        db_url = f"postgresql://{connection.login}:{connection.password}@{connection.host}:{connection.port}/{connection.schema}"
        logger.info(f"Starting load from {input_path} to database {db_url}")

        spark = SparkSession.builder.appName("ETL_Load").getOrCreate()
        df = spark.read.parquet(input_path)

        # Конвертация в pandas DataFrame для загрузки
        pandas_df = df.toPandas()

        # Логирование размера DataFrame
        logger.info(f"DataFrame size: {pandas_df.shape}")

        # Создание SQLAlchemy engine
        engine = create_engine(db_url)
        metadata = MetaData()

        # Определение таблицы
        users_table = Table(
            "users",
            metadata,
            Column("user_id", Integer, primary_key=True),
            Column("name", String(255)),
            Column("email", String(255)),
            Column("signup_date", Date),
            Column("domain", String(255)),
        )

        # Создание таблицы, если не существует
        metadata.create_all(engine)
        logger.info("Table 'users' ensured in the database.")

        # Подготовка данных для вставки
        records = pandas_df.to_dict(orient="records")
        logger.info(f"Prepared {len(records)} records for insertion.")

        # Использование upsert для предотвращения дублирования
        stmt = insert(users_table).values(records)
        stmt = stmt.on_conflict_do_nothing(index_elements=["user_id"])

        # Выполнение вставки с использованием контекстного менеджера для транзакций
        with engine.connect() as connection:
            with connection.begin():
                connection.execute(stmt)

        logger.info("Data successfully loaded into the database.")
        spark.stop()
    except Exception as e:
        logger.error(f"Error during loading: {e}")
        raise
