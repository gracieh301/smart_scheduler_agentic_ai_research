"""
Simple test script for Flask endpoints.
Run this to verify all endpoints are working.
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health check endpoint"""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"  Error: {e}")
        return False

def test_chat():
    """Test chat endpoint"""
    print("\nTesting /chat endpoint...")
    try:
        data = {
            "message": "Hello, can you help me?",
            "user_id": "test_user_001"
        }
        response = requests.post(
            f"{BASE_URL}/chat",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print(f"  Status: {response.status_code}")
        print(f"  Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code in [200, 503]  # 503 if CrewAI not available
    except Exception as e:
        print(f"  Error: {e}")
        return False

def test_get_plan():
    """Test get plan endpoint"""
    print("\nTesting /plan endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/plan?user_id=test_user_001")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code in [200, 404]  # 404 if no plan exists
    except Exception as e:
        print(f"  Error: {e}")
        return False

def test_update_mastery():
    """Test update mastery endpoint"""
    print("\nTesting /update_mastery endpoint...")
    try:
        data = {
            "user_id": "test_user_001",
            "topic": "Neural Networks",
            "mastery_level": 0.7,
            "confidence_score": 0.8,
            "notes": "Test mastery update"
        }
        response = requests.post(
            f"{BASE_URL}/update_mastery",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print(f"  Status: {response.status_code}")
        print(f"  Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"  Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Testing Smart Scheduler Flask Endpoints")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print("\nMake sure the Flask server is running!")
    print("Start it with: python backend/app.py\n")
    
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Chat", test_chat()))
    results.append(("Get Plan", test_get_plan()))
    results.append(("Update Mastery", test_update_mastery()))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")

