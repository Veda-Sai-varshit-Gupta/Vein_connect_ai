import asyncio
import asyncpg

async def alter_table():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/veinconnect_db")
    print("Altering donors table...")
    await conn.execute("""
        ALTER TABLE donors ADD COLUMN IF NOT EXISTS medical_clearance_url VARCHAR(500) NULL;
        ALTER TABLE donors ADD COLUMN IF NOT EXISTS medical_clearance_at TIMESTAMP WITH TIME ZONE NULL;
        ALTER TABLE donors ADD COLUMN IF NOT EXISTS demanded_reimbursement NUMERIC(10, 2) DEFAULT 0.00 NOT NULL;
    """)
    print("Donors table altered successfully.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(alter_table())
