import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from sqlalchemy import select, update
from app.models.donor import Donor
from app.models.enums import BloodGroup
from app.services.scheduling_service import SchedulingService

async def test_success():
    async with AsyncSessionLocal() as db:
        # Find donor
        res_d = await db.execute(select(Donor))
        donor = res_d.scalars().first()
        if not donor:
            print("No donors found in DB, cannot run success test.")
            return

        original_bg = donor.blood_group
        
        # We have a transfusion for Patient A+ (transfusion ID: a799fd24-b956-4eb8-bf40-243593a407e0)
        transfusion_id = "a799fd24-b956-4eb8-bf40-243593a407e0"
        
        # 1. Update donor to A+ (exact match)
        print(f"\n1. Setting donor {donor.name} blood group to A+ (exact match for patient)...")
        await db.execute(
            update(Donor)
            .where(Donor.id == donor.id)
            .values(blood_group=BloodGroup.A_POS)
        )
        await db.commit()
        
        # Clear database session cache
        db.expire_all()
        
        # Fetch matches
        service = SchedulingService()
        matches = await service.get_donor_matches(db, transfusion_id)
        print(f"Found {len(matches)} matches:")
        for m in matches:
            print(f" - Donor: {m.donor_name}, blood group: {m.blood_group}, score: {m.match_score}")
            
        assert len(matches) > 0, "Error: AI Matcher should have matched the same blood group donor!"
        assert matches[0].blood_group == "A+", f"Error: Matched donor has incorrect blood group {matches[0].blood_group}!"
        print("SUCCESS: Donor matched successfully when blood group is exactly the same!")

        # 2. Reset donor back to A- (mismatch)
        print(f"\n2. Setting donor {donor.name} blood group back to {original_bg.value} (mismatch)...")
        await db.execute(
            update(Donor)
            .where(Donor.id == donor.id)
            .values(blood_group=original_bg)
        )
        await db.commit()
        
        db.expire_all()
        
        # Fetch matches again
        matches_after = await service.get_donor_matches(db, transfusion_id)
        print(f"Found {len(matches_after)} matches after resetting to mismatch:")
        assert len(matches_after) == 0, "Error: AI Matcher should NOT have matched a different blood group donor!"
        print("SUCCESS: Matching engine correctly returned 0 recommendations for mismatched blood group!")

if __name__ == "__main__":
    asyncio.run(test_success())
