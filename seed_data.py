import datetime
from database import get_db_connection

def seed_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing data
    tables = [
        'campuses', 'users', 'classrooms', 'students', 'leads', 'attendance_logs',
        'staff_attendance', 'staff_credentials', 'daily_activities', 'invoices',
        'inventory_items', 'supply_requests', 'menus', 'messages', 'student_badges', 'reading_logs'
    ]
    for table in tables:
        cursor.execute(f"DELETE FROM {table}")
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")

    print("Cleared existing tables. Seeding fresh Little Millennium Kharadi branch data...")

    # 1. Campus
    cursor.execute('''
    INSERT INTO campuses (name, code, address, phone, license_no)
    VALUES (?, ?, ?, ?, ?)
    ''', (
        "Little Millennium & Nest Daycare (Kharadi Branch)",
        "LM-NEST-KHD",
        "Survey No. 42/1, Kharadi Bypass Rd, Near EON IT Park, Kharadi, Pune, Maharashtra 411014",
        "+91 98230 45678",
        "MH-PUN-ECE-2024-8841"
    ))
    campus_id = cursor.lastrowid

    # 2. Classrooms
    classrooms_data = [
        ("Infant Care", "3 - 12 Months", 9, "Room 101 (Soft Nest)", 3),
        ("Toddler Nest", "12 - 24 Months", 15, "Room 102 (Little Crawlers)", 5),
        ("Playgroup", "2 - 3 Years", 14, "Room 103 (Curious Tots)", 7),
        ("Pre-K / Kindergarten", "3 - 5 Years", 16, "Room 104 (Little Scholars)", 8),
        ("After-School Daycare", "5 - 10 Years", 20, "Room 105 (Activity Zone)", 10)
    ]
    cursor.executemany('''
    INSERT INTO classrooms (name, age_group, capacity, room_number, max_ratio)
    VALUES (?, ?, ?, ?, ?)
    ''', classrooms_data)

    # 3. Users (Admins, Teachers, Parents, Students)
    users_data = [
        # Admin / Director
        (campus_id, "Chanchal Sharma", "director@littlemillennium.com", "director123", "director", "+91 98220 11223", "1234", "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150", "Center Director"),
        (campus_id, "Rajesh Kulkarni", "admin@littlemillennium.com", "admin123", "admin", "+91 98220 44556", "1111", "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=150", "Operations & Finance Lead"),
        # Teachers
        (campus_id, "Priya Nair", "priya@littlemillennium.com", "priya123", "teacher", "+91 97660 12345", "2222", "https://images.unsplash.com/photo-1580894732454-def9d4c2b96c?w=150", "Lead Infant Educator"),
        (campus_id, "Ananya Deshmukh", "ananya@littlemillennium.com", "ananya123", "teacher", "+91 97660 23456", "3333", "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150", "Toddler Nest Specialist"),
        (campus_id, "Sunita Rao", "sunita@littlemillennium.com", "sunita123", "teacher", "+91 97660 34567", "4444", "https://images.unsplash.com/photo-1567532939604-b6b5b0db2604?w=150", "Playgroup Instructor"),
        (campus_id, "Meera Joshi", "meera@littlemillennium.com", "meera123", "teacher", "+91 97660 45678", "5555", "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=150", "Pre-K Senior Teacher"),
        (campus_id, "Kavita Patil", "kavita@littlemillennium.com", "kavita123", "teacher", "+91 97660 56789", "6666", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150", "Daycare & Activity Coordinator"),
        # Parents
        (campus_id, "Vikram Mehta", "vikram.mehta@gmail.com", "vikram123", "parent", "+91 98901 23456", "7777", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150", "Parent (Father of Aarav)"),
        (campus_id, "Neha Kapoor", "neha.kapoor@gmail.com", "neha123", "parent", "+91 98902 34567", "8888", "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150", "Parent (Mother of Anvi)"),
        (campus_id, "Rohan Gupta", "rohan.gupta@gmail.com", "rohan123", "parent", "+91 98903 45678", "9999", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150", "Parent (Father of Vihaan)"),
        # Students (User profiles for Student Portal)
        (campus_id, "Aarav Mehta", "aarav@student.lm", "aarav123", "student", "+91 98901 23456", "0001", "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150", "Little Explorer (Toddler)"),
        (campus_id, "Anvi Kapoor", "anvi@student.lm", "anvi123", "student", "+91 98902 34567", "0002", "https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=150", "Pre-K Scholar"),
        (campus_id, "Vihaan Gupta", "vihaan@student.lm", "vihaan123", "student", "+91 98903 45678", "0003", "https://images.unsplash.com/photo-1516627145497-ae6968895b74?w=150", "Playgroup Buddy")
    ]
    cursor.executemany('''
    INSERT INTO users (campus_id, name, email, password, role, phone, pin_code, avatar, title)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', users_data)

    # 4. Students Records (SIS)
    students_data = [
        # Infant Care (Class 1)
        (campus_id, 1, 8, "Riaan", "Patel", "2026-03-15", "Male", "O+", "None", 0, "Formula only (Enfamil)", "Compliant", "Hiren Patel", "+91 98221 00001", "1011", "https://images.unsplash.com/photo-1544717305-2782549b5136?w=150", "2026-06-01"),
        (campus_id, 1, 8, "Tara", "Iyer", "2026-04-10", "Female", "A+", "None", 0, "Expressed Breast Milk", "Compliant", "Ramesh Iyer", "+91 98221 00002", "1012", "https://images.unsplash.com/photo-1519689680058-324335c77eba?w=150", "2026-07-01"),
        (campus_id, 1, 9, "Kabir", "Bose", "2026-01-20", "Male", "B+", "Cow Milk (Lactose)", 0, "Soy Formula Only", "Expiring Soon", "Sharmila Bose", "+91 98221 00003", "1013", "https://images.unsplash.com/photo-1502086223501-7ea6ecd79368?w=150", "2026-05-15"),
        
        # Toddler Nest (Class 2)
        (campus_id, 2, 8, "Aarav", "Mehta", "2025-05-14", "Male", "B+", "Severe Peanut Allergy", 1, "Nut-free diet strictly", "Compliant", "Vikram Mehta", "+91 98901 23456", "7777", "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150", "2025-08-01"),
        (campus_id, 2, 9, "Isha", "Kulkarni", "2025-06-22", "Female", "O+", "None", 0, "Vegetarian", "Compliant", "Gaurav Kulkarni", "+91 98221 00004", "1022", "https://images.unsplash.com/photo-1543332164-6e82f355badc?w=150", "2025-09-01"),
        (campus_id, 2, 10, "Advait", "Nambiar", "2025-04-05", "Male", "AB+", "Egg Allergy", 0, "Eggless meals", "Overdue", "Deepak Nambiar", "+91 98221 00005", "1023", "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150", "2025-07-15"),
        (campus_id, 2, 8, "Zoya", "Khan", "2025-07-18", "Female", "A-", "None", 0, "Halal / Pure Veg", "Compliant", "Tariq Khan", "+91 98221 00006", "1024", "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?w=150", "2025-10-01"),
        (campus_id, 2, 9, "Samarth", "Pawar", "2025-03-30", "Male", "O+", "None", 0, "General", "Compliant", "Nitin Pawar", "+91 98221 00007", "1025", "https://images.unsplash.com/photo-1485546246426-74dc88dec4d9?w=150", "2025-06-20"),

        # Playgroup (Class 3)
        (campus_id, 3, 10, "Vihaan", "Gupta", "2024-04-12", "Male", "O+", "Gluten Sensitivity", 0, "Gluten-Free Snacks", "Compliant", "Rohan Gupta", "+91 98903 45678", "9999", "https://images.unsplash.com/photo-1516627145497-ae6968895b74?w=150", "2024-07-01"),
        (campus_id, 3, 8, "Myra", "Singh", "2024-08-08", "Female", "B+", "None", 0, "Vegetarian", "Compliant", "Harpreet Singh", "+91 98221 00008", "1032", "https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?w=150", "2024-09-01"),
        (campus_id, 3, 9, "Dhruv", "Rathore", "2024-02-19", "Male", "A+", "Severe Bee Sting / Insect", 1, "EpiPen in First Aid Box", "Compliant", "Sanjay Rathore", "+91 98221 00009", "1033", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150", "2024-06-15"),
        (campus_id, 3, 10, "Ananya", "Choudhury", "2024-06-30", "Female", "O+", "None", 0, "No Seafood", "Expiring Soon", "Subrata Choudhury", "+91 98221 00010", "1034", "https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=150", "2024-08-15"),
        (campus_id, 3, 8, "Kiaan", "Verma", "2024-05-11", "Male", "AB+", "None", 0, "General", "Compliant", "Anil Verma", "+91 98221 00011", "1035", "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=150", "2024-07-20"),

        # Pre-K / Kindergarten (Class 4)
        (campus_id, 4, 9, "Anvi", "Kapoor", "2023-03-25", "Female", "A+", "None", 0, "Vegetarian, Lactose-friendly", "Compliant", "Neha Kapoor", "+91 98902 34567", "8888", "https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=150", "2023-06-15"),
        (campus_id, 4, 10, "Dev", "Shah", "2023-07-14", "Male", "B+", "None", 0, "Jain Diet (No Root Veg)", "Compliant", "Bhavin Shah", "+91 98221 00012", "1042", "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150", "2023-08-01"),
        (campus_id, 4, 8, "Saanvi", "Reddy", "2023-09-02", "Female", "O-", "Strawberries", 0, "No Berries", "Compliant", "Venkat Reddy", "+91 98221 00013", "1043", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150", "2023-10-10"),
        (campus_id, 4, 9, "Reyansh", "Shinde", "2023-01-18", "Male", "O+", "None", 0, "General", "Compliant", "Amol Shinde", "+91 98221 00014", "1044", "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150", "2023-06-01"),

        # After-School Daycare (Class 5)
        (campus_id, 5, 8, "Ishaan", "Bhatia", "2021-08-15", "Male", "A+", "Asthma Inhaler in Bag", 0, "High Energy Snacks", "Compliant", "Karan Bhatia", "+91 98221 00015", "1051", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150", "2022-04-01"),
        (campus_id, 5, 9, "Kiara", "Menon", "2022-02-10", "Female", "B+", "None", 0, "Vegetarian", "Compliant", "Sunil Menon", "+91 98221 00016", "1052", "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150", "2022-07-01"),
        (campus_id, 5, 10, "Arjun", "Malhotra", "2021-11-28", "Male", "O+", "None", 0, "General", "Compliant", "Rajeev Malhotra", "+91 98221 00017", "1053", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150", "2022-05-15")
    ]
    cursor.executemany('''
    INSERT INTO students (campus_id, classroom_id, parent_id, first_name, last_name, dob, gender, blood_group, allergies, epipen_required, dietary_restrictions, immunization_status, emergency_contact_name, emergency_contact_phone, pickup_pin, photo_url, enrollment_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', students_data)

    # 5. CRM Leads & Tour Scheduling
    today_str = datetime.date.today().isoformat()
    leads_data = [
        (campus_id, "Miraan Kotecha", "18 Months", "Shruti Kotecha", "+91 98231 11223", "shruti.kotecha@gmail.com", "Toddler Nest", "New", None, None, "Parent inquired online via Kharadi portal. Looking for immediate start."),
        (campus_id, "Anaya Agarwal", "2.5 Years", "Manish Agarwal", "+91 98231 22334", "manish.agarwal@wipro.com", "Playgroup", "Tour Scheduled", today_str, "10:30 AM", "Working at EON IT Park. Wants to see outdoor splash pool and safety fencing."),
        (campus_id, "Vivaan Joshi", "3 Years", "Pooja Joshi", "+91 98231 33445", "pooja.j@infosys.com", "Pre-K / Kindergarten", "Tour Scheduled", today_str, "04:00 PM", "Interested in full-day daycare combination."),
        (campus_id, "Tanya Sen", "10 Months", "Amit Sen", "+91 98231 44556", "amit.sen@tcs.com", "Infant Care", "Tour Completed", "2026-10-27", "11:00 AM", "Tour went well. Loved the soft play area and CCTV live ratio monitor."),
        (campus_id, "Rudra Deshmukh", "2 Years", "Prakash Deshmukh", "+91 98231 55667", "prakash.d@gmail.com", "Toddler Nest", "Application Submitted", "2026-10-25", "02:00 PM", "Submitted digital packet. Waiting for doctor immunization record upload."),
        (campus_id, "Sia Rao", "4 Years", "Kiran Rao", "+91 98231 66778", "kiran.rao@gmail.com", "Pre-K / Kindergarten", "Enrolled", "2026-10-20", "10:00 AM", "Enrolled for Nov batch! First fee installment cleared.")
    ]
    cursor.executemany('''
    INSERT INTO leads (campus_id, child_name, child_age, parent_name, parent_phone, parent_email, requested_program, status, tour_date, tour_time, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', leads_data)

    # 6. Student Attendance for Today (Simulating checked-in students)
    # Infant: 3 present (1 teacher on duty => 3:1 compliant)
    # Toddler: 5 present (1 teacher on duty => 5:1 compliant)
    # Playgroup: 5 present (1 teacher on duty => 5:1 compliant)
    # Pre-K: 4 present (1 teacher on duty => 4:1 compliant)
    # Daycare: 3 present (1 teacher on duty => 3:1 compliant)
    attendance_data = [
        (campus_id, 1, 1, today_str, "08:15 AM", None, "Priya Nair", None, "Present"),
        (campus_id, 2, 1, today_str, "08:30 AM", None, "Priya Nair", None, "Present"),
        (campus_id, 3, 1, today_str, "08:45 AM", None, "Priya Nair", None, "Present"),
        (campus_id, 4, 2, today_str, "08:20 AM", None, "Ananya Deshmukh", None, "Present"),
        (campus_id, 5, 2, today_str, "08:35 AM", None, "Ananya Deshmukh", None, "Present"),
        (campus_id, 6, 2, today_str, "08:50 AM", None, "Ananya Deshmukh", None, "Present"),
        (campus_id, 7, 2, today_str, "09:00 AM", None, "Ananya Deshmukh", None, "Present"),
        (campus_id, 8, 2, today_str, "09:10 AM", None, "Ananya Deshmukh", None, "Present"),
        (campus_id, 9, 3, today_str, "08:40 AM", None, "Sunita Rao", None, "Present"),
        (campus_id, 10, 3, today_str, "08:55 AM", None, "Sunita Rao", None, "Present"),
        (campus_id, 11, 3, today_str, "09:05 AM", None, "Sunita Rao", None, "Present"),
        (campus_id, 12, 3, today_str, "09:15 AM", None, "Sunita Rao", None, "Present"),
        (campus_id, 13, 3, today_str, "09:25 AM", None, "Sunita Rao", None, "Present"),
        (campus_id, 14, 4, today_str, "08:30 AM", None, "Meera Joshi", None, "Present"),
        (campus_id, 15, 4, today_str, "08:45 AM", None, "Meera Joshi", None, "Present"),
        (campus_id, 16, 4, today_str, "09:00 AM", None, "Meera Joshi", None, "Present"),
        (campus_id, 17, 4, today_str, "09:10 AM", None, "Meera Joshi", None, "Present"),
        (campus_id, 18, 5, today_str, "01:30 PM", None, "Kavita Patil", None, "Present"),
        (campus_id, 19, 5, today_str, "01:45 PM", None, "Kavita Patil", None, "Present"),
        (campus_id, 20, 5, today_str, "02:00 PM", None, "Kavita Patil", None, "Present")
    ]
    cursor.executemany('''
    INSERT INTO attendance_logs (campus_id, student_id, classroom_id, date, check_in, check_out, checked_in_by, checked_out_by, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', attendance_data)

    # 7. Staff Clock-in Punches Today
    staff_attendance_data = [
        (campus_id, 3, today_str, "07:55 AM", None, 7.5, "Present"), # Priya (Infant)
        (campus_id, 4, today_str, "08:05 AM", None, 7.3, "Present"), # Ananya (Toddler)
        (campus_id, 5, today_str, "08:15 AM", None, 7.1, "Present"), # Sunita (Playgroup)
        (campus_id, 6, today_str, "08:10 AM", None, 7.2, "Present"), # Meera (Pre-K)
        (campus_id, 7, today_str, "08:30 AM", None, 6.8, "Present"), # Kavita (Daycare)
        (campus_id, 1, today_str, "08:00 AM", None, 7.5, "Present"), # Director Chanchal
        (campus_id, 2, today_str, "08:20 AM", None, 7.0, "Present")  # Admin Rajesh
    ]
    cursor.executemany('''
    INSERT INTO staff_attendance (campus_id, user_id, date, clock_in, clock_out, total_hours, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', staff_attendance_data)

    # 8. Staff Credentials & Compliance Records
    credentials_data = [
        (3, "Pediatric CPR & First Aid Certification", "2025-02-10", "2027-02-10", "Valid", "DOC-CPR-01"),
        (3, "Police Background Verification", "2025-01-15", "2027-01-15", "Valid", "DOC-BG-01"),
        (4, "Early Childhood Development Diploma", "2024-06-01", "2029-06-01", "Valid", "DOC-ECD-02"),
        (4, "Fire Safety & Evacuation Drill Certification", "2025-11-01", "2026-11-05", "Expiring Soon", "DOC-FIRE-02"),
        (5, "Food Handler's Hygiene Certificate", "2025-03-12", "2027-03-12", "Valid", "DOC-FOOD-03"),
        (6, "Montessori Teaching Credentials (AMI)", "2023-08-10", "2028-08-10", "Valid", "DOC-AMI-04"),
        (7, "Daycare Management & Child Safeguarding", "2024-10-15", "2026-10-15", "Expired", "DOC-SAFE-05")
    ]
    cursor.executemany('''
    INSERT INTO staff_credentials (user_id, credential_name, issue_date, expiry_date, status, doc_ref)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', credentials_data)

    # 9. Daily Classroom Activities (Teacher Daily Sheets)
    activities_data = [
        # Aarav Mehta (Toddler Nest)
        (4, 2, 4, "meal", "Morning Snack Finished!", "Aarav ate all banana slices and 1 whole wheat toast. Good appetite!", "10:00 AM", '{"meal_type":"Snack","portion":"100%"}'),
        (4, 2, 4, "nap", "Afternoon Nap", "Fell asleep quickly with soft music. Slept peacefully from 12:45 PM to 02:15 PM.", "02:15 PM", '{"duration":"1 hr 30 mins"}'),
        (4, 2, 4, "potty", "Potty Check", "Dry diaper check, used the toddler toilet successfully with teacher encouragement!", "11:30 AM", '{"result":"Dry/Toilet Success"}'),
        (4, 2, 4, "learning", "Sensory Play & Watercolors", "Loved mixing primary colors today! Created a beautiful green frog painting using handprints.", "03:15 PM", '{"milestone":"Fine Motor"}'),
        # Anvi Kapoor (Pre-K)
        (14, 4, 6, "observation", "Phonics & Rhyme Time", "Anvi identified all words starting with the letter 'P'. She helped her friend dev count blocks.", "10:30 AM", '{"milestone":"Cognitive"}'),
        (14, 4, 6, "meal", "Nutritious Hot Lunch", "Ate 1 roti, yellow dal, and steamed carrot sticks. Drank 1 cup of warm milk.", "12:30 PM", '{"meal_type":"Lunch","portion":"90%"}'),
        # Vihaan Gupta (Playgroup)
        (9, 3, 5, "learning", "Building Blocks Tower", "Built a 9-block tower independently! Practiced sharing red blocks with Myra.", "11:15 AM", '{"milestone":"Social-Emotional"}'),
        (9, 3, 5, "nap", "Rest Time", "Rested calmly on his cot for 1 hour. Woke up refreshed with smiles.", "02:00 PM", '{"duration":"1 hr"}')
    ]
    cursor.executemany('''
    INSERT INTO daily_activities (student_id, classroom_id, teacher_id, activity_type, title, details, timestamp, metadata_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', activities_data)

    # 10. Billing & Invoices
    invoices_data = [
        (campus_id, 4, 8, "INV-2026-03-004", "October 2026", 14500.0, "2026-10-10", "Paid", "UPI", "2026-10-05 14:20:00", "REC-LM-4401"),
        (campus_id, 14, 9, "INV-2026-03-014", "October 2026", 16000.0, "2026-10-10", "Paid", "NetBanking", "2026-10-06 09:15:00", "REC-LM-4402"),
        (campus_id, 9, 10, "INV-2026-03-009", "October 2026", 13500.0, "2026-10-10", "Pending", "Pending", None, None),
        (campus_id, 1, 8, "INV-2026-03-001", "October 2026", 18000.0, "2026-10-10", "Paid", "Cash", "2026-10-08 11:00:00", "REC-LM-4403"),
        (campus_id, 6, 9, "INV-2026-03-006", "September 2026", 14500.0, "2026-09-10", "Overdue", "Pending", None, None)
    ]
    cursor.executemany('''
    INSERT INTO invoices (campus_id, student_id, parent_id, invoice_number, term_month, amount, due_date, status, payment_method, paid_at, receipt_number)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', invoices_data)

    # 11. Inventory & Supplies (Classroom Consumables)
    inventory_data = [
        (campus_id, "Hygiene", "Pampers Toddler Diapers (Size 4)", 38, 50, "Pieces", "2026-10-20"),
        (campus_id, "Hygiene", "Huggies Sensitive Wet Wipes (80pk)", 14, 25, "Packs", "2026-10-22"),
        (campus_id, "Hygiene", "Sterillium Hand Sanitizer 500ml", 12, 10, "Bottles", "2026-10-15"),
        (campus_id, "Hygiene", "Disposable Nitrile Gloves (Medium)", 8, 15, "Boxes", "2026-10-10"),
        (campus_id, "Art & Craft", "Non-Toxic Crayola Finger Paints", 24, 15, "Sets", "2026-10-25"),
        (campus_id, "Art & Craft", "A4 Pastel Construction Paper", 180, 100, "Sheets", "2026-10-18"),
        (campus_id, "Art & Craft", "Child-Safe Ergonomic Scissors", 22, 20, "Pieces", "2026-09-15"),
        (campus_id, "Medical/First-Aid", "Waterproof Band-Aid Strips", 110, 50, "Strips", "2026-10-12"),
        (campus_id, "Medical/First-Aid", "Infant Paracetamol & Fever Scan Strips", 6, 5, "Units", "2026-10-01")
    ]
    cursor.executemany('''
    INSERT INTO inventory_items (campus_id, category, item_name, current_stock, min_threshold, unit, last_restocked)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', inventory_data)

    # 12. Supply Requests Kanban
    supply_requests_data = [
        (campus_id, 4, 2, "Wet Wipes (Size 4) - Urgent for Toddler Room", 5, "Urgent", "Pending", "We have only 2 packs remaining after morning routine."),
        (campus_id, 5, 3, "Construction Paper - Yellow & Blue for Craft", 50, "Normal", "Approved", "Needed for upcoming Diwali lantern activity."),
        (campus_id, 3, 1, "Sterile Diaper Changing Mat Liners", 2, "High", "Dispatched", "Dispatched by store coordinator.")
    ]
    cursor.executemany('''
    INSERT INTO supply_requests (campus_id, teacher_id, classroom_id, item_name, quantity, urgency, status, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', supply_requests_data)

    # 13. CACFP / Nutritional Food Program Menus
    menus_data = [
        (campus_id, "Monday", "Breakfast", "Steamed Idlis with Coconut Chutney & Warm Milk", "Milk", 210),
        (campus_id, "Monday", "Morning Snack", "Organic Fresh Papaya Cubes & Sprouted Moong", "None", 90),
        (campus_id, "Monday", "Lunch", "Soft Phulkas, Yellow Dal Tadka, Steamed Jeera Rice, Carrot-Cucumber Salad", "Gluten", 340),
        (campus_id, "Monday", "Afternoon Snack", "Oatmeal Apple Porridge with a touch of Cinnamon", "Oats, Milk", 140),

        (campus_id, "Tuesday", "Breakfast", "Vegetable Poha with Toasted Peanuts (Allergy Checked)", "Peanuts (Flagged)", 220),
        (campus_id, "Tuesday", "Morning Snack", "Crispy Apple Slices with Pure Sunflower Seed Butter", "None", 110),
        (campus_id, "Tuesday", "Lunch", "Paneer Bhurji, Spinach Khichdi with Pure Cow Ghee, Curd", "Milk", 360),
        (campus_id, "Tuesday", "Afternoon Snack", "Whole Wheat Banana Bread muffin (Homemade, Low Sugar)", "Gluten", 150)
    ]
    cursor.executemany('''
    INSERT INTO menus (campus_id, day_of_week, meal_time, items_description, allergen_tags, calories)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', menus_data)

    # 14. Direct Parent-Teacher Messages
    messages_data = [
        (8, 4, "parent", "Good morning Ananya ma'am, Aarav had a slight cough last night. I have packed his syrup with the label.", 1, "शुभ प्रभात अनन्या मैम, आरव को कल रात हल्की खांसी थी। मैंने लेबल के साथ उसका सिरप पैक कर दिया है।"),
        (4, 8, "teacher", "Thank you for the update Vikram ji! We will keep a close eye on him during outdoor play and log his temperature at nap time.", 1, "अपडेट के लिए धन्यवाद विक्रम जी! हम बाहरी खेल के दौरान उस पर कड़ी नज़र रखेंगे।")
    ]
    cursor.executemany('''
    INSERT INTO messages (sender_id, receiver_id, sender_role, message_text, read_status, translated_text)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', messages_data)

    # 15. Student Achievement Badges
    badges_data = [
        (4, "tied_shoes", "I Tied My Shoes!", "👟", "Independence", "Mastered tying loop-and-swoop laces during circle time!"),
        (4, "counted_twenty", "Counted to 20!", "🔢", "Math & Logic", "Counted 20 colorful counting bears without skipping!"),
        (4, "clean_plate", "Clean Plate Champion", "🥣", "Nutrition", "Ate all veggies during lunch time with a big smile!"),
        (4, "kind_helper", "Golden Helper", "⭐", "Social", "Helped friend pick up fallen blocks and held the classroom door open."),
        (14, "master_artist", "Star Painter", "🎨", "Creativity", "Created a brilliant rainbow collage using finger paints."),
        (9, "block_architect", "Tower Builder", "🏰", "Spatial", "Constructed a steady 9-block high tower independently!")
    ]
    cursor.executemany('''
    INSERT INTO student_badges (student_id, badge_key, badge_title, badge_icon, category, description)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', badges_data)

    # 16. Reading Bookshelf Logs
    reading_data = [
        (4, "The Very Hungry Caterpillar", "Eric Carle", 22, "🐛"),
        (4, "Brown Bear, Brown Bear, What Do You See?", "Bill Martin Jr.", 26, "🐻"),
        (4, "Where is the Green Sheep?", "Mem Fox", 32, "🐑"),
        (14, "Giraffes Can't Dance", "Giles Andreae", 32, "🦒"),
        (9, "Goodnight Moon", "Margaret Wise Brown", 30, "🌙")
    ]
    cursor.executemany('''
    INSERT INTO reading_logs (student_id, book_title, author, pages, sticker_icon)
    VALUES (?, ?, ?, ?, ?)
    ''', reading_data)

    conn.commit()
    conn.close()
    print("Database successfully seeded with realistic Little Millennium Kharadi branch data!")

if __name__ == '__main__':
    seed_database()
