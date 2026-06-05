import asyncio
import asyncpg

async def clear_database():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/veinconnect_db")
    print("Connected to PostgreSQL database.")

    # Fetch all tables in the public schema except alembic_version
    rows = await conn.fetch("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_name != 'alembic_version'
    """)
    tables = [row['table_name'] for row in rows]

    if not tables:
        print("No tables found in the database to clear.")
        await conn.close()
        return

    print(f"Found {len(tables)} tables to clear: {', '.join(tables)}")

    # Truncate tables with CASCADE to handle foreign key dependencies and RESTART IDENTITY to reset sequences
    truncate_query = f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE;"
    
    try:
        await conn.execute(truncate_query)
        print("\nSuccessfully cleared all values from all tables and reset serial sequences.")
    except Exception as e:
        print(f"\nError clearing tables: {e}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(clear_database())
