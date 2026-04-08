"""Quick test of API endpoints."""
import requests
import json

# Replace with your HF Space URL
BASE_URL = "https://your-space-url.hf.space"  # Update this!

print("Testing API endpoints...\n")

# Test 1: Health check
print("1. Testing GET /health")
response = requests.get(f"{BASE_URL}/health")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}\n")

# Test 2: Reset environment
print("2. Testing POST /reset")
response = requests.post(f"{BASE_URL}/reset", json={"task": "easy", "seed": 42})
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✅ Reset successful\n")
else:
    print(f"   ❌ Reset failed: {response.json()}\n")

# Test 3: Take action
print("3. Testing POST /step")
response = requests.post(f"{BASE_URL}/step", json={"action_type": "inspect_logs", "target": None})
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Step successful")
    print(f"   Reward: {data['reward']['total']}")
    print(f"   Done: {data['done']}\n")
else:
    print(f"   ❌ Step failed: {response.json()}\n")

# Test 4: Get state
print("4. Testing GET /state")
response = requests.get(f"{BASE_URL}/state")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✅ State retrieved successfully\n")
else:
    print(f"   ❌ State failed: {response.json()}\n")

print("✅ All API endpoints working!")
