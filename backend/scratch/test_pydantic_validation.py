import sys
import os

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.patient import PatientCreate
from pydantic import ValidationError

def test_validation():
    payloads = [
        # 1. Valid payload
        {
            "name": "Rahul Sharma",
            "age": 12,
            "gender": "male",
            "address": "123 Test Street",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "blood_group": "B+",
            "thalassemia_type": "major",
            "avg_transfusion_interval_days": 21,
            "last_transfusion_date": None,
            "emergency_contact_name": "Suresh Sharma",
            "emergency_contact_phone": "9876543210",
            "data_sharing_consent": True,
            "emergency_consent": True,
            "hospital_preferences": [
                {"hospital_id": "fe167895-afd0-444f-9115-1cd1ea32fa99", "preference_order": 1}
            ]
        },
        # 2. String representation for date
        {
            "name": "Rahul Sharma",
            "age": 12,
            "gender": "male",
            "address": "123 Test Street",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "blood_group": "B+",
            "thalassemia_type": "major",
            "avg_transfusion_interval_days": 21,
            "last_transfusion_date": "2026-06-04",
            "emergency_contact_name": "Suresh Sharma",
            "emergency_contact_phone": "9876543210",
            "data_sharing_consent": True,
            "emergency_consent": True,
            "hospital_preferences": [
                {"hospital_id": "fe167895-afd0-444f-9115-1cd1ea32fa99", "preference_order": 1}
            ]
        },
        # 3. What if preferred_hospitals are strings like hosp-1?
        {
            "name": "Rahul Sharma",
            "age": 12,
            "gender": "male",
            "address": "123 Test Street",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "blood_group": "B+",
            "thalassemia_type": "major",
            "avg_transfusion_interval_days": 21,
            "last_transfusion_date": None,
            "emergency_contact_name": "Suresh Sharma",
            "emergency_contact_phone": "9876543210",
            "data_sharing_consent": True,
            "emergency_consent": True,
            "hospital_preferences": [
                {"hospital_id": "hosp-1", "preference_order": 1}
            ]
        },
        # 4. What if date is empty string?
        {
            "name": "Rahul Sharma",
            "age": 12,
            "gender": "male",
            "address": "123 Test Street",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "blood_group": "B+",
            "thalassemia_type": "major",
            "avg_transfusion_interval_days": 21,
            "last_transfusion_date": "",
            "emergency_contact_name": "Suresh Sharma",
            "emergency_contact_phone": "9876543210",
            "data_sharing_consent": True,
            "emergency_consent": True,
            "hospital_preferences": [
                {"hospital_id": "fe167895-afd0-444f-9115-1cd1ea32fa99", "preference_order": 1}
            ]
        }
    ]

    for i, p in enumerate(payloads, 1):
        try:
            PatientCreate.model_validate(p)
            print(f"Payload {i}: VALID")
        except ValidationError as e:
            print(f"Payload {i}: INVALID")
            print("Errors:")
            for err in e.errors():
                print(f" - {err['loc']}: {err['msg']} ({err['type']})")

if __name__ == "__main__":
    test_validation()
