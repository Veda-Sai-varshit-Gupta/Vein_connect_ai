import asyncio
import asyncpg
import uuid
from datetime import date, timedelta

async def create_transfusion():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/veinconnect_db")
    
    # 1. Get patient rogi
    patient = await conn.fetchrow("SELECT id, name, blood_group FROM patients WHERE name = 'rogi'")
    if not patient:
        print("Patient 'rogi' not found!")
        await conn.close()
        return
    patient_id = patient['id']
    
    # 2. Get donor Ishaan Sari (A-)
    donor = await conn.fetchrow("SELECT id, name, blood_group, user_id FROM donors WHERE name = 'Ishaan Sari'")
    if not donor:
        print("Donor 'Ishaan Sari' not found!")
        await conn.close()
        return
    donor_id = donor['id']
    
    # 3. Get first hospital
    hospital = await conn.fetchrow("SELECT id, name FROM hospitals LIMIT 1")
    if not hospital:
        print("No hospitals found!")
        await conn.close()
        return
    hospital_id = hospital['id']
    
    print(f"Patient: {patient['name']} (ID: {patient_id}) | Blood: {patient['blood_group']}")
    print(f"Donor: {donor['name']} (ID: {donor_id}) | Blood: {donor['blood_group']}")
    print(f"Hospital: {hospital['name']} (ID: {hospital_id})")
    
    # 4. Check if a transfusion already exists
    existing = await conn.fetchval("SELECT COUNT(*) FROM transfusions WHERE patient_id = $1", patient_id)
    if existing > 0:
        print("Transfusion already exists for rogi! Deleting existing ones to re-create clean...")
        await conn.execute("DELETE FROM confirmations WHERE transfusion_id IN (SELECT id FROM transfusions WHERE patient_id = $1)", patient_id)
        await conn.execute("DELETE FROM transfusions WHERE patient_id = $1", patient_id)
        
    # 5. Insert transfusion
    transfusion_id = uuid.uuid4()
    scheduled_date = date.today() + timedelta(days=14)
    await conn.execute("""
        INSERT INTO transfusions (
            id, patient_id, donor_id, hospital_id, predicted_date, scheduled_date,
            urgency_level, status, patient_confirmation, donor_confirmation,
            coordinator_confirmation, hospital_confirmation, is_emergency, created_at, updated_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, 'urgent', 'donor_confirmed', 'confirmed', 'confirmed', 'pending', 'pending', false, now(), now())
    """, transfusion_id, patient_id, donor_id, hospital_id, scheduled_date, scheduled_date)
    print(f"Transfusion request created successfully with ID {transfusion_id}!")
    
    # 6. Create confirmations for the status flow (Patient, Donor)
    # Patient confirmation
    await conn.execute("""
        INSERT INTO confirmations (id, transfusion_id, user_id, role, status, reminder_count, created_at, updated_at)
        VALUES ($1, $2, (SELECT user_id FROM patients WHERE id = $3), 'patient', 'confirmed', 0, now(), now())
    """, uuid.uuid4(), transfusion_id, patient_id)
    
    # Donor confirmation
    await conn.execute("""
        INSERT INTO confirmations (id, transfusion_id, user_id, role, status, reminder_count, created_at, updated_at)
        VALUES ($1, $2, $3, 'donor', 'confirmed', 0, now(), now())
    """, uuid.uuid4(), transfusion_id, donor['user_id'])
    
    print("Confirmations seeded successfully.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(create_transfusion())
