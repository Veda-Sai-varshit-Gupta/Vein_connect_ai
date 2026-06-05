import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.transfusion import Transfusion
from app.models.coordinator import Coordinator
from app.models.user import User

async def main():
    async with AsyncSessionLocal() as db:
        # Transfusion
        t_id = "ef9853ad-de01-4fd7-83f2-aeb54e5b4608"
        res = await db.execute(select(Transfusion).where(Transfusion.id == t_id))
        t = res.scalar_one_or_none()
        
        print("\n=== Transfusion Details ===")
        if t:
            print(f"ID: {t.id}")
            print(f"Patient ID: {t.patient_id}")
            print(f"Coordinator ID: {t.coordinator_id}")
            print(f"Status: {t.status}")
            print(f"Urgency: {t.urgency_level}")
            print(f"Patient Confirm: {t.patient_confirmation}")
            print(f"Coordinator Confirm: {t.coordinator_confirmation}")
        else:
            print(f"Transfusion with ID {t_id} not found.")
            
        # All coordinators
        res_c = await db.execute(select(Coordinator))
        coords = res_c.scalars().all()
        print("\n=== Coordinator Profiles ===")
        for c in coords:
            res_u = await db.execute(select(User).where(User.id == c.user_id))
            u = res_u.scalar_one_or_none()
            email = u.email if u else "Unknown"
            print(f"Coordinator ID: {c.id} | User ID: {c.user_id} | Email: {email} | Region: {c.assigned_region}")

if __name__ == "__main__":
    asyncio.run(main())
