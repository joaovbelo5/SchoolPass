import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

token = os.getenv('TELEGRAM_TOKEN')

print(f"Token loaded: {token}")

if not token:
    print("❌ Error: TELEGRAM_TOKEN not found in environment variables.")
    exit(1)

if "'" in token or '"' in token:
    print("⚠️ Warning: Token contains quotes. This might be the issue.")
    print(f"Raw token value: >{token}<")
else:
    print("✅ Token format looks clean (no quotes).")

# Test connection
url = f"https://api.telegram.org/bot{token}/getMe"
print(f"Testing connection to: {url.replace(token, '******')}")

try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Connection successful! Bot is working.")
        user_data = response.json().get('result', {})
        print(f"Bot Name: {user_data.get('first_name')}")
        print(f"Bot Username: @{user_data.get('username')}")
    else:
        print("❌ Connection failed. Check token or internet connection.")
except Exception as e:
    print(f"❌ Exception during request: {e}")
