import http.client
import json
import os
from database.auth_db import get_auth_token
from database.token_db import get_token
from mapping.transform_data import transform_data , map_product_type, reverse_map_product_type, transform_modify_order_data


def get_api_response(endpoint, method="GET", payload='', auth_token=None, api_key=None):
    # If auth_token and api_key are not provided, try to get them from session
    from flask import session
    
    if auth_token is None:
        # Try to get from session first
        auth_token = session.get('AUTH_TOKEN')  # Changed from 'auth_token' to 'AUTH_TOKEN'
        
        # If not in session, return an error - we need a valid auth token
        if auth_token is None:
            print("ERROR: No AUTH_TOKEN found in session")
            return {"status": "error", "message": "Authentication token not found. Please log in again."}
    
    if api_key is None:
        # Try to get from session first
        api_key = session.get('apikey')  # Changed from 'api_key' to 'apikey'
        
        # If not in session, return an error - we need a valid API key
        if api_key is None:
            print("ERROR: No apikey found in session")
            return {"status": "error", "message": "API key not found. Please log in again."}

    # Check if auth_token or api_key is a dictionary (error response from earlier checks)
    if isinstance(auth_token, dict) and auth_token.get('status') == 'error':
        return auth_token
    if isinstance(api_key, dict) and api_key.get('status') == 'error':
        return api_key
        
    try:
        conn = http.client.HTTPSConnection("apiconnect.angelbroking.com")
        headers = {
          'Authorization': f'Bearer {auth_token}',
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-UserType': 'USER',
          'X-SourceID': 'WEB',
          'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
          'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
          'X-MACAddress': 'MAC_ADDRESS',
          'X-PrivateKey': api_key
        }
        conn.request(method, endpoint, payload, headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        print(f"API Error: {str(e)}")
        return {"status": "error", "message": f"API Connection Error: {str(e)}"}

def get_order_book():
    try:
        return get_api_response("/rest/secure/angelbroking/order/v1/getOrderBook")
    except Exception as e:
        print(f"Error in get_order_book: {str(e)}")
        return {"status": "error", "message": str(e)}

def get_trade_book():
    return get_api_response("/rest/secure/angelbroking/order/v1/getTradeBook")

def get_positions():
    return get_api_response("/rest/secure/angelbroking/order/v1/getPosition")

def get_holdings():
    return get_api_response("/rest/secure/angelbroking/portfolio/v1/getAllHolding")

def get_open_position(tradingsymbol, exchange, producttype):
    positions_data = get_positions()
    net_qty = '0'

    if positions_data and positions_data.get('status') and positions_data.get('data'):
        for position in positions_data['data']:
            if position.get('tradingsymbol') == tradingsymbol and position.get('exchange') == exchange and position.get('producttype') == producttype:
                net_qty = position.get('netqty', '0')
                break  # Assuming you need the first match

    return net_qty

def place_order_api(data, user_id=None):
    # Get auth token and API key from session if available
    from flask import session
    from database.auth_db import get_auth_tokens, get_user_by_id
    
    AUTH_TOKEN = session.get('AUTH_TOKEN')  # Try session first
    BROKER_API_KEY = session.get('apikey')
    
    # If not in session and user_id provided, get from database
    if AUTH_TOKEN is None and user_id:
        # Get user details from database
        user = get_user_by_id(user_id)
        if user:
            # Get auth tokens from database
            tokens = get_auth_tokens(user.username)
            if tokens.get('status') == 'success':
                AUTH_TOKEN = tokens.get('access_token')
                print(f"✅ Using auth token from database for user: {user.username}")
            
            # Get broker API key from user record
            BROKER_API_KEY = user.apikey
            print(f"✅ Using broker API key from database for user: {user_id}")
    
    # Fallback to environment variables
    if AUTH_TOKEN is None:
        login_username = os.getenv('LOGIN_USERNAME')
        AUTH_TOKEN = get_auth_token(login_username)
    
    if BROKER_API_KEY is None:
        BROKER_API_KEY = os.getenv('BROKER_API_KEY')
        
    data['apikey'] = BROKER_API_KEY
    token = get_token(data['symbol'], data['exchange'])
    newdata = transform_data(data, token)  
    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': 'CLIENT_LOCAL_IP', 
        'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
        'X-MACAddress': 'MAC_ADDRESS',
        'X-PrivateKey': newdata['apikey']
    }
    payload = json.dumps({
        "variety": newdata.get('variety', 'NORMAL'),
        "tradingsymbol": newdata['tradingsymbol'],
        "symboltoken": newdata['symboltoken'],
        "transactiontype": newdata['transactiontype'],
        "exchange": newdata['exchange'],
        "ordertype": newdata.get('ordertype', 'MARKET'),
        "producttype": newdata.get('producttype', 'INTRADAY'),
        "duration": newdata.get('duration', 'DAY'),
        "price": newdata.get('price', '0'),
        "triggerprice": newdata.get('triggerprice', '0'),
        "squareoff": newdata.get('squareoff', '0'),
        "stoploss": newdata.get('stoploss', '0'),
        "quantity": newdata['quantity']
    })

    print(payload)
    conn = http.client.HTTPSConnection("apiconnect.angelbroking.com")
    conn.request("POST", "/rest/secure/angelbroking/order/v1/placeOrder", payload, headers)
    res = conn.getresponse()
    response_data = json.loads(res.read().decode("utf-8"))
    if response_data['status'] == True:
        orderid = response_data['data']['orderid']
    else:
        orderid = None
    return res, response_data, orderid

