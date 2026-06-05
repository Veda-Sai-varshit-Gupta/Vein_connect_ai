import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from sqlalchemy import update
from app.models.transfusion import Transfusion

async def main():
    async with AsyncSessionLocal() as db:
        t_id = "ef9853ad-de01-4fd7-83f2-aeb54e5b4608"
        coord_id = "50d2f3fe-b262-48c8-a888-afeafd9e33cf"
        
        await db.execute(
            update(Transfusion)
            .where(Transfusion.id == t_id)
            .values(coordinator_id=coord_id)
        )
        await db.commit()
        print(f"Successfully reassigned Transfusion {t_id} to Coordinator {coord_id} (coordinator@gmail.com)!")

if __name__ == "__main__":
    asyncio.run(main())
