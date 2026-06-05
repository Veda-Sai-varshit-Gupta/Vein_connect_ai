import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import asyncpg

async def test_rewards_conversion():
    # Connect to the DB
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/veinconnect_db")
    print("Connected to PostgreSQL database.")

    # Clean up any existing test records first
    await conn.execute("DELETE FROM users WHERE email = 'test_rew_donor@veinconnect.com'")

    print("\n--- Setup mock donor profile ---")
    user_id = uuid.uuid4()
    donor_id = uuid.uuid4()

    # Create User without wallet to verify on-the-fly wallet creation
    await conn.execute("""
        INSERT INTO users (id, email, phone, password_hash, role, is_active, is_verified, created_at, updated_at)
        VALUES ($1, 'test_rew_donor@veinconnect.com', '+919999999099', 'hash', 'donor', true, true, now(), now())
    """, user_id)

    # Create Donor Profile
    await conn.execute("""
        INSERT INTO donors (id, user_id, name, age, gender, blood_group, total_donations, reliability_score, max_travel_distance_km, is_available, medical_clearance_url, medical_clearance_at, demanded_reimbursement, created_at, updated_at)
        VALUES ($1, $2, 'Rewards Test Donor', 27, 'male', 'B_POS', 0, 100.00, 25, true, 'url', now(), 0.00, now(), now())
    """, donor_id, user_id)
    print("Mock donor created.")

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    engine = create_async_engine("postgresql+asyncpg://postgres:password@localhost:5432/veinconnect_db")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        from app.services.reward_service import RewardService
        from app.models.enums import RewardType
        
        service = RewardService()

        # 1. Award mock points to donor
        # Award 1200 points
        print("\n--- Awarding Points ---")
        from app.repositories.reward_repo import RewardRepository
        reward_repo = RewardRepository()
        
        await reward_repo.create(session, {
            "donor_id": donor_id,
            "type": RewardType.donation,
            "points": 1000,
            "description": "First donation bonus"
        })
        await reward_repo.create(session, {
            "donor_id": donor_id,
            "type": RewardType.consistency_bonus,
            "points": 200,
            "description": "Consistency milestone bonus"
        })
        await session.commit()
        print("Awarded 1200 points to donor.")

        # 2. Get Summary and verify fields
        print("\n--- Testing Rewards Summary ---")
        summary = await service.get_summary(session, donor_id)
        print(f"Summary: {summary}")
        
        assert summary["total_points"] == 1200, f"Expected 1200 points, got {summary['total_points']}"
        assert summary["tier"] == "Gold", f"Expected Gold tier, got {summary['tier']}"
        assert summary["tier_level"] == 3, f"Expected tier level 3, got {summary['tier_level']}"
        assert summary["points_to_next_tier"] == 800, f"Expected 800 points to next tier, got {summary['points_to_next_tier']}"
        assert summary["next_tier"] == "Platinum", f"Expected next tier Platinum, got {summary['next_tier']}"
        print("Summary fields verified successfully.")

        # 3. Test Conversion
        print("\n--- Testing Point Conversion ---")
        conversion_res = await service.convert_points(session, donor_id, 1000)
        await session.commit()
        print(f"Conversion result: {conversion_res}")
        
        assert conversion_res["converted_points"] == 1000
        assert conversion_res["inr_credited"] == 500.0
        print("Conversion return values verified successfully.")

        # 4. Verify Wallet and Transaction existence
        print("\n--- Verifying Wallet and Transaction ---")
        from app.repositories.wallet_repo import WalletRepository
        wallet_repo = WalletRepository()
        wallet = await wallet_repo.get_by_user_id(session, user_id)
        assert wallet is not None, "Wallet should have been created on-the-fly"
        assert wallet.balance == Decimal("500.00"), f"Expected wallet balance ₹500.00, got ₹{wallet.balance}"
        assert wallet.total_earned == Decimal("500.00"), f"Expected total earned ₹500.00, got ₹{wallet.total_earned}"
        print("Wallet balance and totals verified successfully.")

        txns = await wallet_repo.get_transactions(session, wallet.id)
        assert len(txns) == 1, f"Expected 1 transaction, got {len(txns)}"
        assert txns[0].amount == Decimal("500.00")
        assert txns[0].description == "1000 reward points converted to ₹500.0"
        print("Wallet transaction log verified successfully.")

        # 5. Verify Summary updates after conversion
        print("\n--- Verifying Updated Summary ---")
        summary_updated = await service.get_summary(session, donor_id)
        print(f"Updated Summary: {summary_updated}")
        
        assert summary_updated["total_points"] == 200, f"Expected 200 points remaining, got {summary_updated['total_points']}"
        assert summary_updated["tier"] == "Bronze", f"Expected Bronze tier, got {summary_updated['tier']}"
        assert summary_updated["tier_level"] == 1, f"Expected tier level 1, got {summary_updated['tier_level']}"
        assert summary_updated["points_to_next_tier"] == 300, f"Expected 300 points to next tier, got {summary_updated['points_to_next_tier']}"
        assert summary_updated["next_tier"] == "Silver", f"Expected next tier Silver, got {summary_updated['next_tier']}"
        print("Updated summary fields verified successfully.")

    # Clean up test accounts
    await conn.execute("DELETE FROM users WHERE email = 'test_rew_donor@veinconnect.com'")
    await conn.close()
    print("\nAll rewards conversion integration tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_rewards_conversion())