def place_smartorder_api(data, user_id=None):

    #If no API call is made in this function then res will return None
    res = None

    # Extract necessary info from data
    symbol = data.get("symbol")
    exchange = data.get("exchange")
    product = data.get("product")
    position_size = int(data.get("position_size", "0"))

    

    # Get current open position for the symbol
    current_position = int(get_open_position(symbol, exchange, map_product_type(product)))


    #print(f"position_size : {position_size}") 
    #print(f"Open Position : {current_position}") 
    
    # Determine action based on position_size and current_position
    action = None
    quantity = 0


    # If both position_size and current_position are 0, do nothing
    if position_size == 0 and current_position == 0:
        action = data['action']
        quantity = data['quantity']
        #print(f"action : {action}")
        #print(f"Quantity : {quantity}")
        res, response, orderid = place_order_api(data, user_id=user_id)
        #print(res)
        #print(response)
        
        return res , response
        
    elif position_size == current_position:
        response = {"status": "success", "message": "No action needed. Position size matches current position."}
        return res, response  # res remains None as no API call was mad
   
   

    if position_size == 0 and current_position>0 :
        action = "SELL"
        quantity = abs(current_position)
    elif position_size == 0 and current_position<0 :
        action = "BUY"
        quantity = abs(current_position)
    elif current_position == 0:
        action = "BUY" if position_size > 0 else "SELL"
        quantity = abs(position_size)
    else:
        if position_size > current_position:
            action = "BUY"
            quantity = position_size - current_position
            #print(f"smart buy quantity : {quantity}")
        elif position_size < current_position:
            action = "SELL"
            quantity = current_position - position_size
            #print(f"smart sell quantity : {quantity}")




    if action:
        # Prepare data for placing the order
        order_data = data.copy()
        order_data["action"] = action
        order_data["quantity"] = str(quantity)

        #print(order_data)
        # Place the order
        res, response, orderid = place_order_api(order_data, user_id=user_id)
        #print(res)
        #print(response)
        
        return res , response, orderid
    



def close_all_positions(current_api_key):
    # Fetch the current open positions
    positions_response = get_positions()

    # Check if the positions data is null or empty
    if positions_response['data'] is None or not positions_response['data']:
        return {"message": "No Open Positions Found"}, 200

    if positions_response['status']:
        # Loop through each position to close
        for position in positions_response['data']:
            # Skip if net quantity is zero
            if int(position['netqty']) == 0:
                continue

            # Determine action based on net quantity
            action = 'SELL' if int(position['netqty']) > 0 else 'BUY'
            quantity = abs(int(position['netqty']))

            # Prepare the order payload
            place_order_payload = {
                "apikey": current_api_key,
                "strategy": "Squareoff",
                "symbol": position['tradingsymbol'],
                "action": action,
                "exchange": position['exchange'],
                "pricetype": "MARKET",
                "product": reverse_map_product_type(position['producttype']),
                "quantity": str(quantity)
            }

            print(place_order_payload)

            # Place the order to close the position
            _, api_response, _ =   place_order_api(place_order_payload)

            print(api_response)
            
            # Note: Ensure place_order_api handles any errors and logs accordingly

    return {'status': 'success', "message": "All Open Positions SquaredOff"}, 200


