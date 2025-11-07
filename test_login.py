import requests
import re

# Step 1: Get the login page and extract the CSRF token
login_url = 'http://127.0.0.1:5000/login'
session = requests.Session()
try:
    response = session.get(login_url, timeout=5)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"Error fetching login page: {e}")
    exit()

csrf_token_match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', response.text)

if not csrf_token_match:
    print("Could not find CSRF token")
    exit()

csrf_token = csrf_token_match.group(1)
print(f"CSRF Token: {csrf_token}")

# Step 2: Send a POST request to log in
login_data = {
    'username': 'admin',
    'password': 'admin',
    'csrf_token': csrf_token
}

try:
    response = session.post(login_url, data=login_data, timeout=5)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"Error on login request: {e}")
    exit()


# Step 3: Check if login was successful
if 'Invalid username or password' in response.text:
    print('Login failed.')
else:
    print('Login successful.')
    # Now that we are logged in, let's try to access the dashboard
    try:
        dashboard_response = session.get('http://127.0.0.1:5000/index', timeout=5)
        dashboard_response.raise_for_status()
        if 'Home' in dashboard_response.text:
            print("Successfully accessed the dashboard.")
        else:
            print("Failed to access the dashboard.")
    except requests.exceptions.RequestException as e:
        print(f"Error accessing dashboard: {e}")
