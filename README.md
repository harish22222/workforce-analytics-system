# Weekly Workforce Analytics & Risk Assessment System

This project is a scalable, cloud-ready solution for managing workforce analytics, evaluating compliance, and forecasting pay estimates. Built using Django, Django REST Framework, AWS SQS, and various mock API integrations for an MSc Cloud Computing Module.

## Architecture

1. **Django REST Backend**: Manages Jobs in an SQLite database (adaptable to PostgreSQL) and handles asynchronous task generation.
2. **Django Templates System**: Serves responsive, stylized Vanilla CSS user interfaces matching premium design aesthetics.
3. **AWS SQS**: Asynchronous event queue. Jobs submitted via web are sent to SQS and picked up by a standalone background worker script to ensure the web server is non-blocking.
4. **Standalone Python Worker**: Daemon constantly polling AWS SQS to perform calculations and external API fetches.

## Integrations

- **Workforce Analytics Algorithm**: Local core calculator parsing total hours, classifying risk, and determining EU compliance thresholds (<48 hrs).
- **Public Holiday API**: Integrates with standard public APIs measuring holiday overlaps.
- **Classmate Pay Calculator API**: (Simulated via Serverless Lambdas). Secure integration handling POST requests via wrapper proxy with built-in timeouts.

## Local Setup

### 1. Prerequisites
- Python 3.9+ installed.
- Valid AWS Credentials (configured via environment variables or `~/.aws/credentials`).
- Access to an active AWS SQS Queue.

### 2. Installation Setup

1. Clone or navigate to the project root:
   ```bash
   cd workforce-analytics-system
   ```

2. Activate virtual environment and install requirements:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or `.\venv\Scripts\Activate.ps1` on Windows
   pip install -r requirements.txt
   ```

3. Configure Environment Variables:
   Copy the example and update with your real values (You MUST update `SQS_QUEUE_URL`).
   ```bash
   cp .env.example .env
   ```

### 3. Database Initialization

Run Django migrations to create the SQLite schemas:

```bash
cd backend
python manage.py makemigrations analytics
python manage.py migrate
```

### 4. Running the Project

Because this architecture relies on SQS decoupled asynchronous processing, you need to run TWO separate terminals.

**Terminal 1: Start the Web Server**
```bash
cd backend
python manage.py runserver
```
Navigate to `http://localhost:8000/` to view the **Weekly Input View**.

**Terminal 2: Start the Background SQS Worker Daemon**
```bash
cd backend
python worker.py
```
*Note: If AWS credentials are not configured or valid in your `.env`, the system automatically defaults to an in-memory database mock sequence so you can test functionality without a live SQS endpoint.*

## Running Tests

Automated testing using `unittest` and `mock` assertions to check algorithm integrity and REST integrations:

```bash
cd backend
python manage.py test analytics
```

## Cloud Deployment Readiness

The architecture supports a standard deployment onto an **AWS EC2** Instance:
1. `gunicorn core.wsgi:application` to serve Django application.
2. `nginx` configured with a reverse-proxy routing to gunicorn on port 80/443.
3. `systemd` supervisor file keeping `worker.py` alive and monitoring SQS.
4. Scale workers horizontally by booting new EC2 instances simply running `worker.py`.
