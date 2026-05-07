"""
Flask backend for VinTelligence Revenue & COGS Forecasting Model
Serves the model-v1.pkl predictions via REST API
"""

import os
import joblib
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

# ──────────────────────────────────────────────────────────────────────────────
# Load model at startup
# ──────────────────────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'model_v1.pkl')
models = joblib.load(MODEL_PATH)

# Top 10 features most correlated with Revenue (from EDA)
# Note: COGS_lag_1 and COGS_roll_mean_* are highly correlated but not in the model's
# 47-feature set; we use Revenue_lag_1, Revenue_roll_mean_* instead for input form
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
# Serve static files
# ──────────────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# ──────────────────────────────────────────────────────────────────────────────
# Prediction endpoint
# ──────────────────────────────────────────────────────────────────────────────
@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        model_name = data.get('model', 'XGBoost')
        target = data.get('target', 'Revenue')
        inputs = data.get('inputs', {})

        # Build feature vector (zeros for features not provided)
        feature_vector = []
        for feat in ALL_FEATURES:
            val = inputs.get(feat, 0.0)
            try:
                feature_vector.append(float(val))
            except (ValueError, TypeError):
                feature_vector.append(0.0)

        X = np.array([feature_vector])

        # Get the correct model
        if model_name not in models:
            return jsonify({'error': f'Model "{model_name}" not found'}), 400

        model = models[model_name]

        # For Revenue vs COGS we need the model trained on the right target
        # The saved dict has models trained, we predict and return
        prediction = float(model.predict(X)[0])

        return jsonify({
            'prediction': prediction,
            'model': model_name,
            'target': target,
            'formatted': f"{prediction:,.0f} VND"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/features', methods=['GET'])
def get_features():
    """Return the top 10 features with descriptions"""
    feature_info = {
        'total_orders': {
            'label': 'Total Orders',
            'description': 'Tổng số đơn hàng đặt trong ngày',
            'unit': 'orders',
            'correlation': 0.9358,
            'default': 1200
        },
        'cancelled_orders': {
            'label': 'Cancelled Orders',
            'description': 'Số đơn hàng bị huỷ trong ngày',
            'unit': 'orders',
            'correlation': 0.8795,
            'default': 50
        },
        'Revenue_lag_1': {
            'label': 'Revenue (Hôm qua)',
            'description': 'Doanh thu ngày hôm qua (lag 1 ngày)',
            'unit': 'VND',
            'correlation': 0.8657,
            'default': 5000000000
        },
        'returned_orders': {
            'label': 'Returned Orders',
            'description': 'Số đơn hàng bị trả lại trong ngày',
            'unit': 'orders',
            'correlation': 0.8376,
            'default': 30
        },
        'Revenue_roll_mean_7': {
            'label': 'Revenue TB 7 ngày',
            'description': 'Doanh thu trung bình 7 ngày gần nhất',
            'unit': 'VND',
            'correlation': 0.6956,
            'default': 4800000000
        },
        'Revenue_roll_mean_30': {
            'label': 'Revenue TB 30 ngày',
            'description': 'Doanh thu trung bình 30 ngày gần nhất',
            'unit': 'VND',
            'correlation': 0.6833,
            'default': 4600000000
        },
        'Revenue_roll_mean_14': {
            'label': 'Revenue TB 14 ngày',
            'description': 'Doanh thu trung bình 14 ngày gần nhất',
            'unit': 'VND',
            'correlation': 0.6705,
            'default': 4700000000
        },
        'avg_order_value': {
            'label': 'Avg Order Value',
            'description': 'Giá trị trung bình mỗi đơn hàng',
            'unit': 'VND',
            'correlation': 0.6200,
            'default': 350000
        },
        'avg_promo_discount': {
            'label': 'Avg Promo Discount',
            'description': 'Mức giảm giá khuyến mãi trung bình',
            'unit': '%',
            'correlation': 0.5800,
            'default': 10
        },
        'total_discount_amount': {
            'label': 'Total Discount Amount',
            'description': 'Tổng số tiền giảm giá trong ngày',
            'unit': 'VND',
            'correlation': 0.5500,
            'default': 50000000
        },
    }

    return jsonify({
        'top_features': TOP_10_FEATURES,
        'feature_info': feature_info,
        'all_features': ALL_FEATURES,
        'models': list(models.keys())
    })


if __name__ == '__main__':
    print("[OK] Model loaded successfully!")
    print(f"   Available models: {list(models.keys())}")
    print("[*] Starting server on http://localhost:5000")
    app.run(debug=True, port=5000)

