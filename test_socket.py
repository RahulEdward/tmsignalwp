import requests
import json

# Test Socket.IO endpoint
url = "http://127.0.0.1:5000/api/test/socket"

# Test data
test_cases = [
    {
        "symbol": "RELIANCE",
        "action": "BUY",
        "orderid": "TEST001"
    },
    {
        "symbol": "INFY",
        "action": "SELL",
        "orderid": "TEST002"
    },
    {
        "symbol": "TCS",
        "action": "BUY",
        "orderid": "TEST003"
    }
]

print("🧪 Starting Socket.IO Signal Tests...\n")
print("=" * 60)

for i, test_data in enumerate(test_cases, 1):
    print(f"\n📤 Test {i}: Sending signal for {test_data['action']} {test_data['symbol']}")
    print(f"   Order ID: {test_data['orderid']}")
    
    try:
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Status: {result['status']}")
            print(f"   📨 Message: {result['message']}")
            print(f"   📊 Event Data: {result['event_data']}")
            print(f"   👀 Check your browser for the notification!")
        else:
            print(f"   ❌ Error: Status code {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection Error: Server not running at {url}")
        print(f"   💡 Make sure to start the server with: python app.py")
        break
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

print("\n" + "=" * 60)
print("\n✨ Test completed!")
print("📝 Check your browser console and dashboard for notifications")
print("🔍 Server logs should show: '🔔 Emitting order_event via SocketIO'")
