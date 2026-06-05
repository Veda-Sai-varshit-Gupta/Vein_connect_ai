import asyncio
import asyncpg

async def list_users():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/veinconnect_db")
    
    print("--- USERS ---")
    users = await conn.fetch("SELECT id, email, role, is_active FROM users")
    for u in users:
        print(f"User: {u['email']} | Role: {u['role']} | Active: {u['is_active']} | ID: {u['id']}")
        
    print("\n--- DONORS ---")
    donors = await conn.fetch("SELECT id, user_id, name, blood_group FROM donors")
    for d in donors:
        print(f"Donor: {d['name']} | User ID: {d['user_id']} | ID: {d['id']}")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(list_users())
