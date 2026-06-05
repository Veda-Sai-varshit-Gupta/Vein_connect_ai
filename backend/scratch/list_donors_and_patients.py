import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.patient import Patient
from app.models.donor import Donor
from app.models.transfusion import Transfusion

async def inspect():
    async with AsyncSessionLocal() as db:
        res_p = await db.execute(select(Patient))
        patients = res_p.scalars().all()
        print(f"--- PATIENTS ({len(patients)}) ---")
        for p in patients:
            print(f"Patient {p.name}: {p.blood_group.value if hasattr(p.blood_group, 'value') else p.blood_group} (ID: {p.id})")
            
        res_d = await db.execute(select(Donor))
        donors = res_d.scalars().all()
        print(f"\n--- DONORS ({len(donors)}) ---")
        for d in donors:
            print(f"Donor {d.name}: {d.blood_group.value if hasattr(d.blood_group, 'value') else d.blood_group} (ID: {d.id}, available: {d.is_available}, last_donation: {d.last_donation_date})")

        res_t = await db.execute(select(Transfusion))
        transfusions = res_t.scalars().all()
        print(f"\n--- TRANSFUSIONS ({len(transfusions)}) ---")
        for t in transfusions:
            print(f"Transfusion {t.id} -> Patient ID: {t.patient_id}, Donor ID: {t.donor_id}, Status: {t.status}")

if __name__ == "__main__":
    asyncio.run(inspect())
