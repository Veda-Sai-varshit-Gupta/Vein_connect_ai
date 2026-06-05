import httpx
import random
import uuid

def test():
    # Register a new patient user
    email = f"testpatient_{random.randint(10000, 99999)}@veinconnect.com"
    phone = f"98765{random.randint(10000, 99999)}"
    signup_payload = {
        "email": email,
        "phone": phone,
        "password": "Password123",
        "role": "patient"
    }
    r = httpx.post("http://127.0.0.1:8000/api/v1/auth/signup", json=signup_payload)
    print("Signup response status:", r.status_code)
    if r.status_code != 201:
        print("Signup failed:", r.text)
        return
        
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Query an expense for a non-existent donation ID
    fake_donation_id = str(uuid.uuid4())
    print(f"Requesting expense for fake donation ID: {fake_donation_id}")
    res = httpx.get(f"http://127.0.0.1:8000/api/v1/expenses/donation/{fake_donation_id}", headers=headers)
    
    print("Status code:", res.status_code)
    print("Response JSON/Text:", res.text)
    
    if res.status_code == 200 and res.json() is None:
        print("SUCCESS: Endpoint returned 200 OK and null/None value!")
    else:
        print("FAILED: Expected 200 OK and null.")

if __name__ == "__main__":
    test()
