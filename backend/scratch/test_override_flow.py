import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uuid
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal
import asyncpg

async def test_override_flow():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/veinconnect_db")
    print("Connected to PostgreSQL database.")

    # Clean up test accounts
    await conn.execute("DELETE FROM users WHERE email LIKE 'test_over_%'")

    print("\n--- Step 1: Setting up mock profiles ---")
    user_p = uuid.uuid4()
    user_d1 = uuid.uuid4()
    user_d2 = uuid.uuid4()
    user_d3 = uuid.uuid4()
    user_h1 = uuid.uuid4()
    user_h2 = uuid.uuid4()

    # Create Users
    roles = [
        (user_p, "patient", "test_over_p@veinconnect.com"),
        (user_d1, "donor", "test_over_d1@veinconnect.com"),
        (user_d2, "donor", "test_over_d2@veinconnect.com"),
        (user_d3, "donor", "test_over_d3@veinconnect.com"),
        (user_h1, "hospital", "test_over_h1@veinconnect.com"),
        (user_h2, "hospital", "test_over_h2@veinconnect.com"),
    ]
    for i, (u_id, role, email) in enumerate(roles):
        phone = f"+9199999999{i}"
        await conn.execute("""
            INSERT INTO users (id, email, phone, password_hash, role, is_active, is_verified, created_at, updated_at)
            VALUES ($1, $2, $3, 'hash', $4, true, true, now(), now())
        """, u_id, email, phone, role)
        # Create wallet
        await conn.execute("""
            INSERT INTO wallets (id, user_id, balance, total_earned, total_spent, currency, created_at, updated_at)
            VALUES ($1, $2, 0.00, 0.00, 0.00, 'INR', now(), now())
        """, uuid.uuid4(), u_id)

    # Create Patient
    patient_id = uuid.uuid4()
    await conn.execute("""
        INSERT INTO patients (id, user_id, name, age, gender, address, city, state, blood_group, thalassemia_type, avg_transfusion_interval_days, data_sharing_consent, emergency_consent, created_at, updated_at)
        VALUES ($1, $2, 'Test Patient', 25, 'male', 'Address', 'ChennaiOver', 'TN', 'B_POS', 'major', 21, true, true, now(), now())
    """, patient_id, user_p)

    # Create Hospitals
    h1_id = uuid.uuid4()
    h2_id = uuid.uuid4()
    await conn.execute("""
        INSERT INTO hospitals (id, user_id, name, registration_number, address, city, state, total_transfusion_beds, total_transfusion_chairs, emergency_capacity, is_active, created_at, updated_at)
        VALUES ($1, $2, 'Hospital Preferred', 'REG-HP', 'Address', 'ChennaiOver', 'TN', 5, 5, 1, true, now(), now())
    """, h1_id, user_h1)
    await conn.execute("""
        INSERT INTO hospitals (id, user_id, name, registration_number, address, city, state, total_transfusion_beds, total_transfusion_chairs, emergency_capacity, is_active, created_at, updated_at)
        VALUES ($1, $2, 'Hospital Alternate', 'REG-HA', 'Address', 'ChennaiOver', 'TN', 5, 5, 1, true, now(), now())
    """, h2_id, user_h2)

    # Create Donors
    d1_id = uuid.uuid4() # Male, donated 100 days ago -> ELIGIBLE (cooldown 90)
    d2_id = uuid.uuid4() # Female, donated 100 days ago -> INELIGIBLE (cooldown 120)
    d3_id = uuid.uuid4() # Female, donated 130 days ago -> ELIGIBLE (cooldown 120)
    
    date_100_days_ago = date.today() - timedelta(days=100)
    date_130_days_ago = date.today() - timedelta(days=130)

    # Donor 1: Male, B+, medical clearance valid
    await conn.execute("""
        INSERT INTO donors (id, user_id, name, age, gender, blood_group, total_donations, reliability_score, max_travel_distance_km, is_available, medical_clearance_url, medical_clearance_at, demanded_reimbursement, last_donation_date, created_at, updated_at)
        VALUES ($1, $2, 'Donor First (Male)', 25, 'male', 'B_POS', 3, 100.00, 25, true, 'url', now(), 0.00, $3, now(), now())
    """, d1_id, user_d1, date_100_days_ago)
    
    # Donor 2: Female, B+, medical clearance valid
    await conn.execute("""
        INSERT INTO donors (id, user_id, name, age, gender, blood_group, total_donations, reliability_score, max_travel_distance_km, is_available, medical_clearance_url, medical_clearance_at, demanded_reimbursement, last_donation_date, created_at, updated_at)
        VALUES ($1, $2, 'Donor Alt (Female 100d)', 25, 'female', 'B_POS', 0, 100.00, 25, true, 'url', now(), 0.00, $3, now(), now())
    """, d2_id, user_d2, date_100_days_ago)

    # Donor 3: Female, B+, medical clearance valid
    await conn.execute("""
        INSERT INTO donors (id, user_id, name, age, gender, blood_group, total_donations, reliability_score, max_travel_distance_km, is_available, medical_clearance_url, medical_clearance_at, demanded_reimbursement, last_donation_date, created_at, updated_at)
        VALUES ($1, $2, 'Donor Third (Female 130d)', 25, 'female', 'B_POS', 0, 100.00, 25, true, 'url', now(), 0.00, $3, now(), now())
    """, d3_id, user_d3, date_130_days_ago)

    # Create confirmations to establish a 150-day average gap for Donor First (user_d1)
    # Event 1: 300 days ago, Event 2: 150 days ago
    t_hist1 = uuid.uuid4()
    t_hist2 = uuid.uuid4()
    await conn.execute("""
        INSERT INTO transfusions (id, patient_id, donor_id, hospital_id, predicted_date, urgency_level, status, patient_confirmation, donor_confirmation, coordinator_confirmation, hospital_confirmation, is_emergency, created_at, updated_at)
        VALUES ($1, $2, $3, $4, current_date - 300, 'routine', 'completed', 'confirmed', 'confirmed', 'confirmed', 'confirmed', false, now() - interval '300 days', now())
    """, t_hist1, patient_id, d1_id, h1_id)
    await conn.execute("""
        INSERT INTO transfusions (id, patient_id, donor_id, hospital_id, predicted_date, urgency_level, status, patient_confirmation, donor_confirmation, coordinator_confirmation, hospital_confirmation, is_emergency, created_at, updated_at)
        VALUES ($1, $2, $3, $4, current_date - 150, 'routine', 'completed', 'confirmed', 'confirmed', 'confirmed', 'confirmed', false, now() - interval '150 days', now())
    """, t_hist2, patient_id, d1_id, h1_id)

    await conn.execute("""
        INSERT INTO confirmations (id, transfusion_id, user_id, role, status, reminder_count, responded_at, created_at, updated_at)
        VALUES ($1, $2, $3, 'donor', 'confirmed', 0, now() - interval '300 days', now() - interval '300 days', now())
    """, uuid.uuid4(), t_hist1, user_d1)
    await conn.execute("""
        INSERT INTO confirmations (id, transfusion_id, user_id, role, status, reminder_count, responded_at, created_at, updated_at)
        VALUES ($1, $2, $3, 'donor', 'confirmed', 0, now() - interval '150 days', now() - interval '150 days', now())
    """, uuid.uuid4(), t_hist2, user_d1)

    print("Mock setup completed successfully.")

    # Create transfusion request
    t_id = uuid.uuid4()
    await conn.execute("""
        INSERT INTO transfusions (id, patient_id, donor_id, hospital_id, predicted_date, urgency_level, status, patient_confirmation, donor_confirmation, coordinator_confirmation, hospital_confirmation, is_emergency, created_at, updated_at)
        VALUES ($1, $2, $3, $4, current_date, 'routine', 'matching_donors', 'confirmed', 'pending', 'pending', 'pending', false, now(), now())
    """, t_id, patient_id, d1_id, h1_id)

    # Create confirmation record for the donor
    conf_id = uuid.uuid4()
    await conn.execute("""
        INSERT INTO confirmations (id, transfusion_id, user_id, role, status, reminder_count, created_at, updated_at)
        VALUES ($1, $2, $3, 'donor', 'pending', 1, now() - interval '7 hours', now())
    """, conf_id, t_id, user_d1)

    print("\n--- Step 2: Testing Unresponsive Donor Queries ---")
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    engine = create_async_engine("postgresql+asyncpg://postgres:password@localhost:5432/veinconnect_db")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        from app.services.scheduling_service import SchedulingService
        ss = SchedulingService()
        
        unresponsive = await ss.get_unresponsive_donors(session)
        print(f"Found unresponsive donors: {len(unresponsive)}")
        assert len(unresponsive) >= 1, "Unresponsive list should have at least 1 record"
        assert unresponsive[0]["donor_id"] == str(d1_id), "Donor 1 should be listed as unresponsive"
        print("Unresponsive donor retrieval assertion passed.")

        print("\n--- Step 3: Testing Gender-Specific Cooldowns & AI Pattern Learning ---")
        matches = await ss.get_donor_matches(session, t_id)
        print(f"Found recommended donor matches: {len(matches)}")
        
        # Verify that Donor 2 (Female, 100 days cooldown) is NOT in the matches (due to 120 days cooldown)
        match_ids = [m.donor_id for m in matches]
        print(f"Match IDs: {match_ids}")
        assert d2_id not in match_ids, "Female donor with 100 days cooldown should be ineligible (120 days needed)"
        assert d1_id in match_ids, "Male donor with 100 days cooldown should be eligible (90 days needed)"
        assert d3_id in match_ids, "Female donor with 130 days cooldown should be eligible (120 days needed)"
        print("Gender-specific cooldown filters verified successfully!")

        # Verify pattern learning response likelihood adjustment
        # Donor 1 (d1_id) has a learned gap of 150 days. Time since last donation is 100 days.
        # Ratio: 100 / 150 = ~0.667. Multiplier should scale down their base likelihood.
        d1_match = [m for m in matches if m.donor_id == d1_id][0]
        d3_match = [m for m in matches if m.donor_id == d3_id][0]
        
        # Base probability predicted by engine is usually ~0.9 or 0.8 depending on variables.
        # Verify that their likelihood is scaled down relative to the base 0.5+ threshold
        print(f"Donor 1 Adjusted Response Likelihood: {d1_match.response_likelihood}")
        # Maximum un-penalized likelihood is ~0.9. With a 0.667 multiplier, it must be < 0.70.
        assert d1_match.response_likelihood < 0.70, "Response likelihood should be penalized due to learned response pattern gap"
        print("AI Personal response frequency learning verified successfully!")

        # Verify Rotation and Frequency penalties:
        # Donor 1 should have a rotation penalty of -30.0 (since they were the last donor)
        # and a frequency gap penalty of -8.33 (since 100 days < 150 days average gap).
        # This pushes Donor 1's score down (to around 23.2), whereas Donor 3 (with no penalties) should score around 64.8.
        print(f"Donor 1 Match Score (with penalties): {d1_match.match_score}")
        print(f"Donor 3 Match Score (no penalties): {d3_match.match_score}")
        assert d1_match.match_score < 50.0, f"Donor 1 score {d1_match.match_score} should be penalized below 50.0"
        assert d3_match.match_score > 60.0, f"Donor 3 score {d3_match.match_score} should be above 60.0"
        # Check relative ranks rather than absolute ranks to be robust against other database records
        assert d3_match.match_score > d1_match.match_score, "Donor 3 should have a higher score than Donor 1"
        assert d3_match.rank < d1_match.rank, "Donor 3 should be ranked higher than Donor 1"
        print("Donor rotation and comfortable frequency gap penalties verified successfully!")

        print("\n--- Step 4: Testing Unresponsive Donor Override & Reliability Score Reduction ---")
        # Call override_donor
        updated_t = await ss.override_donor(session, t_id, d3_id)
        await session.commit()
        
        # Verify columns
        print(f"Updated Transfusion Donor ID: {updated_t.donor_id}")
        assert updated_t.donor_id == d3_id, "New donor should be assigned"
        assert updated_t.previous_donor_id == d1_id, "Previous donor ID should be tracked"

        # Check reliability score in database
        score_row = await conn.fetchrow("SELECT reliability_score FROM donors WHERE id = $1", d1_id)
        print(f"Previous Donor Reliability Score: {score_row['reliability_score']}%")
        assert score_row["reliability_score"] < 90.0, "Reliability score should be reduced by 15% (100 -> 85)"
        print("Donor override and reliability penalty assertions passed.")

        print("\n--- Step 5: Testing Hospital Rejection & Alternate proposed routing ---")
        from app.services.confirmation_service import ConfirmationService
        cs = ConfirmationService()

        # Preferred hospital rejects transfusion
        # We simulate this by calling confirmation_service.reject
        print("Preferred Hospital rejects the request...")
        await cs.reject(session, t_id, user_h1, "hospital", "No bed capacity")
        await session.commit()

        # Check if alternative hospital was automatically route proposed
        hosp_row = await conn.fetchrow("SELECT alternate_hospital_id, hospital_confirmation, patient_confirmation, donor_confirmation FROM transfusions WHERE id = $1", t_id)
        print(f"Proposed Alternate Hospital ID: {hosp_row['alternate_hospital_id']}")
        assert hosp_row["alternate_hospital_id"] == h2_id, "Alternate hospital h2 should be automatically proposed"
        assert hosp_row["hospital_confirmation"] == "pending", "Hospital confirmation should be reset to pending"
        assert hosp_row["patient_confirmation"] == "pending", "Patient confirmation should be reset to pending"
        assert hosp_row["donor_confirmation"] == "pending", "Donor confirmation should be reset to pending"
        print("Hospital alternate routing assertions passed.")

        # Simulate alternative hospital rejecting (second rejection)
        print("Alternative Hospital also rejects the request...")
        await cs.reject(session, t_id, user_h2, "hospital", "No chair slots")
        await session.commit()

        # Verify second rejection logs notes
        hosp_row_2 = await conn.fetchrow("SELECT notes FROM transfusions WHERE id = $1", t_id)
        print(f"Transfusion notes: {hosp_row_2['notes']}")
        assert "Manual routing required" in hosp_row_2["notes"], "Manual routing warning should be appended to notes"
        print("Second hospital rejection (takeover) assertions passed.")

        print("\n--- Step 6: Testing Manual Hospital Force Override ---")
        # Coordinator overrides and force-routes back to Hospital Preferred
        print("Coordinator force-assigns Hospital Preferred...")
        forced_t = await ss.override_hospital(session, t_id, h1_id)
        await session.commit()

        # Verify force assignment columns
        assert forced_t.hospital_id == h1_id, "Force assignment should set hospital_id"
        assert forced_t.alternate_hospital_id is None, "alternate_hospital_id should be cleared"
        assert forced_t.hospital_confirmation.value == "pending", "hospital_confirmation should be pending"
        print("Manual hospital override assertions passed.")

    # Clean up test accounts
    print("\n--- Step 7: Cleaning up test profiles ---")
    await conn.execute("DELETE FROM notifications WHERE transfusion_id IN ($1, $2, $3)", t_id, t_hist1, t_hist2)
    await conn.execute("DELETE FROM donations WHERE transfusion_id IN ($1, $2, $3)", t_id, t_hist1, t_hist2)
    await conn.execute("DELETE FROM confirmations WHERE transfusion_id IN ($1, $2, $3)", t_id, t_hist1, t_hist2)
    await conn.execute("DELETE FROM confirmations WHERE user_id IN ($1, $2, $3)", user_d1, user_d2, user_d3)
    await conn.execute("DELETE FROM transfusions WHERE id IN ($1, $2, $3)", t_id, t_hist1, t_hist2)
    await conn.execute("DELETE FROM donors WHERE id IN ($1, $2, $3)", d1_id, d2_id, d3_id)
    await conn.execute("DELETE FROM patients WHERE id = $1", patient_id)
    await conn.execute("DELETE FROM hospitals WHERE id IN ($1, $2)", h1_id, h2_id)
    await conn.execute("DELETE FROM wallets WHERE user_id IN ($1, $2, $3, $4, $5, $6)", user_p, user_d1, user_d2, user_d3, user_h1, user_h2)
    await conn.execute("DELETE FROM users WHERE id IN ($1, $2, $3, $4, $5, $6)", user_p, user_d1, user_d2, user_d3, user_h1, user_h2)
    await conn.close()

    print("\nAll integration tests for override flow passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_override_flow())


if __name__ == "__main__":
    asyncio.run(test_override_flow())
