# 🚀 VinTelligence 2026 — Revenue & COGS Forecasting

> **Datathon VinTelligence 2026 | Vòng 1**  
> Dự đoán doanh thu (Revenue) và giá vốn hàng bán (COGS) hàng ngày cho giai đoạn **2023-01-01 → 2024-07-01** (548 ngày).

---

## 📁 Cấu trúc Dự án

```
Datathon_VinTelligence/
├── data/
│   ├── datathon-2026-round-1/          # Dữ liệu gốc (raw)
│   │   ├── sales.csv                   # Doanh thu & COGS hàng ngày
│   │   ├── web_traffic.csv             # Lưu lượng truy cập web
│   │   ├── orders.csv                  # Đơn hàng
│   │   ├── order_items.csv             # Chi tiết đơn hàng
│   │   ├── returns.csv                 # Hoàn trả
│   │   ├── promotions.csv              # Khuyến mãi
│   │   └── sample_submission.csv       # File mẫu submission
│   └── data_clean/                     # Dữ liệu đã xử lý (tạo bởi notebook 01)
│       ├── sales_clean.csv
│       ├── calendar_features.csv
│       ├── prophet_holidays.csv
│       ├── tet_multipliers.csv
│       ├── aux_web_profile.csv
│       ├── aux_orders_profile.csv
│       ├── aux_returns_profile.csv
│       ├── aux_promos_profile.csv
│       └── hist_median_*.csv
├── notebook/
│   ├── 01_data_preparation.ipynb       # Chuẩn bị dữ liệu
│   ├── 02_baseline_models.ipynb        # Baseline: Prophet + LightGBM
│   ├── 03_advanced_ensemble.ipynb      # v4 Top Kill + v5 Naive-First
│   ├── 04_breakthrough.ipynb           # v10/v11: 10 strategies
│   └── forecasting.ipynb              # ⭐ Pipeline tổng hợp (chạy đây)
├── output/                             # Submissions
│   ├── v11_final_ensemble.csv          # 🥇 PRIMARY submission
│   ├── v11_final_e_variant.csv         # 🥈 BACKUP-1
│   ├── v10_E_cogs_ratio.csv            # 🥉 BACKUP-2
│   └── ...                            # Các submission khác
├── main/                               # Flask API (inference)
│   ├── app.py
│   └── pipeline/
├── models/                             # Saved models
├── references/                         # Tài liệu tham khảo
├── reports/                            # Báo cáo
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## ⚡ Chạy Nhanh

### 1. Cài đặt Dependencies

```bash
pip install prophet lightgbm catboost statsforecast scikit-learn pandas numpy matplotlib seaborn scipy
```

### 2. Chạy Pipeline Tổng hợp (Khuyến nghị)

Mở và chạy **`notebook/forecasting.ipynb`** — đây là notebook duy nhất cần chạy, bao gồm toàn bộ pipeline từ đầu đến cuối.

> 💡 **Chú ý:** Notebook tự động nhận dạng môi trường (Google Colab / Local) và thiết lập đường dẫn phù hợp.

### 3. Chạy Từng Bước (tùy chọn)

```
01_data_preparation.ipynb   →  02_baseline_models.ipynb
                            →  03_advanced_ensemble.ipynb
                            →  04_breakthrough.ipynb
```

---

## 🏗️ Kiến trúc Pipeline

```
Raw Data
    │
    ▼
[01] Data Preparation
  • Validate & clean sales data
  • Vietnamese calendar features (Tet, holidays, mega sales)
  • Prophet holiday DataFrame
  • Auxiliary profiles (web, orders, returns, promos)
  • Empirical Tet multipliers
    │
    ▼
[02] Baseline Models (v3)
  • Prophet (backbone) + LightGBM (residual correction)
  • AutoSearch: 17 hyperparameter profiles
  • Rolling-year cross-validation (2020/2021/2022)
    │
    ▼
[03] Advanced Ensemble (v4 + v5)
  • v4 – Top Kill: Theta + multiple Prophet configs + aggressive horizon decay
  • v5 – Naive-First: Naive364 backbone, LightGBM corrects Naive residuals
    │
    ▼
[04] Breakthrough Search (v10 + v11)
  • 10 parallel strategies (A–G + scaled + statsfc + post2019)
  • Scale correction to match sample_submission level
  • statsforecast: AutoTheta + AutoETS + SeasonalNaive
  • Final weighted ensemble
    │
    ▼
forecasting.ipynb (TỔNG HỢP)
  • Chạy toàn bộ pipeline end-to-end
  • Output: 15 submission files
