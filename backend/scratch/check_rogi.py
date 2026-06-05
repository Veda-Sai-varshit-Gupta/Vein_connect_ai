import asyncio
import asyncpg

async def check_patient_data():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/veinconnect_db")
    
    # 1. Get user details
    user = await conn.fetchrow("SELECT id, email FROM users WHERE email = 'patient1@gmail.com'")
    if not user:
        print("User patient1@gmail.com not found!")
        await conn.close()
        return
    print(f"User ID: {user['id']}")
    
    # 2. Get patient details
    patient = await conn.fetchrow("SELECT id, name, blood_group FROM patients WHERE user_id = $1", user['id'])
    if not patient:
        print("Patient profile not found!")
        await conn.close()
        return
    print(f"Patient Name: {patient['name']} | ID: {patient['id']} | BG: {patient['blood_group']}")
    
    # 3. Get transfusion requests for this patient
    transfusions = await conn.fetch("SELECT id, status, donor_id, hospital_id, predicted_date, scheduled_date FROM transfusions WHERE patient_id = $1", patient['id'])
    print(f"\nFound {len(transfusions)} transfusion(s) for patient:")
    for t in transfusions:
        print(f"Transfusion ID: {t['id']} | Status: {t['status']} | Donor ID: {t['donor_id']} | Hospital ID: {t['hospital_id']}")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_patient_data())
