import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/veinconnect_db")
    print("Connected to PostgreSQL database.")
    
    # Drop constraint
    await conn.execute("ALTER TABLE rewards DROP CONSTRAINT IF EXISTS ck_rewards_points_positive")
    print("Check constraint 'ck_rewards_points_positive' dropped from 'rewards' table.")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
