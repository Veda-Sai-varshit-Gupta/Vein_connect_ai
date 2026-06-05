import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.services.scheduling_service import SchedulingService
from sqlalchemy import select
from app.models.transfusion import Transfusion
from app.models.patient import Patient

async def test_blood_group():
    async with AsyncSessionLocal() as db:
        # Fetch all transfusions
        res = await db.execute(select(Transfusion).limit(10))
        transfusions = res.scalars().all()
        if not transfusions:
            print("No transfusions in DB, cannot test.")
            return

        service = SchedulingService()
        total_checks = 0
        for t in transfusions:
            patient = await db.get(Patient, t.patient_id)
            if not patient:
                continue
            
            p_bg = patient.blood_group.value if hasattr(patient.blood_group, 'value') else patient.blood_group
            print(f"\nTransfusion {t.id} Patient blood group: {p_bg}")
            
            matches = await service.get_donor_matches(db, t.id)
            print(f"Found {len(matches)} AI-recommended matches:")
            for m in matches:
                print(f" - Donor: {m.donor_name}, blood group: {m.blood_group}, match score: {m.match_score}")
                # Assert same blood group
                if m.blood_group != p_bg:
                    print(f"ERROR: Donor blood group {m.blood_group} is different from patient blood group {p_bg}!")
                    sys.exit(1)
                total_checks += 1
            print("All matches for this transfusion have the exact same blood group!")
        print(f"\nSuccessfully validated {total_checks} donor matches. All of them match the patient's blood group exactly.")

if __name__ == "__main__":
    asyncio.run(test_blood_group())
