# blueprints/tv_json.py

from flask import Blueprint, render_template, request, jsonify, session, url_for, redirect
from database.tv_search import search_symbols
from database.auth_db import get_api_key
from collections import OrderedDict
from dotenv import load_dotenv
import os

load_dotenv()

host = os.getenv('HOST_SERVER')

tv_json_bp = Blueprint('tv_json_bp', __name__, url_prefix='/tradingview')

@tv_json_bp.route('/', methods=['GET', 'POST'])
def tradingview_json():
    
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))  # Fixed auth_bp.login to auth.login
    
    if request.method == 'GET':
        return render_template('tradingview.html', host=host)
    
    if request.method == 'POST':
        symbol_input = request.json.get('symbol')
        exchange = request.json.get('exchange')
        product = request.json.get('product')
        
        # Always get the latest API key from the database
        user_id = session.get('user_id')
        api_key = get_api_key(user_id)
        
        print(f"DEBUG - User ID: {user_id}")
        print(f"DEBUG - API key from database: {api_key}")
        
        # If no API key found, generate a new platform key
        if not api_key:
            print("No API key found, generating new platform key...")
            from blueprints.apikey import generate_api_key
            from database.auth_db import upsert_api_key
            api_key = generate_api_key(user_id)
            upsert_api_key(user_id, api_key)
            print(f"Generated new API key: {api_key}")
        
        # Validate if it's a platform key
        from blueprints.apikey import is_platform_api_key
        if not is_platform_api_key(api_key, user_id):
            print("Detected broker API key, generating platform key...")
            from blueprints.apikey import generate_api_key
            from database.auth_db import upsert_api_key
            api_key = generate_api_key(user_id)
            upsert_api_key(user_id, api_key)
            print(f"Generated platform API key: {api_key}")
        
        # Search for the symbol in the database to get the exchange segment
        symbols = search_symbols(symbol_input, exchange)
        if not symbols:
            return jsonify({'error': 'Symbol not found'}), 404
        symbol_data = symbols[0]  # Take the first match
        
        # Create the JSON response object
        # Create an OrderedDict with the keys in the desired order
        json_data = OrderedDict([
            ("apikey", api_key),
            ("strategy", "Tradingview"),
            ("symbol", symbol_data.symbol),
            ("action", "{{strategy.order.action}}"),
            ("exchange", symbol_data.exchange),
            ("pricetype", "MARKET"),
            ("product", product),
            ("quantity", "{{strategy.order.contracts}}"),
            ("position_size", "{{strategy.position_size}}"),
        ])
        
        # JSONify the ordered dict
        response = jsonify(json_data)
        response.headers.add('Content-Type', 'application/json')
        return response
    
    return jsonify({'status': 'success', 'message': 'TradingView endpoint', 'host': host})