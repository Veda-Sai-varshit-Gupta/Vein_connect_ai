import asyncio
import asyncpg
import uuid

async def create_profile():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/veinconnect_db")
    user_id = '0e8c34a7-8112-4f2b-8f52-05b44f3b25c2'
    
    # Check if donor profile already exists
    exists = await conn.fetchval("SELECT COUNT(*) FROM donors WHERE user_id = $1", user_id)
    if exists > 0:
        print("Donor profile already exists!")
    else:
        donor_id = uuid.uuid4()
        await conn.execute("""
            INSERT INTO donors (
                id, user_id, name, age, gender, blood_group, 
                total_donations, reliability_score, max_travel_distance_km, 
                is_available, upi_id, demanded_reimbursement, created_at, updated_at
            )
            VALUES ($1, $2, 'Test Donor', 25, 'male', 'B_POS', 5, 85.00, 25, true, 'donor@upi', 0.00, now(), now())
        """, donor_id, user_id)
        print(f"Donor profile created successfully with ID {donor_id} for User ID {user_id}!")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(create_profile())
