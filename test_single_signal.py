import requests
import time

url = "http://127.0.0.1:5000/api/test/socket"

print("🧪 Sending a single test signal...")
print("=" * 60)
print("⏳ Waiting 3 seconds for you to open browser console...")
time.sleep(3)

test_data = {
    "symbol": "NIFTY",
    "action": "BUY",
    "orderid": "LIVE_TEST_001"
}

print(f"\n📤 Sending: {test_data['action']} {test_data['symbol']}")

try:
    response = requests.post(url, json=test_data, timeout=5)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Server Response: {result['message']}")
        print(f"\n👀 NOW CHECK YOUR BROWSER:")
        print(f"   1. Open Console (F12)")
        print(f"   2. Look for: '🔔 Received event: order_event'")
        print(f"   3. Look for: '📈 Order Event:'")
        print(f"   4. Look for green notification on top-right")
    else:
        print(f"❌ Error: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
