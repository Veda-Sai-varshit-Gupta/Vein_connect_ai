import asyncio
import uuid
import random
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
import bcrypt
import asyncpg

# Password hashing
def hash_password(plain_password: str) -> str:
    pwd_bytes = plain_password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

# Mock data helper lists (mapped to database enum keys)
BLOOD_GROUPS = ["A_POS", "A_NEG", "B_POS", "B_NEG", "AB_POS", "AB_NEG", "O_POS", "O_NEG"]
GENDERS = ["male", "female", "other"]
THALASSEMIA_TYPES = ["major", "intermedia", "minor", "hb_e", "hb_s"]
CITIES = ["Chennai", "Bangalore", "Hyderabad", "Mumbai", "Delhi"]
STATES = ["TN", "KA", "TG", "MH", "DL"]

FIRST_NAMES = [
    "Aarav", "Vihaan", "Vivaan", "Ananya", "Diya", "Priya", "Rahul", "Siddharth",
    "Aditya", "Rohan", "Sneha", "Neha", "Arjun", "Karan", "Ishaan", "Tanvi",
    "Meera", "Kabir", "Riya", "Rajesh", "Amit", "Kiran", "Suresh", "Ramesh",
    "Vikram", "Sunil", "Anil", "Meena", "Sita", "Gita", "Lata", "Pooja",
    "Deepak", "Sanjay", "Vijay", "Aisha", "Zara", "Saira", "Farhan", "Imran"
]
LAST_NAMES = [
    "Sharma", "Verma", "Kumar", "Singh", "Patel", "Reddy", "Nair", "Iyer",
    "Rao", "Joshi", "Gupta", "Mehta", "Das", "Sen", "Bose", "Choudhury",
    "Pillai", "Menon", "Kapoor", "Khan", "Malhotra", "Grover", "Bahl", "Kohli",
    "Sari", "Roy", "Dutta", "Mishra", "Pandey", "Dubey", "Trivedi", "Pathak"
]

HOSPITAL_NAMES = [
    "City General Hospital", "Apollo Hospitals", "Fortis Healthcare",
    "St. John's Medical Center", "Manipal Hospital", "Narayana Health",
    "Global Hospitals", "Columbia Asia Hospital", "Aster CMI Hospital",
    "HCG Cancer Centre", "Kempegowda Institute of Medical Sciences",
    "M. S. Ramaiah Memorial Hospital", "People Tree Hospital", "Cloudnine Hospital",
    "Motherhood Hospital", "Sakra World Hospital", "BGS Gleneagles Global Hospital"
]

NGO_ORGANIZATIONS = ["Blood Warriors NGO", "Red Cross Society", "LifeSave NGO", "Youth Red Cross", "Helping Hands Foundation"]

# Blood compatibility map (using DB Enum keys)
COMPATIBILITY = {
    "O_NEG": ["O_NEG", "O_POS", "A_NEG", "A_POS", "B_NEG", "B_POS", "AB_NEG", "AB_POS"],
    "O_POS": ["O_POS", "A_POS", "B_POS", "AB_POS"],
    "A_NEG": ["A_NEG", "A_POS", "AB_NEG", "AB_POS"],
    "A_POS": ["A_POS", "AB_POS"],
    "B_NEG": ["B_NEG", "B_POS", "AB_NEG", "AB_POS"],
    "B_POS": ["B_POS", "AB_POS"],
    "AB_NEG": ["AB_NEG", "AB_POS"],
    "AB_POS": ["AB_POS"]
}

def get_compatible_donors(recipient_bg):
    """Find donor blood groups that can donate to recipient_bg."""
    donors = []
    for d_bg, recips in COMPATIBILITY.items():
        if recipient_bg in recips:
            donors.append(d_bg)
    return donors

