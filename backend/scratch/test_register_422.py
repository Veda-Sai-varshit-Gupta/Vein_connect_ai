import httpx
import json
import random

def test():
    # Register a new patient user
    email = f"testpatient_{random.randint(10000, 99999)}@veinconnect.com"
    signup_payload = {
        "email": email,
        "phone": "9876543210",
        "password": "Password123",
        "role": "patient"
    }
    r = httpx.post("http://127.0.0.1:8000/api/v1/auth/signup", json=signup_payload)
    print("Signup response status:", r.status_code)
    if r.status_code != 201:
        print("Signup failed:", r.text)
        return
        
    token = r.json()["access_token"]
    
    # Send a mock registration payload matching the frontend exactly
    payload = {
        "name": "Test Patient",
        "age": 12,
        "gender": "male",
        "address": "123 Test Street",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "blood_group": "B+",
        "thalassemia_type": "major",
        "avg_transfusion_interval_days": 21,
        "last_transfusion_date": None,
        "emergency_contact_name": "Test Contact",
        "emergency_contact_phone": "9876543210",
        "data_sharing_consent": True,
        "emergency_consent": True,
        "hospital_preferences": [
            {"hospital_id": "fe167895-afd0-444f-9115-1cd1ea32fa99", "preference_order": 1} # Dummy UUID
        ]
    }
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    res = httpx.post("http://127.0.0.1:8000/api/v1/patients/register", json=payload, headers=headers)
    print("Register status:", res.status_code)
    print("Register body:")
    print(json.dumps(res.json(), indent=2))

if __name__ == "__main__":
    test()
