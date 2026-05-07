<div align="center">

# VinTelligence
### Revenue & COGS Forecasting System — Datathon 2026

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.x-FF6600?style=for-the-badge&logoColor=white)](https://xgboost.readthedocs.io)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

*Hệ thống dự đoán doanh thu và COGS theo ngày sử dụng Machine Learning,*
*được containerize hoàn toàn với Docker và lưu trữ lịch sử dự đoán bằng MySQL.*

**Team: MANCHESTER_UNITED** · **Dang Van Tam** · Datathon 2026

</div>

---

## Table of Contents

- [Overview](#overview)
- [Technical Report](#technical-report)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Requirements](#requirements)
- [Installation & Usage](#installation--usage)
- [API Reference](#api-reference)
- [Model Performance](#model-performance)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [License](#license)

---

## Overview

**VinTelligence** is a daily Revenue and Cost of Goods Sold (COGS) forecasting system, developed as part of the **Datathon 2026** competition. The system applies state-of-the-art Machine Learning models — XGBoost and Random Forest — trained on real-world data encompassing sales transactions, web traffic, promotional campaigns, and order management records.

The system is designed as a production-ready, fully containerized service, exposing a REST API for integration and persisting every inference to a relational database for auditability and retrospective analysis.

### Objectives

- Forecast daily revenue with high accuracy (R² > 0.99) using temporal and behavioral features
- Expose a standards-compliant REST API suitable for integration into enterprise systems
- Persist all prediction records to MySQL for historical tracking and analysis

---

## Technical Report

The full analytical report for this project — covering data preprocessing, feature engineering, model selection, cross-validation methodology, and result interpretation — has been authored in compliance with the **NeurIPS 2025 (Conference on Neural Information Processing Systems)** paper format.

The report follows the official NeurIPS 2025 LaTeX template, adhering to its formatting guidelines for structure, typography, citation style, and figure/table presentation. It is available at:

```
reports/figures/datathon_2026_report.tex
```

---

## System Architecture

```
+-----------------------------------------------------------+
|                     Docker Environment                    |
|                                                           |
|   +------------------+        +----------------------+   |
|   |   Flask App       |        |     MySQL 8.0        |   |
|   |   (Port 5000)     |<------>|     (Port 3306)      |   |
|   |                   |        |   vintelligence DB   |   |
|   |   XGBoost         |        +----------------------+   |
|   |   Random Forest   |                                   |
|   +------------------+                                    |
+-----------------------------------------------------------+
         |
         v
   Web Browser / API Client
   http://localhost:5000
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Dual Model Support** | XGBoost and Random Forest models, selectable at inference time |
| **47-Feature Pipeline** | Full processing of lag features, rolling statistics, and temporal encodings |
| **Prediction History** | Every inference is persisted to MySQL and queryable via `/api/history` |
| **Docker Ready** | Fully containerized stack via Docker Compose |
| **REST API** | JSON-compliant API, compatible with any frontend or downstream service |
| **Smart Imputation** | Missing features are automatically filled with training-set medians |

---

## Requirements

### Running with Docker (Recommended)

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) >= 24.x

### Running Locally (Development)

- Python >= 3.11
- MySQL >= 8.0
- pip

---

## Installation & Usage

### Option 1 — Docker Compose (Full Stack)

Start the entire system (Flask + MySQL) with a single command:

```bash
# Clone the repository
git clone <repo-url>
cd Datathon_VinTelligence

# Configure environment variables
cp .env.example .env   # or edit .env directly

# Build and start
docker compose up --build -d

# Verify status
docker compose ps
docker compose logs app --tail 20
```

> The application will automatically wait for MySQL to be ready before starting (healthcheck configured).

### Option 2 — Docker (with local MySQL)

```bash
# Build the image
docker build -t vintelligence .

# Run the container, pointing to the host MySQL instance
docker run -d \
  --name vintel_app \
  -p 5000:5000 \
  -e MYSQL_HOST=host.docker.internal \
  -e MYSQL_USER=root \
  -e MYSQL_PASSWORD=<your_password> \
  -e MYSQL_DATABASE=vintelligence \
  vintelligence
```

### Option 3 — Direct Execution (Development)

```bash
# Install dependencies
pip install -r main/requirements.txt

# Initialize the database schema
mysql -u root -p < init.sql

# Run the application
python main/app.py
```

Open your browser at **http://localhost:5000**

---

## API Reference

### GET /

Serves the main web interface.

---

### GET /api/features

Returns the list of input features, their metadata, and available models.

**Response:**
```json
{
  "top_features": ["total_orders", "cancelled_orders", "..."],
  "feature_info": { "total_orders": { "label": "...", "correlation": 0.9358 } },
  "models": ["XGBoost", "RandomForest"]
}
```

---

### POST /api/predict

Performs a Revenue or COGS prediction for a given set of inputs.

**Request body:**
```json
{
  "model": "XGBoost",
  "target": "Revenue",
  "inputs": {
    "total_orders": 1200,
    "cancelled_orders": 50,
    "Revenue_lag_1": 5000000000,
    "returned_orders": 30,
    "Revenue_roll_mean_7": 4800000000,
    "Revenue_roll_mean_30": 4600000000,
    "Revenue_roll_mean_14": 4700000000,
    "avg_order_value": 350000,
    "avg_promo_discount": 10,
    "total_discount_amount": 50000000
  }
}
```

**Response:**
```json
{
  "prediction": 5234567890.12,
  "model": "XGBoost",
  "target": "Revenue",
  "formatted": "5,234,567,890 VND"
}
```

---

### GET /api/history?limit=50

Returns the N most recent prediction records (maximum 200).

**Response:**
```json
{
  "count": 50,
  "data": [
    {
      "id": 1,
      "created_at": "2026-05-07 18:00:00",
      "model_name": "XGBoost",
      "target": "Revenue",
      "prediction_value": 5234567890.12
    }
  ]
}
```

---

## Model Performance

Results evaluated via **Time Series Cross-Validation** (5 folds):

| Model | R² Score | MSE | RMSE |
|-------|----------|-----|------|
| XGBoost | **0.9955** | — | — |
| Random Forest | **0.99+** | — | — |

### Top 10 Features by Correlation

| Rank | Feature | Correlation (r) | Description |
|------|---------|-----------------|-------------|
| 1 | `total_orders` | +0.9358 | Total orders placed on the day |
| 2 | `cancelled_orders` | +0.8795 | Number of cancelled orders |
| 3 | `Revenue_lag_1` | +0.8657 | Revenue from the previous day |
| 4 | `returned_orders` | +0.8376 | Number of returned orders |
| 5 | `Revenue_roll_mean_7` | +0.6956 | 7-day rolling average revenue |
| 6 | `Revenue_roll_mean_30` | +0.6833 | 30-day rolling average revenue |
| 7 | `Revenue_roll_mean_14` | +0.6705 | 14-day rolling average revenue |
| 8 | `avg_order_value` | +0.6200 | Average value per order |
| 9 | `avg_promo_discount` | +0.5800 | Average promotional discount rate |
| 10 | `total_discount_amount` | +0.5500 | Total discount amount for the day |

---

## Project Structure

```
Datathon_VinTelligence/
|
+-- docker-compose.yml           # Service orchestration: Flask + MySQL
+-- Dockerfile                   # Flask application container
+-- init.sql                     # Database schema initialization
+-- .env                         # Environment variables (credentials)
+-- .dockerignore                # Docker build exclusions
+-- Makefile                     # Command shortcuts
|
+-- main/                        # Flask backend
|   +-- app.py                   # Entry point: API routes, DB connection pool
|   +-- requirements.txt         # Python dependencies
|   +-- feature_medians.json     # Median imputation values per feature
|
+-- models/                      # Trained model artifacts
|   +-- model_v1.pkl             # XGBoost + Random Forest (joblib format)
|
+-- webapp/                      # Frontend
|   +-- static/
|       +-- index.html           # Main UI
|       +-- style.css            # Dark theme stylesheet
|       +-- app.js               # Frontend logic
|
+-- notebook/                    # Jupyter notebooks for analysis
+-- data/                        # Raw and processed datasets
+-- reports/                     # Technical report (NeurIPS 2025 format)
+-- docs/                        # Supplementary documentation
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MYSQL_HOST` | `localhost` | MySQL server hostname |
| `MYSQL_PORT` | `3306` | MySQL port |
| `MYSQL_DATABASE` | `vintelligence` | Database name |
| `MYSQL_USER` | `root` | MySQL username |
| `MYSQL_PASSWORD` | `root` | MySQL password |
| `FLASK_ENV` | `production` | Flask environment mode |
| `FLASK_PORT` | `5000` | Flask listening port |

---

## License

This project is distributed under the **MIT License**.
See the [LICENSE](LICENSE) file for full terms.

---

<div align="center">

MANCHESTER_UNITED Team · Dang Van Tam · Datathon 2026

</div>
