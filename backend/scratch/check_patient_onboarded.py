import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/veinconnect_db")
    
    print("--- USERS & PATIENTS ---")
    users = await conn.fetch("SELECT id, email, role, is_onboarded FROM users WHERE role = 'patient'")
    for u in users:
        patient = await conn.fetchrow("SELECT id, name FROM patients WHERE user_id = $1", u['id'])
        print(f"User: {u['email']} | Onboarded: {u['is_onboarded']} | Profile: {patient['name'] if patient else 'MISSING'}")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check())