```

---

## 💡 Key Insights

| Insight | Mô tả |
|---------|--------|
| 🔑 **Naive-First** | Naive364 MAE ≈ **830k** vs Prophet alone MAE ≈ **2.3M** → Naive là backbone, không phải Prophet |
| 🔑 **COGS/Revenue ratio** | Tỷ lệ COGS/Revenue rất ổn định (~0.68-0.72). Dự đoán Revenue, derive COGS từ ratio giảm lỗi tổng thể |
| 🔑 **Tet Empirical Multipliers** | Tính multiplier từ dữ liệu lịch sử cho từng ngày xung quanh Tết, chính xác hơn dùng window flag |
| 🔑 **Post-2019 Structural Break** | COVID-19 tạo ra structural break → train riêng model từ 2019+ cho short-range prediction |
| 🔑 **Scale Correction** | Model thường over-predict ~40%. Scale correction để match level với sample_submission |
| 🔑 **M-competition winners** | AutoTheta, AutoETS (statsforecast) cho kết quả tốt trên time-series competition |

---

## 📊 Forecast Strategies & Weights

| Strategy | Mô tả | Ensemble Weight |
|----------|--------|:---:|
| A | Naive 75% + v5_pure_naive 25% | 10% |
| B | Post-2018 training + LightGBM | 10% |
| C | Blend best previous submissions | 10% |
| D | Sample submission as level anchor | 10% |
| **E** | **COGS = Revenue × historical ratio** | **15%** |
| F | Smoothed Tet calibration (Savitzky-Golay) | 10% |
| G | LightGBM + CatBoost residual ensemble | 5% |
| scaled | Scale-corrected to sample_sub level | 10% |
| statsfc | AutoTheta + AutoETS + SeasonalNaive | 10% |
| post2019 | COVID-aware post-2019 models | 10% |

---

## 📤 Submission Files

| File | Mô tả | Khuyến nghị |
|------|--------|:-----------:|
| `v11_final_ensemble.csv` | Final weighted ensemble của 10 strategies | 🥇 PRIMARY |
| `v11_final_e_variant.csv` | Ensemble Revenue + COGS từ ratio | 🥈 BACKUP-1 |
| `v10_E_cogs_ratio.csv` | Revenue trực tiếp, COGS từ ratio | 🥉 BACKUP-2 |
| `v11_scaled.csv` | Force-scale về sample_sub level (diagnostic) | 🔬 DIAGNOSTIC |
| `v5_corrected.csv` | v5 Naive-First với full LGBM correction | baseline |
| `v5_pure_naive.csv` | Pure Naive364 + Tet multipliers | baseline |
| `v10_D_sample_anchor.csv` | 60% model + 40% sample_sub | alternative |

---

## 🛠️ Model Architecture

### v5 — Naive-First (Primary Backbone)
```
Forecast = 0.6 × Naive364_tet + 0.4 × MultiYearWeightedMedian
         + damped(LightGBM correction on Naive residuals)

Where:
  Naive364_tet = Naive364 × YoY_growth × Tet_multiplier
  Damping = exp(-t / 300)  # Correction fades at far horizons
```

### v5 Feature Matrix (60+ features)
- **Calendar**: DOW, DOY, month, quarter, cyclical encodings
- **Vietnamese events**: Tet proximity, VN holidays, mega sale windows
- **Historical medians**: By DOY / DOW / month (zero leakage)
- **Auxiliary profiles**: Web traffic, order count, returns, promotions
- **Prophet hint**: Weak feature from Prophet yhat

### LightGBM Configuration
```python
LGBMRegressor(
    n_estimators=1200,    learning_rate=0.02,
    num_leaves=31,        min_child_samples=20,
    reg_alpha=0.5,        reg_lambda=5.0,
    objective='mae',      subsample=0.85,
    colsample_bytree=0.85,
    sample_weight=recency_weighted  # Recent rows weighted higher
)
```

---

## 📈 Cross-Validation Strategy

### Rolling Year CV (Notebooks 01-03)
- Folds: 2020, 2021, 2022 validation years
- Weights: [1.0, 1.5, 2.0] — recent folds matter more
- Metric: Weighted average MAE

### 548-Day Holdout Validation (Notebook 03)
- Origins: [2021-06-30, 2021-01-01, 2020-06-30]
- Mimics competition setup exactly (548-day forecast horizon)

---

## 🐳 Docker Deployment

```bash
# Build và chạy Flask API
docker-compose up --build

---

## 📦 Dependencies

```
prophet>=1.1          # Facebook Prophet
lightgbm>=3.3         # LightGBM
catboost>=1.2         # CatBoost (optional, Strategy G)
statsforecast>=1.5    # AutoTheta, AutoETS, SeasonalNaive (optional)
scikit-learn>=1.0     # LinearRegression, TimeSeriesSplit
pandas>=1.5
numpy>=1.23
matplotlib>=3.5
seaborn>=0.11
scipy>=1.9
```

---

## 📝 Ghi Chú Quan Trọng

> [!IMPORTANT]
> Chạy `forecasting.ipynb` là đủ để tái tạo toàn bộ kết quả.  
> Các file `01` → `04` là bước phát triển iterative, không cần chạy lại trừ khi muốn hiểu từng bước.

> [!NOTE]
> **Môi trường**: Notebook tự động detect Colab vs Local và mount Drive nếu cần.  
> **Local**: Đặt project tại đường dẫn chứa thư mục `data/` và chạy trực tiếp.

> [!TIP]
> Để submit nhanh nhất: chạy `forecasting.ipynb` đến cell 13, lấy file `output/v11_final_ensemble.csv`.

---

## 🏆 Leaderboard Context

- LB best so far: **931k MAE**
- Top 1 target: **532k MAE** → gap **400k**
- Root cause identified: Model over-predicts ~40% (mean ~4.4M vs sample_sub mean ~3.1M)
- v11 strategies address scale gap via correction + post-2019 training

---

*Datathon VinTelligence 2026 | Team solution*
