import sqlite3
import os
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Campuses
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS campuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        address TEXT,
        phone TEXT,
        license_no TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campus_id INTEGER DEFAULT 1,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL, -- admin, director, teacher, parent, student
        phone TEXT,
        pin_code TEXT,
        avatar TEXT,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(campus_id) REFERENCES campuses(id)
    )
    ''')

    # Classrooms
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS classrooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campus_id INTEGER DEFAULT 1,
        name TEXT NOT NULL,
        age_group TEXT NOT NULL,
        capacity INTEGER NOT NULL,
        room_number TEXT,
        max_ratio INTEGER NOT NULL,
        FOREIGN KEY(campus_id) REFERENCES campuses(id)
    )
    ''')

    # Students
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campus_id INTEGER DEFAULT 1,
        roll_number TEXT UNIQUE,
        classroom_id INTEGER,
        parent_id INTEGER,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        dob TEXT,
        gender TEXT,
        blood_group TEXT,
        allergies TEXT,
        epipen_required INTEGER DEFAULT 0,
        dietary_restrictions TEXT,
        immunization_status TEXT DEFAULT 'Compliant', -- Compliant, Expiring Soon, Overdue
        emergency_contact_name TEXT,
        emergency_contact_phone TEXT,
        pickup_pin TEXT,
        photo_url TEXT,
        enrollment_date TEXT,
        status TEXT DEFAULT 'Active',
        FOREIGN KEY(classroom_id) REFERENCES classrooms(id),
        FOREIGN KEY(parent_id) REFERENCES users(id)
    )
    ''')

    # CRM Leads & Inquiries
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campus_id INTEGER DEFAULT 1,
        child_name TEXT NOT NULL,
        child_age TEXT,
        parent_name TEXT NOT NULL,
        parent_phone TEXT NOT NULL,
        parent_email TEXT,
        requested_program TEXT NOT NULL,
        status TEXT DEFAULT 'New', -- New, Contacted, Tour Scheduled, Tour Completed, Application Submitted, Enrolled, Lost
        tour_date TEXT,
        tour_time TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Student Attendance
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campus_id INTEGER DEFAULT 1,
        student_id INTEGER NOT NULL,
        classroom_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        check_in TEXT,
        check_out TEXT,
        checked_in_by TEXT,
        checked_out_by TEXT,
        status TEXT DEFAULT 'Present',
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(classroom_id) REFERENCES classrooms(id)
    )
    ''')

    # Staff Attendance
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS staff_attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campus_id INTEGER DEFAULT 1,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        clock_in TEXT,
        clock_out TEXT,
        total_hours REAL DEFAULT 0,
        status TEXT DEFAULT 'Present',
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    # Staff Credentials & Audits
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS staff_credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        credential_name TEXT NOT NULL,
        issue_date TEXT,
        expiry_date TEXT,
        status TEXT DEFAULT 'Valid', -- Valid, Expiring Soon, Expired
        doc_ref TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    # Daily Activities (Daily Sheets)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        classroom_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        activity_type TEXT NOT NULL, -- nap, meal, potty, observation, photo, learning
        title TEXT NOT NULL,
        details TEXT,
        timestamp TEXT NOT NULL,
        metadata_json TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(classroom_id) REFERENCES classrooms(id),
        FOREIGN KEY(teacher_id) REFERENCES users(id)
    )
    ''')

    # Invoices & Billing
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campus_id INTEGER DEFAULT 1,
        student_id INTEGER NOT NULL,
        parent_id INTEGER NOT NULL,
        invoice_number TEXT UNIQUE NOT NULL,
        term_month TEXT NOT NULL,
        amount REAL NOT NULL,
        due_date TEXT NOT NULL,
        status TEXT DEFAULT 'Pending', -- Paid, Pending, Overdue, Pending Approval
        payment_method TEXT DEFAULT 'Pending', -- Cash, Cheque, UPI, Online Passthrough
        paid_at TEXT,
        receipt_number TEXT,
        parent_receipt_file TEXT,
        parent_txn_ref TEXT,
        parent_payment_date TEXT,
        approval_status TEXT DEFAULT 'None', -- None, Pending Approval, Approved, Rejected
        approved_by TEXT,
        approved_at TEXT,
        rejection_reason TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(parent_id) REFERENCES users(id)
    )
    ''')

    # Inventory & Supplies
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campus_id INTEGER DEFAULT 1,
        category TEXT NOT NULL, -- Hygiene, Art & Craft, Medical/First-Aid, Pantry
        item_name TEXT NOT NULL,
        current_stock INTEGER NOT NULL,
        min_threshold INTEGER NOT NULL,
        unit TEXT NOT NULL,
        last_restocked TEXT
    )
    ''')

    # Supply Requests Requisition Kanban
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS supply_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campus_id INTEGER DEFAULT 1,
        teacher_id INTEGER NOT NULL,
        classroom_id INTEGER NOT NULL,
        item_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        urgency TEXT DEFAULT 'Normal', -- Normal, High, Urgent
        status TEXT DEFAULT 'Pending', -- Pending, Approved, Dispatched, Fulfilled
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY(teacher_id) REFERENCES users(id),
        FOREIGN KEY(classroom_id) REFERENCES classrooms(id)
    )
    ''')

    # CACFP / Nutritional Food Program Menus
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS menus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campus_id INTEGER DEFAULT 1,
        day_of_week TEXT NOT NULL,
        meal_time TEXT NOT NULL, -- Breakfast, Morning Snack, Lunch, Afternoon Snack
        items_description TEXT NOT NULL,
        allergen_tags TEXT,
        calories INTEGER
    )
    ''')

    # Secure Two-Way Messaging
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        sender_role TEXT NOT NULL,
        message_text TEXT NOT NULL,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        read_status INTEGER DEFAULT 0,
        translated_text TEXT,
        FOREIGN KEY(sender_id) REFERENCES users(id),
        FOREIGN KEY(receiver_id) REFERENCES users(id)
    )
    ''')

    # Student Achievement Badges
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        badge_key TEXT NOT NULL,
        badge_title TEXT NOT NULL,
        badge_icon TEXT NOT NULL,
        category TEXT NOT NULL,
        unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        description TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    ''')

    # Digital Reading Logs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reading_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        book_title TEXT NOT NULL,
        author TEXT,
        pages INTEGER DEFAULT 1,
        sticker_icon TEXT DEFAULT '⭐',
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    ''')

    conn.commit()

    # Migration for invoices columns if database already existed
    columns_to_add = [
        ("parent_receipt_file", "TEXT"),
        ("parent_txn_ref", "TEXT"),
        ("parent_payment_date", "TEXT"),
        ("approval_status", "TEXT DEFAULT 'None'"),
        ("approved_by", "TEXT"),
        ("approved_at", "TEXT"),
        ("rejection_reason", "TEXT")
    ]
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type}")
            conn.commit()
        except sqlite3.OperationalError:
            pass # Already exists

    # Migration for students columns
    try:
        cursor.execute("ALTER TABLE students ADD COLUMN roll_number TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Ensure all students have roll numbers (e.g. LM-KHD-001)
    students = cursor.execute("SELECT id, roll_number FROM students").fetchall()
    for s in students:
        if not s['roll_number']:
            roll = f"LM-KHD-{s['id']:03d}"
            cursor.execute("UPDATE students SET roll_number = ? WHERE id = ?", (roll, s['id']))
    conn.commit()

    # Migration for messages columns
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN student_id INTEGER DEFAULT 4")
        cursor.execute("ALTER TABLE messages ADD COLUMN visible_to_director INTEGER DEFAULT 1")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Migration for fee engine enhancements
    invoice_cols = [
        ("base_fee", "REAL DEFAULT 14500.0"),
        ("arrears_carried_forward", "REAL DEFAULT 0.0"),
        ("credit_adjusted", "REAL DEFAULT 0.0"),
        ("amount_paid", "REAL DEFAULT 0.0"),
        ("balance_pending", "REAL DEFAULT 0.0"),
        ("notes", "TEXT")
    ]
    for col_name, col_type in invoice_cols:
        try:
            cursor.execute(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type}")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    # Ensure amount_paid and balance_pending are backfilled
    cursor.execute("""
    UPDATE invoices 
    SET base_fee = amount,
        amount_paid = CASE WHEN status = 'Paid' THEN amount ELSE 0 END,
        balance_pending = CASE WHEN status = 'Paid' THEN 0 ELSE amount END
    WHERE balance_pending = 0 AND status != 'Paid'
    """)
    conn.commit()

    student_fee_cols = [
        ("annual_fee", "REAL DEFAULT 174000.0"),
        ("monthly_base_fee", "REAL DEFAULT 14500.0"),
        ("credit_balance", "REAL DEFAULT 0.0")
    ]
    for col_name, col_type in student_fee_cols:
        try:
            cursor.execute(f"ALTER TABLE students ADD COLUMN {col_name} {col_type}")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    # Create fee_payments transaction log table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fee_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campus_id INTEGER DEFAULT 1,
        invoice_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        receipt_number TEXT UNIQUE NOT NULL,
        amount_paid REAL NOT NULL,
        previous_due REAL NOT NULL,
        balance_remaining REAL NOT NULL,
        credit_added REAL DEFAULT 0.0,
        payment_method TEXT NOT NULL,
        paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        recorded_by TEXT,
        notes TEXT,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id),
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    ''')
    conn.commit()

    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database schema successfully created!")
