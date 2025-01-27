# Local Installation Guide for Apache Airflow with PostgreSQL

This guide provides a concise step-by-step process to install and set up Apache Airflow with PostgreSQL on your local machine without using Docker.

## Prerequisites

- **Operating System:** Linux (Ubuntu/Debian) or macOS
- **Python:** Version 3.11.x
- **PostgreSQL:** Version 13 or higher
- **Tools:** `pip`, `virtualenv`

---

## 1. Install Python 3.11

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
python3.11 --version
```

### macOS (Using Homebrew)

```bash
brew install python@3.11
brew link --overwrite python@3.11
python3.11 --version
```

---

## 2. Set Up Virtual Environment

```bash
mkdir ~/airflow_project
cd ~/airflow_project
python3.11 -m venv venv
source venv/bin/activate
```

---

## 3. Install PostgreSQL

### Ubuntu/Debian

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### macOS (Using Homebrew)

```bash
brew install postgresql@13
brew services start postgresql@13
```

---

## 4. Configure PostgreSQL

1. **Switch to PostgreSQL User:**

    ```bash
    sudo -i -u postgres
    ```

2. **Create User and Database:**

    ```bash
    psql
    ```

    ```sql
    CREATE USER etl_user WITH PASSWORD '1234';
    CREATE DATABASE etl_db OWNER etl_user;
    GRANT ALL PRIVILEGES ON DATABASE etl_db TO etl_user;
    \q
    exit
    ```

---

## 5. Install Apache Airflow

### Set Environment Variables

Create a `.env` file in your project directory:

```bash
touch .env
```

Add the following to `.env`:

```env
AIRFLOW_HOME=~/airflow_project/airflow
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://etl_user:1234@localhost:5432/etl_db
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__FERNET_KEY=your_generated_fernet_key_here
AIRFLOW__CORE__LOAD_EXAMPLES=False
```

### Generate `FERNET_KEY`

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the generated key and replace `your_generated_fernet_key_here` in the `.env` file.

### Install Airflow

```bash
export AIRFLOW_VERSION=2.10.4
export PYTHON_VERSION=3.11
export CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
```

### Install Additional Dependencies

Create a `requirements.txt` file if needed:

```txt
psycopg2-binary
pandas
sqlalchemy
# Add other dependencies here
```

Install them:

```bash
pip install -r requirements.txt
```

---

## 6. Initialize Airflow Database

```bash
airflow db init
```

---

## 7. Create Airflow User

```bash
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin_password
```

---

## 8. Launch Airflow Services

### Start Scheduler

Open a new terminal, activate the virtual environment, and run:

```bash
source ~/airflow_project/venv/bin/activate
airflow scheduler
```

### Start Webserver

In another terminal, activate the virtual environment, and run:

```bash
source ~/airflow_project/venv/bin/activate
airflow webserver --port 8080
```

---

## 9. Access Airflow Web Interface

1. Open your web browser.
2. Navigate to [http://localhost:8080](http://localhost:8080).
3. Log in with:
    - **Username:** `admin`
    - **Password:** `admin_password`

---

## 10. Troubleshooting

- **Web Interface Not Accessible:**
  - Ensure both Scheduler and Webserver are running.
  - Check firewall settings blocking port `8080`.
  - Verify Airflow logs for errors:
    ```bash
    tail -f ~/airflow_project/airflow/logs/webserver/latest/airflow-webserver.log
    ```

- **Database Connection Issues:**
  - Confirm PostgreSQL is running.
  - Verify connection string in `.env`.
  - Test connection using `psql`:
    ```bash
    psql postgresql://etl_user:1234@localhost:5432/etl_db -c "\l"
    ```

- **DAGs Not Showing or Broken:**
  - Check DAG file syntax.
  - Review Airflow logs for DAG-related errors.
    ```bash
    tail -f ~/airflow_project/airflow/logs/scheduler/latest/airflow-scheduler.log
    ```

---