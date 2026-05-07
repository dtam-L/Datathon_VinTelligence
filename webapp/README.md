# VinTelligence Revenue Forecasting — Web App

## 🚀 Cách chạy

```bash
cd webapp
python app.py
```

Sau đó mở **http://localhost:5000** trong trình duyệt.

---

## 📁 Cấu trúc

```
webapp/
├── app.py              # Flask backend (REST API + static file server)
└── static/
    ├── index.html      # Giao diện chính
    ├── style.css       # Dark theme styling
    └── app.js          # Frontend logic (fetch API, render, animate)
```

---

## 🔌 API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/` | Giao diện web |
| `GET` | `/api/features` | Lấy danh sách 10 features + metadata |
| `POST` | `/api/predict` | Dự đoán Revenue/COGS |

### POST `/api/predict` — Request body

```json
{
  "model": "XGBoost",
  "target": "Revenue",
  "inputs": {
    "total_orders": 1200,
    "cancelled_orders": 50,
    "Revenue_lag_1": 5000000000,
    ...
  }
}
```

---

## 🏆 10 Features Tương quan Cao nhất

| # | Feature | Correlation (r) |
|---|---------|----------------|
| 1 | `total_orders` | +0.9358 |
| 2 | `cancelled_orders` | +0.8795 |
| 3 | `Revenue_lag_1` | +0.8657 |
| 4 | `returned_orders` | +0.8376 |
| 5 | `Revenue_roll_mean_7` | +0.6956 |
| 6 | `Revenue_roll_mean_30` | +0.6833 |
| 7 | `Revenue_roll_mean_14` | +0.6705 |
| 8 | `avg_order_value` | +0.6200 |
| 9 | `avg_promo_discount` | +0.5800 |
| 10 | `total_discount_amount` | +0.5500 |

##  Model Performance

| Model | R² Score |
|-------|---------|
| XGBoost | **0.9955** |
| Random Forest | 0.99+ |