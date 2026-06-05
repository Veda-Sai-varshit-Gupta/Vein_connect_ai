import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uuid
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal
import asyncpg

async def test_matching_flow():
    # Connect to the DB
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/veinconnect_db")
    print("Connected to PostgreSQL database.")

    # Clean up any existing test records first
    await conn.execute("DELETE FROM users WHERE email LIKE 'test_%'")

    # 1. Setup clean mock environment
    print("\n--- Phase 1: Setting up mock profiles ---")
    user_p = uuid.uuid4()
    user_d1 = uuid.uuid4()
    user_d2 = uuid.uuid4()
    user_d3 = uuid.uuid4()
    user_d4 = uuid.uuid4()
    user_h = uuid.uuid4()

    # Create Users
    for i, (u_id, role, email) in enumerate([
        (user_p, "patient", "test_p@veinconnect.com"),
        (user_d1, "donor", "test_d1@veinconnect.com"),
        (user_d2, "donor", "test_d2@veinconnect.com"),
        (user_d3, "donor", "test_d3@veinconnect.com"),
        (user_d4, "donor", "test_d4@veinconnect.com"),
        (user_h, "hospital", "test_h@veinconnect.com"),
    ]):
        phone = f"+91999999990{i}"
        await conn.execute("""
            INSERT INTO users (id, email, phone, password_hash, role, is_active, is_verified, created_at, updated_at)
            VALUES ($1, $2, $3, 'hash', $4, true, true, now(), now())
            ON CONFLICT DO NOTHING
        """, u_id, email, phone, role)
        # Create wallet
        await conn.execute("""
            INSERT INTO wallets (id, user_id, balance, total_earned, total_spent, currency, created_at, updated_at)
            VALUES ($1, $2, 0.00, 0.00, 0.00, 'INR', now(), now())
            ON CONFLICT DO NOTHING
        """, uuid.uuid4(), u_id)

    # Create Patient
    patient_id = uuid.uuid4()
    await conn.execute("""
        INSERT INTO patients (id, user_id, name, age, gender, address, city, state, blood_group, thalassemia_type, avg_transfusion_interval_days, data_sharing_consent, emergency_consent, created_at, updated_at)
        VALUES ($1, $2, 'Test Patient', 10, 'male', 'Address', 'Chennai', 'TN', 'B_POS', 'major', 21, true, true, now(), now())
    """, patient_id, user_p)
    print("Mock patient created (B+).")

    # Create Hospital
    hospital_id = uuid.uuid4()
    await conn.execute("""
        INSERT INTO hospitals (id, user_id, name, registration_number, address, city, state, total_transfusion_beds, total_transfusion_chairs, emergency_capacity, is_active, created_at, updated_at)
        VALUES ($1, $2, 'Test Hospital', 'REG-TEST', 'Address', 'Chennai', 'TN', 5, 5, 1, true, now(), now())
    """, hospital_id, user_h)
    print("Mock hospital created.")

    # Create Donors
    d1_id = uuid.uuid4() # Exact match, eligible, 100% rel, ₹0 reimbursement, cert 1 month old
    d2_id = uuid.uuid4() # Compatible match (O+), eligible, 80% rel, ₹500 reimbursement, cert 3 months old
    d3_id = uuid.uuid4() # Exact match, certificate 7 months old (expired) -> INELIGIBLE
    d4_id = uuid.uuid4() # Exact match, eligible, 90% rel, ₹1200 reimbursement (high)

    now_tz = datetime.now(timezone.utc)
    cert_active_1 = now_tz - timedelta(days=30)
    cert_active_3 = now_tz - timedelta(days=90)
    cert_expired_7 = now_tz - timedelta(days=210)

    # Donor 1
    await conn.execute("""
        INSERT INTO donors (id, user_id, name, age, gender, blood_group, total_donations, reliability_score, max_travel_distance_km, is_available, medical_clearance_url, medical_clearance_at, demanded_reimbursement, created_at, updated_at)
        VALUES ($1, $2, 'Donor A (Premium)', 25, 'male', 'B_POS', 5, 100.00, 25, true, 'url', $3, 0.00, now(), now())
    """, d1_id, user_d1, cert_active_1)

    # Donor 2
    await conn.execute("""
        INSERT INTO donors (id, user_id, name, age, gender, blood_group, total_donations, reliability_score, max_travel_distance_km, is_available, medical_clearance_url, medical_clearance_at, demanded_reimbursement, created_at, updated_at)
        VALUES ($1, $2, 'Donor B (O+ Compatible)', 28, 'male', 'O_POS', 2, 80.00, 25, true, 'url', $3, 500.00, now(), now())
    """, d2_id, user_d2, cert_active_3)

    # Donor 3
    await conn.execute("""
        INSERT INTO donors (id, user_id, name, age, gender, blood_group, total_donations, reliability_score, max_travel_distance_km, is_available, medical_clearance_url, medical_clearance_at, demanded_reimbursement, created_at, updated_at)
        VALUES ($1, $2, 'Donor C (Expired Clearance)', 30, 'female', 'B_POS', 0, 50.00, 25, true, 'url', $3, 0.00, now(), now())
    """, d3_id, user_d3, cert_expired_7)

    # Donor 4
    await conn.execute("""
        INSERT INTO donors (id, user_id, name, age, gender, blood_group, total_donations, reliability_score, max_travel_distance_km, is_available, medical_clearance_url, medical_clearance_at, demanded_reimbursement, created_at, updated_at)
        VALUES ($1, $2, 'Donor D (High Reimbursement)', 22, 'male', 'B_POS', 1, 90.00, 25, true, 'url', $3, 1200.00, now(), now())
    """, d4_id, user_d4, cert_active_1)

    print("Mock donors setup successfully.")

    # 2. Run Matching Engine & Assert Results
    print("\n--- Phase 2: Testing Matching Logic ---")
    from app.ai.matcher import DonorMatchingEngine
    
    # Reload donors from DB
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    engine = create_async_engine("postgresql+asyncpg://postgres:password@localhost:5432/veinconnect_db")
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        from app.models.donor import Donor
        from sqlalchemy import select
        res = await session.execute(select(Donor).where(Donor.id.in_([d1_id, d2_id, d3_id, d4_id])))
        db_donors = list(res.scalars().all())

        matcher = DonorMatchingEngine()
        matches = matcher.rank_donors(
            candidates=db_donors,
            patient_blood_group="B+",
            hospital_lat=13.0827,
            hospital_lng=80.2707,
            response_likelihoods={d1_id: 0.9, d2_id: 0.8, d3_id: 0.5, d4_id: 0.75},
            friendship_scores={d1_id: 50.0, d2_id: 0.0, d3_id: 0.0, d4_id: 0.0},
            previous_donations_counts={d1_id: 1, d2_id: 0, d3_id: 0, d4_id: 0},
            is_emergency=False,
        )

        print(f"Total Ranked Matches: {len(matches)}")
        for m in matches:
            print(f"Rank {m.rank}: {m.donor_name} | Score: {m.match_score} | Eligible: {m.is_eligible} | Reason: {m.reason} | Reimbursement Demanded: Rs.{m.demanded_reimbursement}")

        # Assertions
        assert matches[0].donor_id == d1_id, "Donor A (Premium) should be rank 1"
        assert [m for m in matches if m.donor_id == d3_id][0].is_eligible == False, "Donor C (Expired) should be ineligible"
        
        # Test Fair Reimbursement Score decay
        # Donor D demands Rs.1200, so their Fair Reimbursement Score should be 0.0
        # Donor B demands Rs.500, score should be 50.0
        # Donor A demands Rs.0, score should be 100.0
        d1_match = [m for m in matches if m.donor_id == d1_id][0]
        d2_match = [m for m in matches if m.donor_id == d2_id][0]
        d4_match = [m for m in matches if m.donor_id == d4_id][0]
        
        assert d1_match.score_breakdown["fair_reimbursement"] == 100.0
        assert d2_match.score_breakdown["fair_reimbursement"] == 50.0
        assert d4_match.score_breakdown["fair_reimbursement"] == 0.0
        print("Scoring mathematical rules verified successfully!")

    # 3. Test dynamic reliability update lifecycles
    print("\n--- Phase 3: Testing Dynamic Reliability Lifecycle ---")
    
    # Create a predicted transfusion
    transfusion_id = uuid.uuid4()
    await conn.execute("""
        INSERT INTO transfusions (id, patient_id, hospital_id, predicted_date, urgency_level, status, patient_confirmation, donor_confirmation, coordinator_confirmation, hospital_confirmation, is_emergency, created_at, updated_at)
        VALUES ($1, $2, $3, current_date, 'routine', 'predicted', 'pending', 'pending', 'pending', 'pending', false, now(), now())
    """, transfusion_id, patient_id, hospital_id)
    print("Predicted transfusion created.")

    # Coordinator assigns donor 1
    await conn.execute("""
        UPDATE transfusions SET donor_id = $1, status = 'matching_donors' WHERE id = $2
    """, d1_id, transfusion_id)
    print("Donor A assigned by coordinator.")

    # Donor confirms (using ConfirmationService)
    async with async_session() as session:
        from app.services.confirmation_service import ConfirmationService
        from app.models.enums import UserRole
        conf_service = ConfirmationService()
        await conf_service.confirm(session, transfusion_id, user_d1, UserRole.donor)
        await session.commit()
    print("Donor A confirmed transfusion (Donation should be scheduled, reliability updated).")

    # Verify donation record created
    donation = await conn.fetchrow("SELECT * FROM donations WHERE transfusion_id = $1 AND donor_id = $2", transfusion_id, d1_id)
    assert donation is not None, "Donation record should be created"
    assert donation["status"] == "scheduled", "Donation status should be scheduled"
    print("Scheduled donation record verified.")

    # Mark completed (using TransfusionService)
    # Move transfusion to in_progress first
    await conn.execute("UPDATE transfusions SET status = 'in_progress' WHERE id = $1", transfusion_id)
    
    async with async_session() as session:
        from app.services.transfusion_service import TransfusionService
        from app.schemas.transfusion import TransfusionComplete
        t_service = TransfusionService()
        await t_service.mark_completed(session, transfusion_id, TransfusionComplete(actual_date=date.today(), notes="Successfully donated"))
        await session.commit()
    print("Transfusion marked completed by hospital.")

    # Confirm completion for patient and donor to achieve consensus
    async with async_session() as session:
        from app.services.confirmation_service import ConfirmationService
        from app.models.enums import UserRole
        conf_service = ConfirmationService()
        await conf_service.confirm_completion(session, transfusion_id, user_p, UserRole.patient, "Confirming completion as patient")
        await conf_service.confirm_completion(session, transfusion_id, user_d1, UserRole.donor, "Confirming completion as donor")
        await session.commit()
    print("Consensus achieved, transfusion completed.")

    # Verify donation status became completed and donor's reliability recalculated
    donation = await conn.fetchrow("SELECT * FROM donations WHERE transfusion_id = $1 AND donor_id = $2", transfusion_id, d1_id)
    assert donation["status"] == "completed", "Donation status should be completed"
    
    donor_d1 = await conn.fetchrow("SELECT total_donations, reliability_score FROM donors WHERE id = $1", d1_id)
    print(f"Donor A final reliability score: {donor_d1['reliability_score']}% (total donations: {donor_d1['total_donations']})")
    
    # 4. Clean up mock environment
    print("\n--- Phase 4: Cleaning up mock profiles ---")
    await conn.execute("DELETE FROM completion_confirmations WHERE transfusion_id = $1", transfusion_id)
    await conn.execute("DELETE FROM donations WHERE donor_id IN ($1, $2, $3, $4)", d1_id, d2_id, d3_id, d4_id)
    await conn.execute("DELETE FROM confirmations WHERE user_id IN ($1, $2, $3, $4)", user_d1, user_d2, user_d3, user_d4)
    await conn.execute("DELETE FROM transfusions WHERE patient_id = $1", patient_id)
    await conn.execute("DELETE FROM donors WHERE id IN ($1, $2, $3, $4)", d1_id, d2_id, d3_id, d4_id)
    await conn.execute("DELETE FROM patients WHERE id = $1", patient_id)
    await conn.execute("DELETE FROM hospitals WHERE id = $1", hospital_id)
    await conn.execute("DELETE FROM wallets WHERE user_id IN ($1, $2, $3, $4, $5, $6)", user_p, user_d1, user_d2, user_d3, user_d4, user_h)
    await conn.execute("DELETE FROM users WHERE id IN ($1, $2, $3, $4, $5, $6)", user_p, user_d1, user_d2, user_d3, user_d4, user_h)
    await conn.close()
    
    print("\nAll integration tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_matching_flow())