def cancel_order(orderid):
    # Get auth token and API key from session if available
    from flask import session
    
    AUTH_TOKEN = session.get('AUTH_TOKEN')  # Changed from 'auth_token' to 'AUTH_TOKEN'
    if AUTH_TOKEN is None:
        login_username = os.getenv('LOGIN_USERNAME')
        AUTH_TOKEN = get_auth_token(login_username)
    
    api_key = session.get('apikey')  # Changed from 'api_key' to 'apikey'
    if api_key is None:
        api_key = os.getenv('BROKER_API_KEY')
    
    # Set up the request headers
    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': 'CLIENT_LOCAL_IP', 
        'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
        'X-MACAddress': 'MAC_ADDRESS',
        'X-PrivateKey': api_key
    }
    
    # Prepare the payload
    payload = json.dumps({
        "variety": "NORMAL",
        "orderid": orderid,
    })
    
    # Establish the connection and send the request
    conn = http.client.HTTPSConnection("apiconnect.angelbroking.com")  # Adjust the URL as necessary
    conn.request("POST", "/rest/secure/angelbroking/order/v1/cancelOrder", payload, headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
    
    # Check if the request was successful
    if data.get("status"):
        # Return a success response
        return {"status": "success", "orderid": orderid}, 200
    else:
        # Return an error response
        return {"status": "error", "message": data.get("message", "Failed to cancel order")}, res.status


def modify_order(data):
    # Get auth token and API key from session if available
    from flask import session
    
    AUTH_TOKEN = session.get('AUTH_TOKEN')  # Changed from 'auth_token' to 'AUTH_TOKEN'
    if AUTH_TOKEN is None:
        login_username = os.getenv('LOGIN_USERNAME')
        AUTH_TOKEN = get_auth_token(login_username)
    
    api_key = session.get('apikey')  # Changed from 'api_key' to 'apikey'
    if api_key is None:
        api_key = os.getenv('BROKER_API_KEY')

    token = get_token(data['symbol'], data['exchange'])
    transformed_data = transform_modify_order_data(data, token)  # You need to implement this function
    # Set up the request headers
    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': 'CLIENT_LOCAL_IP', 
        'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
        'X-MACAddress': 'MAC_ADDRESS',
        'X-PrivateKey': api_key
    }
    payload = json.dumps(transformed_data)

    conn = http.client.HTTPSConnection("apiconnect.angelbroking.com")
    conn.request("POST", "/rest/secure/angelbroking/order/v1/modifyOrder", payload, headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))

    if data.get("status") == "true" or data.get("message") == "SUCCESS":
        return {"status": "success", "orderid": data["data"]["orderid"]}, 200
    else:
        return {"status": "error", "message": data.get("message", "Failed to modify order")}, res.status



def cancel_all_orders_api(data):
    # Get the order book
    order_book_response = get_order_book()
    #print(order_book_response)
    if order_book_response['status'] != True:
        return [], []  # Return empty lists indicating failure to retrieve the order book

    # Filter orders that are in 'open' or 'trigger_pending' state
    orders_to_cancel = [order for order in order_book_response.get('data', [])
                        if order['status'] in ['open', 'trigger pending']]
    #print(orders_to_cancel)
    canceled_orders = []
    failed_cancellations = []

    # Cancel the filtered orders
    for order in orders_to_cancel:
        orderid = order['orderid']
        cancel_response, status_code = cancel_order(orderid)
        if status_code == 200:
            canceled_orders.append(orderid)
        else:
            failed_cancellations.append(orderid)
    
    return canceled_orders, failed_cancellations

