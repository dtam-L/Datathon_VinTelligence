"""
Flask backend for VinTelligence Revenue & COGS Forecasting Model
- Serves the model-v1.pkl predictions via REST API
- Persists every prediction to MySQL
"""

import os
import json
import time
import warnings
import joblib
import numpy as np
import mysql.connector
from mysql.connector import pooling
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

warnings.filterwarnings('ignore')

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(__file__)
STATIC_DIR  = os.path.join(BASE_DIR, '..', 'webapp', 'static')
MODEL_PATH  = os.path.join(BASE_DIR, '..', 'models', 'model_v1.pkl')
MEDIANS_PATH = os.path.join(BASE_DIR, 'feature_medians.json')

# ──────────────────────────────────────────────────────────────────────────────
# Flask app
# ──────────────────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=STATIC_DIR)
CORS(app)

# ──────────────────────────────────────────────────────────────────────────────
# Load model & medians at startup
# ──────────────────────────────────────────────────────────────────────────────
models = joblib.load(MODEL_PATH)

with open(MEDIANS_PATH, 'r') as _f:
    FEATURE_MEDIANS = json.load(_f)

# ──────────────────────────────────────────────────────────────────────────────
# MySQL connection pool  (env vars injected by docker-compose)
# ──────────────────────────────────────────────────────────────────────────────
DB_CONFIG = {
    'host':     os.getenv('MYSQL_HOST',     'localhost'),
    'port':     int(os.getenv('MYSQL_PORT', '3306')),
    'database': os.getenv('MYSQL_DATABASE', 'vintelligence'),
    'user':     os.getenv('MYSQL_USER',     'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'root'),
    'charset':  'utf8mb4',
}

def _wait_for_db(max_retries: int = 15, delay: int = 3):
    """Retry connecting to MySQL until it's ready (container startup delay)."""
    for attempt in range(1, max_retries + 1):
        try:
            cnx = mysql.connector.connect(**DB_CONFIG)
            cnx.close()
            print(f"[DB] Connected to MySQL on attempt {attempt}")
            return
        except mysql.connector.Error as err:
            print(f"[DB] Attempt {attempt}/{max_retries} failed: {err}. Retrying in {delay}s...")
            time.sleep(delay)
    raise RuntimeError("[DB] Could not connect to MySQL after max retries.")

_wait_for_db()

db_pool = pooling.MySQLConnectionPool(
    pool_name="vintel_pool",
    pool_size=5,
    **DB_CONFIG
)


def get_conn():
    return db_pool.get_connection()


# ──────────────────────────────────────────────────────────────────────────────
# Feature lists
# ──────────────────────────────────────────────────────────────────────────────
TOP_10_FEATURES = [
    'total_orders',
    'cancelled_orders',
    'Revenue_lag_1',
    'returned_orders',
    'Revenue_roll_mean_7',
    'Revenue_roll_mean_30',
    'Revenue_roll_mean_14',
    'avg_order_value',
    'avg_promo_discount',
    'total_discount_amount',
]

# Exact 47 features the model was trained on (from model.feature_names_in_)
ALL_FEATURES = [
    'total_sessions', 'total_page_views', 'avg_bounce_rate', 'avg_session_duration', 'n_traffic_sources',
    'src_direct_sessions', 'src_email_campaign_sessions', 'src_organic_search_sessions',
    'src_paid_search_sessions', 'src_referral_sessions', 'src_social_media_sessions',
    'active_promos_count', 'avg_promo_discount', 'has_stackable_promo',
    'total_orders', 'cancelled_orders', 'returned_orders', 'cancellation_rate',
    'mobile_ratio', 'total_discount_amount', 'avg_order_value',
    'total_returns', 'total_refund',
    'year', 'month', 'day', 'dayofweek', 'is_weekend',
    'is_month_start', 'is_month_end', 'month_sin', 'month_cos',
    'dow_sin', 'dow_cos',
    'Revenue_lag_1', 'Revenue_lag_7', 'Revenue_lag_14', 'Revenue_lag_30',
    'Revenue_roll_mean_7', 'Revenue_roll_std_7', 'Revenue_roll_mean_14', 'Revenue_roll_std_14',
    'Revenue_roll_mean_30', 'Revenue_roll_std_30',
    'revenue_momentum_7_30',
    'gross_margin_lag_1', 'gross_margin_lag_7',
]

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def save_prediction(model_name: str, target: str, prediction: float, inputs: dict):
    """Ghi kết quả dự đoán vào bảng predictions trong MySQL."""
    sql = """
        INSERT INTO predictions (
            model_name, target, prediction_value,
            total_orders, cancelled_orders, Revenue_lag_1, returned_orders,
            Revenue_roll_mean_7, Revenue_roll_mean_30, Revenue_roll_mean_14,
            avg_order_value, avg_promo_discount, total_discount_amount
        ) VALUES (
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s
        )
    """
    values = (
        model_name, target, prediction,
        inputs.get('total_orders'),
        inputs.get('cancelled_orders'),
        inputs.get('Revenue_lag_1'),
        inputs.get('returned_orders'),
        inputs.get('Revenue_roll_mean_7'),
        inputs.get('Revenue_roll_mean_30'),
        inputs.get('Revenue_roll_mean_14'),
        inputs.get('avg_order_value'),
        inputs.get('avg_promo_discount'),
        inputs.get('total_discount_amount'),
    )
    try:
        cnx = get_conn()
        cursor = cnx.cursor()
        cursor.execute(sql, values)
        cnx.commit()
        cursor.close()
        cnx.close()
    except Exception as err:
        print(f"[DB] save_prediction error: {err}")


# ──────────────────────────────────────────────────────────────────────────────
# Static routes
# ──────────────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/predict
# ──────────────────────────────────────────────────────────────────────────────
@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data       = request.get_json()
        model_name = data.get('model', 'XGBoost')
        target     = data.get('target', 'Revenue')
        inputs     = data.get('inputs', {})

        # Build feature vector:
        # - Top-10 features → user-supplied value
        # - Everything else  → training-data MEDIAN (not 0)
        feature_vector = []
        for feat in ALL_FEATURES:
            if feat in inputs:
                try:
                    feature_vector.append(float(inputs[feat]))
                except (ValueError, TypeError):
                    feature_vector.append(FEATURE_MEDIANS.get(feat, 0.0))
            else:
                feature_vector.append(FEATURE_MEDIANS.get(feat, 0.0))

        X = np.array([feature_vector])

        if model_name not in models:
            return jsonify({'error': f'Model "{model_name}" not found'}), 400

        prediction = float(models[model_name].predict(X)[0])

        # Lưu vào MySQL
        save_prediction(model_name, target, prediction, inputs)

        return jsonify({
            'prediction': prediction,
            'model':      model_name,
            'target':     target,
            'formatted':  f"{prediction:,.0f} VND"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/history  — lịch sử 50 lần dự đoán gần nhất
# ──────────────────────────────────────────────────────────────────────────────
@app.route('/api/history', methods=['GET'])
def history():
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        cnx = get_conn()
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM predictions ORDER BY created_at DESC LIMIT %s",
            (limit,)
        )
        rows = cursor.fetchall()
        cursor.close()
        cnx.close()

        # datetime không JSON-serializable → chuyển thành string
        for row in rows:
            if row.get('created_at'):
                row['created_at'] = row['created_at'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({'count': len(rows), 'data': rows})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/features
# ──────────────────────────────────────────────────────────────────────────────
@app.route('/api/features', methods=['GET'])
def get_features():
    feature_info = {
        'total_orders': {
            'label': 'Total Orders',
            'description': 'Tong so don hang dat trong ngay',
            'unit': 'orders', 'correlation': 0.9358, 'default': 1200
        },
        'cancelled_orders': {
            'label': 'Cancelled Orders',
            'description': 'So don hang bi huy trong ngay',
            'unit': 'orders', 'correlation': 0.8795, 'default': 50
        },
        'Revenue_lag_1': {
            'label': 'Revenue (Hom qua)',
            'description': 'Doanh thu ngay hom qua (lag 1 ngay)',
            'unit': 'VND', 'correlation': 0.8657, 'default': 5000000000
        },
        'returned_orders': {
            'label': 'Returned Orders',
            'description': 'So don hang bi tra lai trong ngay',
            'unit': 'orders', 'correlation': 0.8376, 'default': 30
        },
        'Revenue_roll_mean_7': {
            'label': 'Revenue TB 7 ngay',
            'description': 'Doanh thu trung binh 7 ngay gan nhat',
            'unit': 'VND', 'correlation': 0.6956, 'default': 4800000000
        },
        'Revenue_roll_mean_30': {
            'label': 'Revenue TB 30 ngay',
            'description': 'Doanh thu trung binh 30 ngay gan nhat',
            'unit': 'VND', 'correlation': 0.6833, 'default': 4600000000
        },
        'Revenue_roll_mean_14': {
            'label': 'Revenue TB 14 ngay',
            'description': 'Doanh thu trung binh 14 ngay gan nhat',
            'unit': 'VND', 'correlation': 0.6705, 'default': 4700000000
        },
        'avg_order_value': {
            'label': 'Avg Order Value',
            'description': 'Gia tri trung binh moi don hang',
            'unit': 'VND', 'correlation': 0.6200, 'default': 350000
        },
        'avg_promo_discount': {
            'label': 'Avg Promo Discount',
            'description': 'Muc giam gia khuyen mai trung binh',
            'unit': '%', 'correlation': 0.5800, 'default': 10
        },
        'total_discount_amount': {
            'label': 'Total Discount Amount',
            'description': 'Tong so tien giam gia trong ngay',
            'unit': 'VND', 'correlation': 0.5500, 'default': 50000000
        },
    }
    return jsonify({
        'top_features': TOP_10_FEATURES,
        'feature_info': feature_info,
        'all_features': ALL_FEATURES,
        'models':       list(models.keys())
    })


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    debug = os.getenv('FLASK_ENV', 'production') != 'production'
    port  = int(os.getenv('FLASK_PORT', 5000))
    print(f"[OK] Models loaded: {list(models.keys())}")
    print(f"[*]  Running on http://0.0.0.0:{port}  (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