async def main():
    conn_str = "postgresql://postgres:password@localhost:5432/veinconnect_db"
    conn = await asyncpg.connect(conn_str)
    
    print("Truncating existing records in DB (CASCADE)...")
    await conn.execute("""
        TRUNCATE TABLE 
            users, wallets, wallet_transactions, patients, donors, coordinators, 
            hospitals, hospital_capacities, patient_hospital_preferences, 
            transfusions, donations, confirmations, notifications, rewards, 
            expense_requests, friendship_scores, incidents
        CASCADE;
    """)

    # Hashed passwords for initial seed accounts and bulk users
    default_hashed = hash_password("password")
    
    # Store IDs for relationships
    patient_records = []
    donor_records = []
    coordinator_records = []
    hospital_records = []
    
    # ── 1. Create Default Developer Accounts ──────────────────────────────────
    print("Creating default access portal logins...")
    roles_and_credentials = [
        ("donor@veinconnect.com", "donor"),
        ("patient@veinconnect.com", "patient"),
        ("coordinator@veinconnect.com", "coordinator"),
        ("hospital@veinconnect.com", "hospital"),
        ("admin@veinconnect.com", "admin")
    ]
    
    for email, role in roles_and_credentials:
        u_id = uuid.uuid4()
        phone = f"+91{random.randint(6000000000, 9999999999)}"
        await conn.execute("""
            INSERT INTO users (id, email, phone, password_hash, role, is_active, is_verified, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, true, true, now(), now())
        """, u_id, email, phone, default_hashed, role)
        
        # Create wallet
        w_id = uuid.uuid4()
        balance = Decimal("2340.00") if role == "patient" else Decimal("1580.00") if role == "donor" else Decimal("0.00")
        await conn.execute("""
            INSERT INTO wallets (id, user_id, balance, total_earned, total_spent, currency, created_at, updated_at)
            VALUES ($1, $2, $3, $3, 0.00, 'INR', now(), now())
        """, w_id, u_id, balance)
        
        if role == "patient":
            p_id = uuid.uuid4()
            patient_records.append({"id": p_id, "user_id": u_id, "name": "Ravi Kumar", "blood_group": "B_POS"})
            await conn.execute("""
                INSERT INTO patients (id, user_id, name, age, gender, address, city, state, blood_group, thalassemia_type, avg_transfusion_interval_days, emergency_contact_name, emergency_contact_phone, data_sharing_consent, emergency_consent, created_at, updated_at)
                VALUES ($1, $2, 'Ravi Kumar', 12, 'male', '12 Cathedral Road', 'Chennai', 'TN', 'B_POS', 'major', 21, 'Suresh Kumar', '9876543210', true, true, now(), now())
            """, p_id, u_id)
        elif role == "donor":
            d_id = uuid.uuid4()
            donor_records.append({"id": d_id, "user_id": u_id, "name": "Arjun Kapoor", "blood_group": "B_POS", "reliability_score": Decimal("92.00")})
            await conn.execute("""
                INSERT INTO donors (id, user_id, name, age, gender, blood_group, total_donations, reliability_score, max_travel_distance_km, is_available, created_at, updated_at)
                VALUES ($1, $2, 'Arjun Kapoor', 24, 'male', 'B_POS', 4, 92.00, 25, true, now(), now())
            """, d_id, u_id)
        elif role == "coordinator":
            c_id = uuid.uuid4()
            coordinator_records.append({"id": c_id, "user_id": u_id})
            await conn.execute("""
                INSERT INTO coordinators (id, user_id, name, phone, organization, assigned_region, approval_status, created_at, updated_at)
                VALUES ($1, $2, 'Rajesh Sharma', $3, 'Blood Warriors NGO', 'Chennai', 'approved', now(), now())
            """, c_id, u_id, phone)
        elif role == "hospital":
            h_id = uuid.uuid4()
            hospital_records.append({"id": h_id, "user_id": u_id, "name": "City General Hospital"})
            await conn.execute("""
                INSERT INTO hospitals (id, user_id, name, registration_number, address, city, state, total_transfusion_beds, total_transfusion_chairs, emergency_capacity, coordinator_name, coordinator_email, coordinator_phone, operating_hours_start, operating_hours_end, is_active, created_at, updated_at)
                VALUES ($1, $2, 'City General Hospital', 'HOSP-12345', '15 Mount Road', 'Chennai', 'TN', 10, 15, 2, 'Dr. Geetha', 'geetha@hospital.org', '9898989898', '09:00:00', '18:00:00', true, now(), now())
            """, h_id, u_id)
            
            # Hospital Capacity
            await conn.execute("""
                INSERT INTO hospital_capacities (id, hospital_id, available_beds, occupied_beds, available_chairs, occupied_chairs, staff_available, upcoming_appointments, emergency_capacity_available, last_updated_at, created_at, updated_at)
                VALUES ($1, $2, 4, 6, 6, 9, 5, 3, 2, now(), now(), now())
            """, uuid.uuid4(), h_id)

    # ── 2. Create Bulk Users and Profiles ─────────────────────────────────────
    print("Generating bulk users and profiles (100 total)...")
    
    # 40 Patients
    for i in range(40):
        u_id = uuid.uuid4()
        email = f"patient{i}@veinconnect.com"
        phone = f"+91{random.randint(7000000000, 7999999999)}"
        await conn.execute("""
            INSERT INTO users (id, email, phone, password_hash, role, is_active, is_verified, created_at, updated_at)
            VALUES ($1, $2, $3, $4, 'patient', true, true, now(), now())
        """, u_id, email, phone, default_hashed)
        
        w_id = uuid.uuid4()
        balance = Decimal(str(random.randint(500, 3000)))
        await conn.execute("""
            INSERT INTO wallets (id, user_id, balance, total_earned, total_spent, currency, created_at, updated_at)
            VALUES ($1, $2, $3, $3, 0.00, 'INR', now(), now())
        """, w_id, u_id, balance)
        
        p_id = uuid.uuid4()
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        bg = random.choice(BLOOD_GROUPS)
        patient_records.append({"id": p_id, "user_id": u_id, "name": name, "blood_group": bg})
        
        city_idx = random.randint(0, len(CITIES)-1)
        city = CITIES[city_idx]
        state = STATES[city_idx]
        
        await conn.execute("""
            INSERT INTO patients (id, user_id, name, age, gender, address, city, state, blood_group, thalassemia_type, avg_transfusion_interval_days, emergency_contact_name, emergency_contact_phone, data_sharing_consent, emergency_consent, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, true, true, now(), now())
        """, p_id, u_id, name, random.randint(3, 17), random.choice(GENDERS), f"Flat {random.randint(10, 500)}", city, state, bg, random.choice(THALASSEMIA_TYPES), random.randint(15, 28), f"Parent {random.choice(LAST_NAMES)}", phone)

    # 45 Donors
    for i in range(45):
        u_id = uuid.uuid4()
        email = f"donor{i}@veinconnect.com"
        phone = f"+91{random.randint(8000000000, 8999999999)}"
        await conn.execute("""
            INSERT INTO users (id, email, phone, password_hash, role, is_active, is_verified, created_at, updated_at)
            VALUES ($1, $2, $3, $4, 'donor', true, true, now(), now())
        """, u_id, email, phone, default_hashed)
        
        w_id = uuid.uuid4()
        balance = Decimal(str(random.randint(0, 2000)))
        await conn.execute("""
            INSERT INTO wallets (id, user_id, balance, total_earned, total_spent, currency, created_at, updated_at)
            VALUES ($1, $2, $3, $3, 0.00, 'INR', now(), now())
        """, w_id, u_id, balance)
        
        d_id = uuid.uuid4()
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        bg = random.choice(BLOOD_GROUPS)
        score = Decimal(f"{random.randint(60, 100)}.00")
        donor_records.append({"id": d_id, "user_id": u_id, "name": name, "blood_group": bg, "reliability_score": score})
        dist = random.randint(10, 50)
        
        await conn.execute("""
            INSERT INTO donors (id, user_id, name, age, gender, blood_group, total_donations, reliability_score, max_travel_distance_km, is_available, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, true, now(), now())
        """, d_id, u_id, name, random.randint(18, 55), random.choice(GENDERS), bg, random.randint(1, 15), score, dist)

    # 5 Coordinators
    for i in range(5):
        u_id = uuid.uuid4()
        email = f"coordinator{i}@veinconnect.com"
        phone = f"+91{random.randint(9000000000, 9599999999)}"
        await conn.execute("""
            INSERT INTO users (id, email, phone, password_hash, role, is_active, is_verified, created_at, updated_at)
            VALUES ($1, $2, $3, $4, 'coordinator', true, true, now(), now())
        """, u_id, email, phone, default_hashed)
        
        w_id = uuid.uuid4()
        await conn.execute("""
            INSERT INTO wallets (id, user_id, balance, total_earned, total_spent, currency, created_at, updated_at)
            VALUES ($1, $2, 0.00, 0.00, 0.00, 'INR', now(), now())
        """, w_id, u_id)
        
        c_id = uuid.uuid4()
        coordinator_records.append({"id": c_id, "user_id": u_id})
        await conn.execute("""
            INSERT INTO coordinators (id, user_id, name, phone, organization, assigned_region, approval_status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, 'approved', now(), now())
        """, c_id, u_id, f"Coord {random.choice(FIRST_NAMES)}", phone, random.choice(NGO_ORGANIZATIONS), random.choice(CITIES))

    # 8 Hospitals
    for i in range(8):
        u_id = uuid.uuid4()
        email = f"hospital{i}@veinconnect.com"
        phone = f"+91{random.randint(9600000000, 9999999999)}"
        await conn.execute("""
            INSERT INTO users (id, email, phone, password_hash, role, is_active, is_verified, created_at, updated_at)
            VALUES ($1, $2, $3, $4, 'hospital', true, true, now(), now())
        """, u_id, email, phone, default_hashed)
        
        w_id = uuid.uuid4()
        await conn.execute("""
            INSERT INTO wallets (id, user_id, balance, total_earned, total_spent, currency, created_at, updated_at)
            VALUES ($1, $2, 0.00, 0.00, 0.00, 'INR', now(), now())
        """, w_id, u_id)
        
        h_id = uuid.uuid4()
        name = HOSPITAL_NAMES[i % len(HOSPITAL_NAMES)]
        hospital_records.append({"id": h_id, "user_id": u_id, "name": name})
        
        beds = random.randint(5, 30)
        chairs = random.randint(10, 40)
        
        city_idx = random.randint(0, len(CITIES)-1)
        city = CITIES[city_idx]
        state = STATES[city_idx]
        
        await conn.execute("""
            INSERT INTO hospitals (id, user_id, name, registration_number, address, city, state, total_transfusion_beds, total_transfusion_chairs, emergency_capacity, coordinator_name, coordinator_email, coordinator_phone, operating_hours_start, operating_hours_end, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, '08:00:00', '20:00:00', true, now(), now())
        """, h_id, u_id, name, f"REG-{random.randint(10000, 99999)}", f"Street {random.randint(1, 20)}", city, state, beds, chairs, random.randint(2, 5), f"Manager {random.choice(FIRST_NAMES)}", f"admin@{name.lower().replace(' ', '')}.org", phone)
        
        # Hospital Capacity
        occ_beds = random.randint(0, beds)
        occ_chairs = random.randint(0, chairs)
        await conn.execute("""
            INSERT INTO hospital_capacities (id, hospital_id, available_beds, occupied_beds, available_chairs, occupied_chairs, staff_available, upcoming_appointments, emergency_capacity_available, last_updated_at, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, now(), now(), now())
        """, uuid.uuid4(), h_id, beds - occ_beds, occ_beds, chairs - occ_chairs, occ_chairs, random.randint(3, 10), random.randint(1, 5), random.randint(1, 3))

    # ── 3. Patient Hospital Preferences (80 preferences) ──────────────────────
    print("Generating hospital preferences for patients...")
    for pat in patient_records:
        hosp_choices = random.sample(hospital_records, k=min(3, len(hospital_records)))
        for order, hosp in enumerate(hosp_choices, 1):
            await conn.execute("""
                INSERT INTO patient_hospital_preferences (id, patient_id, hospital_id, preference_order, created_at, updated_at)
                VALUES ($1, $2, $3, $4, now(), now())
            """, uuid.uuid4(), pat["id"], hosp["id"], order)

    # ── 4. Friendship Scores (60 relationships) ──────────────────────────────
    print("Generating friendship score trust pairs...")
    for i in range(60):
        pat = random.choice(patient_records)
        compatible_bgs = get_compatible_donors(pat["blood_group"])
        matching_donors = [d for d in donor_records if d["blood_group"] in compatible_bgs]
        if not matching_donors:
            continue
        donor = random.choice(matching_donors)
        
        # Avoid uniqueness errors
        try:
            await conn.execute("""
                INSERT INTO friendship_scores (id, patient_id, donor_id, score, total_donations, relationship_duration_days, positive_interactions, negative_interactions, last_interaction_at, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, now() - interval '5 days', now(), now())
            """, uuid.uuid4(), pat["id"], donor["id"], Decimal(str(random.randint(40, 100))), random.randint(1, 8), random.randint(30, 200), random.randint(1, 8), random.randint(0, 1))
        except Exception:
            pass # Skip duplicate pairs

    # ── 5. Transfusions (150 coordination runs) ──────────────────────────────
    print("Generating transfusion runs and consensus logs...")
    transfusion_records = []
    
    statuses = ["predicted", "patient_confirmed", "matching_donors", "donor_confirmed", "coordinator_confirmed", "hospital_confirmed", "scheduled", "in_progress", "completed", "cancelled"]
    
    for i in range(150):
        t_id = uuid.uuid4()
        pat = random.choice(patient_records)
        hosp = random.choice(hospital_records)
        coord = random.choice(coordinator_records)
        
        status = random.choice(statuses)
        urgency = random.choices(["routine", "urgent", "emergency"], weights=[0.7, 0.2, 0.1])[0]
        is_em = True if urgency == "emergency" else False
        
        # Pick compatible donor if state requires a matched donor
        donor_id = None
        if status in ["donor_confirmed", "coordinator_confirmed", "hospital_confirmed", "scheduled", "completed"]:
            compatible_bgs = get_compatible_donors(pat["blood_group"])
            matching_donors = [d for d in donor_records if d["blood_group"] in compatible_bgs]
            if matching_donors:
                donor_id = random.choice(matching_donors)["id"]
        
        pred_date = date.today() + timedelta(days=random.randint(-30, 30))
        sched_date = pred_date + timedelta(days=random.randint(-1, 2)) if status != "predicted" else None
        act_date = sched_date if status == "completed" else None
        
        # Confirmations setup
        pat_conf = "confirmed" if status != "predicted" else "pending"
        don_conf = "confirmed" if donor_id and status in ["donor_confirmed", "coordinator_confirmed", "hospital_confirmed", "scheduled", "completed"] else "pending"
        coord_conf = "confirmed" if status in ["coordinator_confirmed", "hospital_confirmed", "scheduled", "completed"] else "pending"
        hosp_conf = "confirmed" if status in ["hospital_confirmed", "scheduled", "completed"] else "pending"
        
        await conn.execute("""
            INSERT INTO transfusions (id, patient_id, donor_id, hospital_id, coordinator_id, predicted_date, scheduled_date, actual_date, urgency_level, status, patient_confirmation, donor_confirmation, coordinator_confirmation, hospital_confirmation, is_emergency, emergency_reason, alternate_hospital_id, notes, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, null, 'Automated scheduler metadata', now(), now())
        """, t_id, pat["id"], donor_id, hosp["id"], coord["id"], pred_date, sched_date, act_date, urgency, status, pat_conf, don_conf, coord_conf, hosp_conf, is_em, "Low Hb count" if is_em else None)
        
        transfusion_records.append({
            "id": t_id, "status": status, "patient_id": pat["id"], "donor_id": donor_id, 
            "hospital_id": hosp["id"], "coordinator_id": coord["id"], "scheduled_date": sched_date
        })

    # ── 6. Donations (120 records) ───────────────────────────────────────────
    print("Generating blood donation records...")
    donation_records = []
    for tr in [t for t in transfusion_records if t["status"] == "completed"]:
        don_id = uuid.uuid4()
        await conn.execute("""
            INSERT INTO donations (id, transfusion_id, donor_id, hospital_id, donation_date, status, blood_units, notes, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, 'completed', 1.00, 'Successful collection', now(), now())
        """, don_id, tr["id"], tr["donor_id"], tr["hospital_id"], tr["scheduled_date"])
        donation_records.append({"id": don_id, "transfusion_id": tr["id"], "donor_id": tr["donor_id"]})

    # ── 7. Confirmations (300 history trails) ─────────────────────────────────
    print("Generating workflow confirmations trails...")
    for tr in transfusion_records[:75]: # log trails for first 75 transfusions
        # Patient confirmation log
        await conn.execute("""
            INSERT INTO confirmations (id, transfusion_id, user_id, role, status, notes, reminder_count, last_reminder_at, responded_at, created_at, updated_at)
            VALUES ($1, $2, (SELECT user_id FROM patients WHERE id=$3), 'patient', 'confirmed', 'Preferred slot matches', 0, null, now() - interval '1 hour', now() - interval '1 hour', now())
        """, uuid.uuid4(), tr["id"], tr["patient_id"])
        
        # Donor confirmation log
        if tr["donor_id"]:
            await conn.execute("""
                INSERT INTO confirmations (id, transfusion_id, user_id, role, status, notes, reminder_count, last_reminder_at, responded_at, created_at, updated_at)
                VALUES ($1, $2, (SELECT user_id FROM donors WHERE id=$3), 'donor', 'confirmed', 'Happy to support', 1, now() - interval '3 hours', now() - interval '30 minutes', now() - interval '4 hours', now())
            """, uuid.uuid4(), tr["id"], tr["donor_id"])

    # ── 8. Rewards (100 logs) ────────────────────────────────────────────────
    print("Awarding reward points...")
    for don in donation_records:
        r_id = uuid.uuid4()
        pts = random.choice([100, 150, 200])
        await conn.execute("""
            INSERT INTO rewards (id, donor_id, donation_id, type, points, description, created_at)
            VALUES ($1, $2, $3, 'donation', $4, 'Earned 150 points for standard transfusion donation', now() - interval '2 days')
        """, r_id, don["donor_id"], don["id"], pts)

    # ── 9. Expense Requests & Wallet Transcations (120 ledger entries) ─────────
    print("Generating expense requests and wallet audit trails...")
    for index, don in enumerate(donation_records[:40]):
        e_id = uuid.uuid4()
        travel = Decimal(f"{random.randint(150, 800)}.00")
        other = Decimal(f"{random.choices([0, 150, 300], weights=[0.8, 0.1, 0.1])[0]}.00")
        total = travel + other
        
        status = "approved" if index < 30 else "pending"
        
        await conn.execute("""
            INSERT INTO expense_requests (id, donation_id, donor_id, travel_expense, other_expense, total_amount, description, status, is_flagged_by_ai, flag_reason, reviewed_by, reviewed_at, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, 'Auto-generated travel expenses claim', $7, false, null, (SELECT id FROM users WHERE role='coordinator' LIMIT 1), now(), now(), now())
        """, e_id, don["transfusion_id"], don["donor_id"], travel, other, total, status)
        
        # If approved, add wallet credit transaction
        if status == "approved":
            wallet_id = await conn.fetchval("SELECT id FROM wallets WHERE user_id = (SELECT user_id FROM donors WHERE id=$1)", don["donor_id"])
            if wallet_id:
                txn_id = uuid.uuid4()
                await conn.execute("""
                    INSERT INTO wallet_transactions (id, wallet_id, type, category, amount, description, reference_type, reference_id, status, created_at)
                    VALUES ($1, $2, 'credit', 'reimbursement', $3, $4, 'expense_request', $5, 'completed', now())
                """, txn_id, wallet_id, total, f"Approved travel reimbursement expense: {e_id}", e_id)
                
                # Update wallet balance
                await conn.execute("UPDATE wallets SET balance = balance + $1, total_earned = total_earned + $1 WHERE id = $2", total, wallet_id)

    # ── 10. Notifications (200 rows) ──────────────────────────────────────────
    print("Populating communication notification logs...")
    for i in range(200):
        recip_user = await conn.fetchrow("SELECT id, role FROM users ORDER BY random() LIMIT 1")
        if not recip_user:
            continue
        
        u_id = recip_user["id"]
        role = recip_user["role"]
        
        title = "Donation Request Match Found" if role == "donor" else "Schedule Predicted by AI" if role == "patient" else "Coordinator Approval Confirmation"
        msg = "Hi, you have a compatible blood group matching request. Please click here to review slot details."
        
        await conn.execute("""
            INSERT INTO notifications (id, user_id, transfusion_id, type, channel, title, message, language, priority, status, sent_at, delivered_at, read_at, failure_reason, created_at)
            VALUES ($1, $2, null, 'donation_request', 'app', $3, $4, 'en', 'normal', 'read', now() - interval '1 hour', now() - interval '55 minutes', now() - interval '40 minutes', null, now() - interval '1 hour')
        """, uuid.uuid4(), u_id, title, msg)

    # ── 11. Incidents (30 reports) ────────────────────────────────────────────
    print("Generating admin safety incidents logs...")
    for i in range(30):
        await conn.execute("""
            INSERT INTO incidents (id, type, severity, title, description, component, status, resolution, resolved_by, resolved_at, metadata_json, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, 'AI.DonorMatcher', 'resolved', 'Alternative donor assigned by NGO coordinator', null, now(), '{}', now() - interval '2 days', now())
        """, uuid.uuid4(), random.choice(["matching_failure", "prediction_failure", "system_error"]), random.choice(["low", "medium", "high"]), "AI Donor Match Exception Flagged", "Response SLA expired for first-tier matching donor. Coordinator escalated to second-tier alternate donor manually.")

    print("\n[SUCCESS] Populated database with related synthetic data!")
    print(f" - Users: {await conn.fetchval('SELECT count(*) FROM users')}")
    print(f" - Wallets: {await conn.fetchval('SELECT count(*) FROM wallets')}")
    print(f" - Patients: {await conn.fetchval('SELECT count(*) FROM patients')}")
    print(f" - Donors: {await conn.fetchval('SELECT count(*) FROM donors')}")
    print(f" - Coordinators: {await conn.fetchval('SELECT count(*) FROM coordinators')}")
    print(f" - Hospitals: {await conn.fetchval('SELECT count(*) FROM hospitals')}")
    print(f" - Hospital Capacities: {await conn.fetchval('SELECT count(*) FROM hospital_capacities')}")
    print(f" - Hospital Preferences: {await conn.fetchval('SELECT count(*) FROM patient_hospital_preferences')}")
    print(f" - Transfusions: {await conn.fetchval('SELECT count(*) FROM transfusions')}")
    print(f" - Donations: {await conn.fetchval('SELECT count(*) FROM donations')}")
    print(f" - Confirmations: {await conn.fetchval('SELECT count(*) FROM confirmations')}")
    print(f" - Rewards: {await conn.fetchval('SELECT count(*) FROM rewards')}")
    print(f" - Wallet Transactions: {await conn.fetchval('SELECT count(*) FROM wallet_transactions')}")
    print(f" - Expense Requests: {await conn.fetchval('SELECT count(*) FROM expense_requests')}")
    print(f" - Friendship Scores: {await conn.fetchval('SELECT count(*) FROM friendship_scores')}")
    print(f" - Notifications: {await conn.fetchval('SELECT count(*) FROM notifications')}")
    print(f" - Incidents: {await conn.fetchval('SELECT count(*) FROM incidents')}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
