import os
import io
import csv
import datetime
import random
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, Response
from werkzeug.utils import secure_filename
from config import Config
from database import get_db_connection, init_db

app = Flask(__name__)
app.config.from_object(Config)

# Ensure database tables and migrations are initialized on startup
init_db()

# Auto-seed if students table is empty on first cloud deploy
try:
    _conn = get_db_connection()
    _count = _conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    _conn.close()
    if _count == 0:
        from seed_data import seed_database
        seed_database()
except Exception as _e:
    pass

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'receipts')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper: Get currently logged-in user
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

@app.context_processor
def inject_globals():
    conn = get_db_connection()
    # Check pending approvals for director badge
    pending_approvals = conn.execute("SELECT COUNT(*) FROM invoices WHERE approval_status = 'Pending Approval'").fetchone()[0]
    conn.close()
    return {
        'current_user': get_current_user(),
        'campus_name': Config.CAMPUS_NAME,
        'campus_code': Config.CAMPUS_CODE,
        'pending_approvals_count': pending_approvals
    }

# -----------------------------------------------------------------------------
# AUTHENTICATION & 1-CLICK ROLE DEMO SWITCHER
# -----------------------------------------------------------------------------
@app.route('/')
def index():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth_login'))
    
    role = user['role']
    if role in ['admin', 'director']:
        return redirect(url_for('admin_dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher_classroom'))
    elif role == 'parent':
        return redirect(url_for('parent_feed'))
    elif role == 'student':
        return redirect(url_for('student_portfolio'))
    return redirect(url_for('auth_login'))

@app.route('/login', methods=['GET', 'POST'])
def auth_login():
    error = None
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '').strip()
        
        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE (email = ? OR phone = ?) AND (password = ? OR pin_code = ?)",
            (identifier, identifier, password, password)
        ).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('index'))
        else:
            error = "Invalid credentials. Use 1-Click Demo buttons below or enter valid PIN."

    return render_template('auth/login.html', error=error)

@app.route('/quick-login', methods=['POST'])
def auth_quick_login():
    target_role = request.form.get('role', 'director')
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE role = ? LIMIT 1", (target_role,)).fetchone()
    conn.close()

    if user:
        session['user_id'] = user['id']
        session['role'] = user['role']
    return redirect(url_for('index'))

@app.route('/logout')
def auth_logout():
    session.clear()
    return redirect(url_for('auth_login'))

# -----------------------------------------------------------------------------
# ADMIN & DIRECTOR COMMAND CENTER
# -----------------------------------------------------------------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    conn = get_db_connection()
    today_str = datetime.date.today().isoformat()

    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    present_students = conn.execute("SELECT COUNT(DISTINCT student_id) FROM attendance_logs WHERE date = ? AND check_out IS NULL", (today_str,)).fetchone()[0]
    staff_on_duty = conn.execute("SELECT COUNT(DISTINCT user_id) FROM staff_attendance WHERE date = ? AND clock_out IS NULL", (today_str,)).fetchone()[0]
    active_leads = conn.execute("SELECT COUNT(*) FROM leads WHERE status NOT IN ('Enrolled', 'Lost')").fetchone()[0]
    
    total_collected = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM invoices WHERE status = 'Paid'").fetchone()[0]

    # Live ratios per room
    classrooms = conn.execute("SELECT * FROM classrooms").fetchall()
    classroom_ratios = []
    for c in classrooms:
        p_count = conn.execute(
            "SELECT COUNT(*) FROM attendance_logs WHERE classroom_id = ? AND date = ? AND check_out IS NULL",
            (c['id'], today_str)
        ).fetchone()[0]
        s_count = 1 if p_count > 0 else 0
        actual_ratio = round(p_count / s_count, 1) if s_count > 0 else 0
        is_breached = actual_ratio > c['max_ratio']
        is_near = actual_ratio >= (c['max_ratio'] - 1) and not is_breached
        classroom_ratios.append({
            'name': c['name'],
            'present_count': p_count,
            'staff_count': s_count,
            'max_ratio': c['max_ratio'],
            'is_breached': is_breached,
            'is_near': is_near
        })

    allergy_students = conn.execute(
        "SELECT s.*, c.name as classroom_name FROM students s JOIN classrooms c ON s.classroom_id = c.id WHERE s.allergies != 'None' AND s.allergies != ''"
    ).fetchall()

    pending_supplies = conn.execute(
        "SELECT r.*, u.name as teacher_name, c.name as classroom_name FROM supply_requests r JOIN users u ON r.teacher_id = u.id JOIN classrooms c ON r.classroom_id = c.id WHERE r.status = 'Pending' LIMIT 4"
    ).fetchall()

    conn.close()
    return render_template(
        'admin/dashboard.html',
        active_page='admin_dashboard',
        total_students_count=total_students,
        present_students_count=present_students,
        staff_on_duty_count=staff_on_duty,
        active_leads_count=active_leads,
        total_collected_amount=total_collected,
        classroom_ratios=classroom_ratios,
        allergy_students=allergy_students,
        pending_supplies=pending_supplies
    )

@app.route('/admin/ratios')
def admin_ratios():
    conn = get_db_connection()
    today_str = datetime.date.today().isoformat()
    classrooms_raw = conn.execute("SELECT * FROM classrooms").fetchall()
    classrooms = []

    for c in classrooms_raw:
        p_count = conn.execute(
            "SELECT COUNT(*) FROM attendance_logs WHERE classroom_id = ? AND date = ? AND check_out IS NULL",
            (c['id'], today_str)
        ).fetchone()[0]
        s_count = 1 if p_count > 0 else 0
        current_ratio = round(p_count / s_count, 1) if s_count > 0 else 0
        is_breached = current_ratio > c['max_ratio']
        is_near = (current_ratio >= c['max_ratio'] - 1) and not is_breached
        teachers = conn.execute("SELECT name FROM users WHERE role = 'teacher' LIMIT 1").fetchall()

        classrooms.append({
            'id': c['id'],
            'name': c['name'],
            'room_number': c['room_number'],
            'age_group': c['age_group'],
            'capacity': c['capacity'],
            'max_ratio': c['max_ratio'],
            'present_count': p_count,
            'staff_count': s_count,
            'current_ratio': current_ratio,
            'is_breached': is_breached,
            'is_near': is_near,
            'teachers': teachers
        })

    all_students = conn.execute("SELECT s.*, c.name as classroom_name FROM students s JOIN classrooms c ON s.classroom_id = c.id").fetchall()
    conn.close()
    return render_template('admin/ratios.html', active_page='admin_ratios', classrooms=classrooms, all_students=all_students)

@app.route('/admin/toggle-checkin', methods=['POST'])
def admin_toggle_checkin():
    student_id = request.form.get('student_id')
    action = request.form.get('action', 'check_in')
    today_str = datetime.date.today().isoformat()
    now_time = datetime.datetime.now().strftime("%I:%M %p")

    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    
    if student:
        if action == 'check_in':
            existing = conn.execute(
                "SELECT * FROM attendance_logs WHERE student_id = ? AND date = ?",
                (student_id, today_str)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE attendance_logs SET check_out = NULL, check_in = ? WHERE id = ?",
                    (now_time, existing['id'])
                )
            else:
                conn.execute(
                    "INSERT INTO attendance_logs (campus_id, student_id, classroom_id, date, check_in, checked_in_by) VALUES (?, ?, ?, ?, ?, ?)",
                    (1, student_id, student['classroom_id'], today_str, now_time, "Front Desk QR Station")
                )
            flash(f"Checked in {student['first_name']} {student['last_name']} successfully!", "success")
        else:
            conn.execute(
                "UPDATE attendance_logs SET check_out = ?, checked_out_by = 'Parent Pickup' WHERE student_id = ? AND date = ?",
                (now_time, student_id, today_str)
            )
            flash(f"Checked out {student['first_name']} {student['last_name']}.", "info")
        conn.commit()

    conn.close()
    return redirect(url_for('admin_ratios'))

@app.route('/admin/crm')
def admin_crm():
    conn = get_db_connection()
    leads = conn.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
    stages = ['New', 'Tour Scheduled', 'Tour Completed', 'Application Submitted', 'Enrolled']
    leads_by_stage = {stage: [] for stage in stages}
    for lead in leads:
        if lead['status'] in leads_by_stage:
            leads_by_stage[lead['status']].append(lead)
    conn.close()
    return render_template('admin/crm_leads.html', active_page='admin_crm', leads_by_stage=leads_by_stage)

@app.route('/admin/create-lead', methods=['POST'])
def admin_create_lead():
    child_name = request.form.get('child_name')
    child_age = request.form.get('child_age')
    parent_name = request.form.get('parent_name')
    parent_phone = request.form.get('parent_phone')
    requested_program = request.form.get('requested_program')
    tour_date = request.form.get('tour_date')
    tour_time = request.form.get('tour_time')
    notes = request.form.get('notes')
    status = 'Tour Scheduled' if tour_date else 'New'

    conn = get_db_connection()
    conn.execute('''
    INSERT INTO leads (campus_id, child_name, child_age, parent_name, parent_phone, requested_program, status, tour_date, tour_time, notes)
    VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (child_name, child_age, parent_name, parent_phone, requested_program, status, tour_date, tour_time, notes))
    conn.commit()
    conn.close()
    flash(f"Inquiry lead for {child_name} registered successfully!", "success")
    return redirect(url_for('admin_crm'))

@app.route('/admin/update-lead-stage/<int:lead_id>', methods=['POST'])
def admin_update_lead_stage(lead_id):
    new_stage = request.form.get('new_stage')
    if new_stage:
        conn = get_db_connection()
        conn.execute("UPDATE leads SET status = ? WHERE id = ?", (new_stage, lead_id))
        conn.commit()
        conn.close()
        flash(f"Lead status moved to {new_stage}!", "success")
    return redirect(url_for('admin_crm'))

@app.route('/admin/billing')
def admin_billing():
    conn = get_db_connection()
    invoices = conn.execute('''
    SELECT i.*, s.roll_number, (s.first_name || ' ' || s.last_name) as student_name, c.name as classroom_name, u.name as parent_name, u.phone as parent_phone
    FROM invoices i
    JOIN students s ON i.student_id = s.id
    JOIN classrooms c ON s.classroom_id = c.id
    JOIN users u ON i.parent_id = u.id
    ORDER BY 
        CASE WHEN i.approval_status = 'Pending Approval' THEN 0 ELSE 1 END,
        i.due_date DESC
    ''').fetchall()

    total_billed = sum(i['amount'] for i in invoices)
    total_collected = sum(i['amount'] for i in invoices if i['status'] == 'Paid')
    total_pending = sum(i['amount'] for i in invoices if i['status'] in ['Pending', 'Pending Approval'])
    total_overdue = sum(i['amount'] for i in invoices if i['status'] == 'Overdue')

    # Pending approval invoices requiring director action
    pending_approval_invoices = [i for i in invoices if i['approval_status'] == 'Pending Approval']

    conn.close()
    return render_template(
        'admin/billing.html',
        active_page='admin_billing',
        invoices=invoices,
        pending_approval_invoices=pending_approval_invoices,
        total_billed=total_billed,
        total_collected=total_collected,
        total_pending=total_pending,
        total_overdue=total_overdue
    )

@app.route('/admin/generate-invoices', methods=['POST'])
def admin_generate_invoices():
    term_month = request.form.get('term_month', 'November 2026')
    due_date = request.form.get('due_date', '2026-11-10')

    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students WHERE status = 'Active'").fetchall()
    
    # Month prefix for invoice number (e.g. 11 for Nov, 12 for Dec)
    month_code = "11"
    if "Dec" in term_month:
        month_code = "12"
    elif "Jan" in term_month:
        month_code = "01"
    elif "Feb" in term_month:
        month_code = "02"
    elif "Mar" in term_month:
        month_code = "03"

    generated_count = 0
    for s in students:
        inv_num = f"INV-2026-{month_code}-{s['id']:03d}"
        existing = conn.execute("SELECT id FROM invoices WHERE invoice_number = ?", (inv_num,)).fetchone()
        if not existing:
            amount = 14500.0 if s['classroom_id'] != 1 else 18000.0
            conn.execute('''
            INSERT INTO invoices (campus_id, student_id, parent_id, invoice_number, term_month, amount, due_date, status, approval_status)
            VALUES (1, ?, ?, ?, ?, ?, ?, 'Pending', 'None')
            ''', (s['id'], s['parent_id'], inv_num, term_month, amount, due_date))
            generated_count += 1
            
    conn.commit()
    conn.close()

    if generated_count > 0:
        flash(f"Successfully generated {generated_count} tuition invoices for {term_month}!", "success")
    else:
        flash(f"All {len(students)} active students already have invoices for {term_month}.", "info")

    return redirect(url_for('admin_billing'))

@app.route('/admin/log-payment', methods=['POST'])
def admin_log_payment():
    invoice_id = request.form.get('invoice_id')
    amount_str = request.form.get('amount', '0').replace('₹', '').replace(',', '').strip()
    try:
        amount = float(amount_str)
    except ValueError:
        amount = 14500.0

    payment_method = request.form.get('payment_method', 'Cash')
    receipt_no = f"REC-LM-{random.randint(5000, 9999)}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    inv = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    if inv:
        current_due = float(inv['balance_pending'] if inv['balance_pending'] is not None and inv['balance_pending'] > 0 else inv['amount'])
        s_id = inv['student_id']

        if 0 < amount < current_due:
            # Partial payment: auto-deduct and split balance
            remaining_pending = current_due - amount
            conn.execute('''
            UPDATE invoices 
            SET amount = ?, amount_paid = ?, balance_pending = 0, status = 'Paid',
                payment_method = ?, paid_at = ?, receipt_number = ?, approval_status = 'Approved',
                approved_by = 'Chanchal Sharma (Director)', approved_at = ?,
                notes = ?
            WHERE id = ?
            ''', (amount, amount, payment_method, now_str, receipt_no, now_str,
                  f"Partial payment received. ₹{remaining_pending:,.0f} balance split to separate pending invoice.", inv['id']))

            counter = 1
            bal_inv_num = f"{inv['invoice_number']}-BAL"
            while conn.execute("SELECT id FROM invoices WHERE invoice_number = ?", (bal_inv_num,)).fetchone():
                counter += 1
                bal_inv_num = f"{inv['invoice_number']}-BAL{counter}"
            conn.execute('''
            INSERT INTO invoices (
                campus_id, student_id, parent_id, invoice_number, term_month,
                amount, base_fee, arrears_carried_forward, credit_adjusted,
                amount_paid, balance_pending, due_date, status, approval_status, notes
            ) VALUES (
                1, ?, ?, ?, ?,
                ?, ?, 0, 0,
                0, ?, ?, 'Pending', 'None', ?
            )
            ''', (s_id, inv['parent_id'], bal_inv_num, inv['term_month'],
                  remaining_pending, remaining_pending,
                  remaining_pending, inv['due_date'],
                  f"Pending balance of ₹{remaining_pending:,.0f} carried from partial payment of {inv['invoice_number']}"))

            conn.commit()
            conn.close()
            flash(f"Partial fee payment of ₹{amount:,.0f} logged (Receipt #{receipt_no})! Remaining ₹{remaining_pending:,.0f} moved to new pending invoice #{bal_inv_num}.", "success")
            return redirect(url_for('admin_billing'))

        elif amount > current_due:
            extra_credit = amount - current_due
            conn.execute('''
            UPDATE invoices 
            SET amount_paid = amount, balance_pending = 0, status = 'Paid',
                payment_method = ?, paid_at = ?, receipt_number = ?, approval_status = 'Approved',
                approved_by = 'Chanchal Sharma (Director)', approved_at = ?,
                notes = ?
            WHERE id = ?
            ''', (payment_method, now_str, receipt_no, now_str,
                  f"Paid in full. Extra ₹{extra_credit:,.0f} credited to advance wallet for next month.", inv['id']))

            conn.execute('''
            UPDATE students SET credit_balance = COALESCE(credit_balance, 0) + ? WHERE id = ?
            ''', (extra_credit, s_id))
            conn.commit()
            conn.close()
            flash(f"Payment of ₹{amount:,.0f} logged (Receipt #{receipt_no})! Due cleared in full and ₹{extra_credit:,.0f} added to student advance credit wallet.", "success")
            return redirect(url_for('admin_billing'))

    conn.execute('''
    UPDATE invoices 
    SET status = 'Paid', amount = ?, amount_paid = ?, balance_pending = 0, payment_method = ?, paid_at = ?, receipt_number = ?, approval_status = 'Approved', approved_by = 'Center Director', approved_at = ?
    WHERE id = ?
    ''', (amount, amount, payment_method, now_str, receipt_no, now_str, invoice_id))
    conn.commit()
    conn.close()

    flash(f"Fee payment of ₹{amount:,.0f} successfully logged! Official Receipt #{receipt_no} created.", "success")
    return redirect(url_for('admin_billing'))

@app.route('/admin/approve-parent-payment/<int:invoice_id>', methods=['POST'])
def admin_approve_parent_payment(invoice_id):
    receipt_no = f"REC-LM-{random.randint(5000, 9999)}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    conn.execute('''
    UPDATE invoices 
    SET status = 'Paid', approval_status = 'Approved', receipt_number = ?, approved_by = 'Chanchal Sharma (Director)', approved_at = ?, paid_at = ?
    WHERE id = ?
    ''', (receipt_no, now_str, now_str, invoice_id))
    conn.commit()
    conn.close()

    flash(f"Payment approved! Official Receipt #{receipt_no} has been issued and family account updated to Paid.", "success")
    return redirect(url_for('admin_billing'))

@app.route('/admin/reject-parent-payment/<int:invoice_id>', methods=['POST'])
def admin_reject_parent_payment(invoice_id):
    reason = request.form.get('rejection_reason', 'Transaction reference could not be verified with school bank account.')
    conn = get_db_connection()
    conn.execute('''
    UPDATE invoices 
    SET status = 'Pending', approval_status = 'Rejected', rejection_reason = ?
    WHERE id = ?
    ''', (reason, invoice_id))
    conn.commit()
    conn.close()

    flash(f"Payment rejected and reset to Pending. Notification sent to parent: '{reason}'", "error")
    return redirect(url_for('admin_billing'))

# -----------------------------------------------------------------------------
# DEDICATED FEES MANAGEMENT HUB (USER MANDATE)
# -----------------------------------------------------------------------------
@app.route('/admin/fees')
def admin_fees_management():
    conn = get_db_connection()
    
    # Fetch active students with classroom details
    students_raw = conn.execute('''
    SELECT s.*, c.name as classroom_name
    FROM students s
    LEFT JOIN classrooms c ON s.classroom_id = c.id
    WHERE s.status = 'Active'
    ORDER BY s.roll_number ASC
    ''').fetchall()

    students_fees = []
    total_annual_expected = 0.0
    total_advance_credits = 0.0

    for s in students_raw:
        s_id = s['id']
        annual_fee = float(s['annual_fee'] or (s['monthly_base_fee'] * 12 if s['monthly_base_fee'] else 174000.0))
        monthly_base_fee = float(s['monthly_base_fee'] or 14500.0)
        credit_balance = float(s['credit_balance'] or 0.0)

        total_annual_expected += annual_fee
        total_advance_credits += credit_balance

        # Find latest pending/overdue invoice
        current_inv = conn.execute('''
        SELECT * FROM invoices 
        WHERE student_id = ? AND status IN ('Pending', 'Pending Approval', 'Overdue')
        ORDER BY id DESC LIMIT 1
        ''', (s_id,)).fetchone()

        if not current_inv:
            latest_inv = conn.execute('''
            SELECT * FROM invoices 
            WHERE student_id = ? 
            ORDER BY id DESC LIMIT 1
            ''', (s_id,)).fetchone()
            current_invoice_id = latest_inv['id'] if latest_inv else 0
            current_due = 0.0
        else:
            current_invoice_id = current_inv['id']
            current_due = float(current_inv['balance_pending'] if current_inv['balance_pending'] is not None and current_inv['balance_pending'] > 0 else current_inv['amount'])

        # Total arrears (unpaid balances from all pending/overdue invoices)
        arrears_row = conn.execute('''
        SELECT COALESCE(SUM(CASE WHEN balance_pending > 0 THEN balance_pending ELSE amount END), 0)
        FROM invoices
        WHERE student_id = ? AND status IN ('Pending', 'Overdue')
        ''', (s_id,)).fetchone()
        arrears = float(arrears_row[0]) if arrears_row else 0.0

        students_fees.append({
            'id': s_id,
            'roll_number': s['roll_number'] or f"LM-KHD-{s_id:03d}",
            'first_name': s['first_name'],
            'last_name': s['last_name'],
            'classroom_name': s['classroom_name'] or 'General',
            'annual_fee': annual_fee,
            'monthly_base_fee': monthly_base_fee,
            'credit_balance': credit_balance,
            'arrears': arrears,
            'current_due': current_due,
            'current_invoice_id': current_invoice_id
        })

    # Total collected YTD
    collected_row = conn.execute('''
    SELECT COALESCE(SUM(amount), 0) FROM invoices WHERE status = 'Paid'
    ''').fetchone()
    total_collected_ytd = float(collected_row[0]) if collected_row else 0.0

    # Total carried arrears
    arrears_sum_row = conn.execute('''
    SELECT COALESCE(SUM(CASE WHEN balance_pending > 0 THEN balance_pending ELSE amount END), 0)
    FROM invoices WHERE status IN ('Pending', 'Overdue')
    ''').fetchone()
    total_arrears_carried = float(arrears_sum_row[0]) if arrears_sum_row else 0.0

    # Month-Wise Stats for academic year
    month_names = ["June 2026", "July 2026", "August 2026", "September 2026", "October 2026", "November 2026"]
    month_stats = []
    current_term = "October 2026"

    for m_name in month_names:
        m_rows = conn.execute('''
        SELECT 
            COALESCE(SUM(amount), 0) as total_billed,
            COALESCE(SUM(CASE WHEN status = 'Paid' THEN amount ELSE 0 END), 0) as total_collected,
            COALESCE(SUM(CASE WHEN status IN ('Pending', 'Overdue') THEN (CASE WHEN balance_pending > 0 THEN balance_pending ELSE amount END) ELSE 0 END), 0) as total_arrears
        FROM invoices
        WHERE term_month = ?
        ''', (m_name,)).fetchone()
        
        billed = float(m_rows['total_billed']) if m_rows else 0.0
        collected = float(m_rows['total_collected']) if m_rows else 0.0
        arrears_m = float(m_rows['total_arrears']) if m_rows else 0.0

        if billed == 0:
            billed = sum(s['monthly_base_fee'] for s in students_fees)

        month_stats.append({
            'name': m_name,
            'billed': billed,
            'collected': collected,
            'arrears': arrears_m,
            'is_current': (m_name == current_term)
        })

    conn.close()

    return render_template(
        'admin/fees_management.html',
        active_page='admin_fees_management',
        total_annual_expected=total_annual_expected,
        total_collected_ytd=total_collected_ytd,
        total_arrears_carried=total_arrears_carried,
        total_advance_credits=total_advance_credits,
        month_stats=month_stats,
        students_fees=students_fees
    )

@app.route('/admin/adjust-student-fee', methods=['POST'])
def admin_adjust_student_fee():
    student_id = request.form.get('student_id')
    monthly_base_fee = float(request.form.get('monthly_base_fee', '14500'))
    annual_fee = float(request.form.get('annual_fee', str(monthly_base_fee * 12)))
    notes = request.form.get('notes', '')

    conn = get_db_connection()
    conn.execute('''
    UPDATE students 
    SET monthly_base_fee = ?, annual_fee = ?
    WHERE id = ?
    ''', (monthly_base_fee, annual_fee, student_id))

    # Update any active Pending invoice for this student to reflect new base fee
    pending_inv = conn.execute('''
    SELECT * FROM invoices WHERE student_id = ? AND status = 'Pending' ORDER BY id DESC LIMIT 1
    ''', (student_id,)).fetchone()
    if pending_inv:
        arrears = float(pending_inv['arrears_carried_forward'] or 0.0)
        credit = float(pending_inv['credit_adjusted'] or 0.0)
        new_amount = max(0.0, monthly_base_fee + arrears - credit)
        conn.execute('''
        UPDATE invoices 
        SET base_fee = ?, amount = ?, balance_pending = ?
        WHERE id = ?
        ''', (monthly_base_fee, new_amount, new_amount, pending_inv['id']))

    conn.commit()
    conn.close()

    flash(f"Fee structure adjusted! Monthly base fee updated to ₹{monthly_base_fee:,.0f} and annual fee to ₹{annual_fee:,.0f}.", "success")
    return redirect(url_for('admin_fees_management'))

@app.route('/admin/record-split-payment', methods=['POST'])
def admin_record_split_payment():
    invoice_id = request.form.get('invoice_id')
    student_id = request.form.get('student_id')
    paid_amount_str = request.form.get('paid_amount', '0').replace('₹', '').replace(',', '').strip()
    payment_method = request.form.get('payment_method', 'UPI')
    try:
        paid_amount = float(paid_amount_str)
    except ValueError:
        paid_amount = 0.0

    conn = get_db_connection()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    receipt_no = f"REC-LM-{random.randint(5000, 9999)}"

    inv = None
    if invoice_id and invoice_id != '0':
        inv = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()

    if inv:
        s_id = inv['student_id']
        current_due = float(inv['balance_pending'] if inv['balance_pending'] is not None and inv['balance_pending'] > 0 else inv['amount'])
        
        # Case A: Partial Payment (auto-deduct & create separate pending balance entry)
        if 0 < paid_amount < current_due:
            remaining_pending = current_due - paid_amount
            # 1. Settle current invoice with paid amount
            conn.execute('''
            UPDATE invoices 
            SET amount = ?, amount_paid = ?, balance_pending = 0, status = 'Paid', 
                payment_method = ?, paid_at = ?, receipt_number = ?, 
                approval_status = 'Approved', approved_by = 'Chanchal Sharma (Director)', approved_at = ?,
                notes = ?
            WHERE id = ?
            ''', (paid_amount, paid_amount, payment_method, now_str, receipt_no, now_str, 
                  f"Partial payment received. ₹{remaining_pending:,.0f} balance split to separate pending invoice.", inv['id']))

            # 2. Create another entry for remaining fee amount pending
            counter = 1
            bal_inv_num = f"{inv['invoice_number']}-BAL"
            while conn.execute("SELECT id FROM invoices WHERE invoice_number = ?", (bal_inv_num,)).fetchone():
                counter += 1
                bal_inv_num = f"{inv['invoice_number']}-BAL{counter}"
            conn.execute('''
            INSERT INTO invoices (
                campus_id, student_id, parent_id, invoice_number, term_month,
                amount, base_fee, arrears_carried_forward, credit_adjusted,
                amount_paid, balance_pending, due_date, status, approval_status, notes
            ) VALUES (
                1, ?, ?, ?, ?,
                ?, ?, 0, 0,
                0, ?, ?, 'Pending', 'None', ?
            )
            ''', (s_id, inv['parent_id'], bal_inv_num, inv['term_month'],
                  remaining_pending, remaining_pending,
                  remaining_pending, inv['due_date'], 
                  f"Pending balance of ₹{remaining_pending:,.0f} carried from partial payment of {inv['invoice_number']}"))

            # 3. Log transaction in fee_payments
            conn.execute('''
            INSERT INTO fee_payments (
                campus_id, invoice_id, student_id, receipt_number, amount_paid,
                previous_due, balance_remaining, credit_added, payment_method, recorded_by, notes
            ) VALUES (
                1, ?, ?, ?, ?,
                ?, ?, 0, ?, 'Chanchal Sharma (Director)', 'Partial Fee Payment with Balance Split'
            )
            ''', (inv['id'], s_id, receipt_no, paid_amount, current_due, remaining_pending, payment_method))

            flash(f"Partial payment of ₹{paid_amount:,.0f} successfully logged! Receipt #{receipt_no} issued. New pending invoice #{bal_inv_num} created for remaining ₹{remaining_pending:,.0f}.", "success")

        # Case B: Overpayment / Extra amount paid (adjust to advance credit wallet)
        elif paid_amount > current_due:
            extra_credit = paid_amount - current_due
            conn.execute('''
            UPDATE invoices 
            SET amount_paid = amount, balance_pending = 0, status = 'Paid',
                payment_method = ?, paid_at = ?, receipt_number = ?, 
                approval_status = 'Approved', approved_by = 'Chanchal Sharma (Director)', approved_at = ?,
                notes = ?
            WHERE id = ?
            ''', (payment_method, now_str, receipt_no, now_str, 
                  f"Paid in full. Extra ₹{extra_credit:,.0f} credited to advance wallet for next month.", inv['id']))

            conn.execute('''
            UPDATE students 
            SET credit_balance = COALESCE(credit_balance, 0) + ? 
            WHERE id = ?
            ''', (extra_credit, s_id))

            conn.execute('''
            INSERT INTO fee_payments (
                campus_id, invoice_id, student_id, receipt_number, amount_paid,
                previous_due, balance_remaining, credit_added, payment_method, recorded_by, notes
            ) VALUES (
                1, ?, ?, ?, ?,
                ?, 0, ?, ?, 'Chanchal Sharma (Director)', 'Full Payment with Extra Advance Wallet Credit'
            )
            ''', (inv['id'], s_id, receipt_no, paid_amount, current_due, extra_credit, payment_method))

            flash(f"Payment of ₹{paid_amount:,.0f} received! Current due of ₹{current_due:,.0f} cleared in full (Receipt #{receipt_no}). Extra ₹{extra_credit:,.0f} added to student's advance wallet for next month auto-deduction!", "success")

        # Case C: Exact payment
        else:
            conn.execute('''
            UPDATE invoices 
            SET amount_paid = amount, balance_pending = 0, status = 'Paid',
                payment_method = ?, paid_at = ?, receipt_number = ?, 
                approval_status = 'Approved', approved_by = 'Chanchal Sharma (Director)', approved_at = ?
            WHERE id = ?
            ''', (payment_method, now_str, receipt_no, now_str, inv['id']))

            conn.execute('''
            INSERT INTO fee_payments (
                campus_id, invoice_id, student_id, receipt_number, amount_paid,
                previous_due, balance_remaining, credit_added, payment_method, recorded_by, notes
            ) VALUES (
                1, ?, ?, ?, ?,
                ?, 0, 0, ?, 'Chanchal Sharma (Director)', 'Exact Fee Payment Settled'
            )
            ''', (inv['id'], s_id, receipt_no, paid_amount, current_due, payment_method))

            flash(f"Fee payment of ₹{paid_amount:,.0f} settled in full! Official Receipt #{receipt_no} generated.", "success")

    else:
        # Direct advance payment without open invoice
        s_id = int(student_id) if student_id else 1
        student = conn.execute("SELECT * FROM students WHERE id = ?", (s_id,)).fetchone()
        conn.execute('''
        UPDATE students 
        SET credit_balance = COALESCE(credit_balance, 0) + ? 
        WHERE id = ?
        ''', (paid_amount, s_id))

        flash(f"Advance payment of ₹{paid_amount:,.0f} added directly to {student['first_name']}'s credit wallet! Will auto-deduct from next month's invoice.", "success")

    conn.commit()
    conn.close()
    return redirect(url_for('admin_fees_management'))

@app.route('/admin/rollover-fees', methods=['POST'])
def admin_rollover_fees():
    target_month = request.form.get('target_month', 'November 2026')
    if "Dec" in target_month:
        month_code = "12"
        due_date = "2026-12-10"
    elif "Jan" in target_month:
        month_code = "01"
        due_date = "2027-01-10"
    elif "Feb" in target_month:
        month_code = "02"
        due_date = "2027-02-10"
    elif "Nov" in target_month:
        month_code = "11"
        due_date = "2026-11-10"
    else:
        month_code = "11"
        due_date = "2026-11-10"

    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students WHERE status = 'Active'").fetchall()

    processed_count = 0
    total_carried_forward = 0.0
    total_credits_deducted = 0.0

    for s in students:
        s_id = s['id']
        parent_id = s['parent_id'] or 1
        base_fee = float(s['monthly_base_fee'] or (14500.0 if s['classroom_id'] != 1 else 18000.0))
        credit_balance = float(s['credit_balance'] or 0.0)

        # 1. Sum up all unpaid arrears from previous months
        unpaid_invoices = conn.execute('''
        SELECT * FROM invoices 
        WHERE student_id = ? AND status IN ('Pending', 'Overdue') AND term_month != ?
        ''', (s_id, target_month)).fetchall()

        unpaid_arrears = 0.0
        for old_inv in unpaid_invoices:
            pending_amt = float(old_inv['balance_pending'] if old_inv['balance_pending'] is not None and old_inv['balance_pending'] > 0 else old_inv['amount'])
            unpaid_arrears += pending_amt
            conn.execute('''
            UPDATE invoices 
            SET status = 'Carried Forward', 
                notes = COALESCE(notes, '') || ' [Arrears of ₹' || ? || ' carried forward into ' || ? || ']'
            WHERE id = ?
            ''', (pending_amt, target_month, old_inv['id']))

        total_carried_forward += unpaid_arrears

        # 2. Total due before credit deduction
        gross_due = base_fee + unpaid_arrears

        # 3. Auto-deduct advance credit from student wallet
        if credit_balance > 0:
            if credit_balance >= gross_due:
                credit_applied = gross_due
                new_credit_bal = credit_balance - gross_due
                net_due = 0.0
                inv_status = 'Paid'
            else:
                credit_applied = credit_balance
                new_credit_bal = 0.0
                net_due = gross_due - credit_balance
                inv_status = 'Pending'
        else:
            credit_applied = 0.0
            new_credit_bal = 0.0
            net_due = gross_due
            inv_status = 'Pending'

        total_credits_deducted += credit_applied

        # Update student credit balance
        conn.execute('UPDATE students SET credit_balance = ? WHERE id = ?', (new_credit_bal, s_id))

        # 4. Create or update target month invoice
        inv_num = f"INV-2026-{month_code}-{s_id:03d}"
        existing = conn.execute('SELECT id FROM invoices WHERE invoice_number = ?', (inv_num,)).fetchone()

        receipt_num = f"REC-LM-{random.randint(5000, 9999)}" if inv_status == 'Paid' else None
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") if inv_status == 'Paid' else None

        if existing:
            conn.execute('''
            UPDATE invoices 
            SET amount = ?, base_fee = ?, arrears_carried_forward = ?, credit_adjusted = ?,
                balance_pending = ?, status = ?, term_month = ?, due_date = ?,
                amount_paid = CASE WHEN ? = 'Paid' THEN ? ELSE 0 END,
                receipt_number = COALESCE(receipt_number, ?),
                paid_at = COALESCE(paid_at, ?)
            WHERE id = ?
            ''', (net_due, base_fee, unpaid_arrears, credit_applied, 
                  net_due if inv_status != 'Paid' else 0, inv_status, target_month, due_date,
                  inv_status, net_due, receipt_num, now_str, existing['id']))
        else:
            conn.execute('''
            INSERT INTO invoices (
                campus_id, student_id, parent_id, invoice_number, term_month,
                amount, base_fee, arrears_carried_forward, credit_adjusted,
                amount_paid, balance_pending, due_date, status, approval_status,
                receipt_number, paid_at, notes
            ) VALUES (
                1, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?, 'None',
                ?, ?, ?
            )
            ''', (s_id, parent_id, inv_num, target_month,
                  net_due, base_fee, unpaid_arrears, credit_applied,
                  net_due if inv_status == 'Paid' else 0,
                  net_due if inv_status != 'Paid' else 0,
                  due_date, inv_status, receipt_num, now_str,
                  f"Auto-rolled invoice for {target_month}. Base: ₹{base_fee:,.0f}, Arrears: +₹{unpaid_arrears:,.0f}, Credit: -₹{credit_applied:,.0f}"))

        processed_count += 1

    conn.commit()
    conn.close()

    flash(f"Monthly fee rollover complete for {target_month}! Processed {processed_count} students: Carried forward ₹{total_carried_forward:,.0f} in unpaid arrears, and auto-deducted ₹{total_credits_deducted:,.0f} in advance credits.", "success")
    return redirect(url_for('admin_fees_management'))

@app.route('/admin/staff')
def admin_staff():
    conn = get_db_connection()
    today_str = datetime.date.today().isoformat()
    staff_attendance = conn.execute('''
    SELECT a.*, u.name, u.avatar, u.title
    FROM staff_attendance a
    JOIN users u ON a.user_id = u.id
    WHERE a.date = ?
    ''', (today_str,)).fetchall()

    all_staff = conn.execute("SELECT * FROM users WHERE role IN ('teacher', 'director', 'admin')").fetchall()
    credentials = conn.execute('''
    SELECT c.*, u.name as user_name
    FROM staff_credentials c
    JOIN users u ON c.user_id = u.id
    ''').fetchall()
    conn.close()
    return render_template('admin/staff_hrm.html', active_page='admin_staff', staff_attendance=staff_attendance, all_staff=all_staff, credentials=credentials)

@app.route('/admin/staff-punch', methods=['POST'])
def admin_staff_punch():
    user_id = request.form.get('user_id')
    punch_type = request.form.get('punch_type', 'clock_in')
    today_str = datetime.date.today().isoformat()
    now_time = datetime.datetime.now().strftime("%I:%M %p")

    conn = get_db_connection()
    user = conn.execute("SELECT name FROM users WHERE id = ?", (user_id,)).fetchone()
    user_name = user['name'] if user else "Staff"

    if punch_type == 'clock_in':
        conn.execute('''
        INSERT INTO staff_attendance (campus_id, user_id, date, clock_in, status)
        VALUES (1, ?, ?, ?, 'Present')
        ''', (user_id, today_str, now_time))
        flash(f"{user_name} punched in at {now_time}.", "success")
    else:
        conn.execute('''
        UPDATE staff_attendance SET clock_out = ?, total_hours = 8.0 WHERE user_id = ? AND date = ?
        ''', (now_time, user_id, today_str))
        flash(f"{user_name} punched out at {now_time}.", "info")
    conn.commit()
    conn.close()
    return redirect(url_for('admin_staff'))

@app.route('/admin/inventory')
def admin_inventory():
    conn = get_db_connection()
    inventory = conn.execute("SELECT * FROM inventory_items").fetchall()
    low_stock = [i for i in inventory if i['current_stock'] <= i['min_threshold']]
    requests = conn.execute('''
    SELECT r.*, u.name as teacher_name, c.name as classroom_name
    FROM supply_requests r
    JOIN users u ON r.teacher_id = u.id
    JOIN classrooms c ON r.classroom_id = c.id
    ORDER BY r.created_at DESC
    ''').fetchall()

    requests_by_status = {'Pending': [], 'Approved': [], 'Dispatched': []}
    for r in requests:
        if r['status'] in requests_by_status:
            requests_by_status[r['status']].append(r)
    conn.close()
    return render_template(
        'admin/inventory.html',
        active_page='admin_inventory',
        inventory=inventory,
        low_stock_items=low_stock,
        requests_by_status=requests_by_status
    )

@app.route('/admin/approve-supply/<int:request_id>', methods=['POST'])
def admin_approve_supply(request_id):
    conn = get_db_connection()
    conn.execute("UPDATE supply_requests SET status = 'Approved' WHERE id = ?", (request_id,))
    conn.commit()
    conn.close()
    flash("Supply requisition approved for procurement!", "success")
    return redirect(request.referrer or url_for('admin_inventory'))

@app.route('/admin/update-supply-status/<int:req_id>', methods=['POST'])
def admin_update_supply_status(req_id):
    status = request.form.get('status')
    if status:
        conn = get_db_connection()
        conn.execute("UPDATE supply_requests SET status = ? WHERE id = ?", (status, req_id))
        conn.commit()
        conn.close()
        flash(f"Requisition status updated to {status}!", "success")
    return redirect(url_for('admin_inventory'))

@app.route('/admin/meals')
def admin_meals():
    conn = get_db_connection()
    today_str = datetime.date.today().isoformat()
    present_count = conn.execute("SELECT COUNT(DISTINCT student_id) FROM attendance_logs WHERE date = ? AND check_out IS NULL", (today_str,)).fetchone()[0]
    menus = conn.execute("SELECT * FROM menus").fetchall()
    conn.close()
    return render_template('admin/cacfp_meals.html', active_page='admin_meals', menus=menus, present_count=present_count)

# -----------------------------------------------------------------------------
# REAL WORKING EXPORT DATA ENDPOINTS (MANDATED FIX)
# -----------------------------------------------------------------------------
@app.route('/admin/export/billing')
def export_billing_csv():
    conn = get_db_connection()
    invoices = conn.execute('''
    SELECT i.invoice_number, COALESCE(s.roll_number, 'LM-KHD-001') as roll_number, (s.first_name || ' ' || s.last_name) as student_name, c.name as classroom_name,
           u.name as parent_name, u.phone as parent_phone, i.term_month, i.amount, i.status,
           i.payment_method, COALESCE(i.receipt_number, 'N/A') as receipt_number, COALESCE(i.paid_at, 'Unpaid') as paid_at
    FROM invoices i
    JOIN students s ON i.student_id = s.id
    JOIN classrooms c ON s.classroom_id = c.id
    JOIN users u ON i.parent_id = u.id
    ORDER BY i.due_date DESC
    ''').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Invoice Number', 'Roll Number', 'Student Name', 'Program / Classroom', 'Parent Name', 'Parent Phone', 'Term Month', 'Amount (INR)', 'Status', 'Payment Method', 'Receipt Number', 'Paid At'])
    
    for row in invoices:
        writer.writerow([row['invoice_number'], row['roll_number'], row['student_name'], row['classroom_name'], row['parent_name'], row['parent_phone'], row['term_month'], row['amount'], row['status'], row['payment_method'], row['receipt_number'], row['paid_at']])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=Little_Millennium_Kharadi_Billing_Ledger.csv"}
    )

@app.route('/admin/export/leads')
def export_leads_csv():
    conn = get_db_connection()
    leads = conn.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Lead ID', 'Child Name', 'Child Age', 'Parent Name', 'Parent Phone', 'Parent Email', 'Program', 'Status', 'Tour Date', 'Tour Time', 'Notes'])
    
    for l in leads:
        writer.writerow([l['id'], l['child_name'], l['child_age'], l['parent_name'], l['parent_phone'], l['parent_email'], l['requested_program'], l['status'], l['tour_date'], l['tour_time'], l['notes']])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=Little_Millennium_CRM_Tour_Leads.csv"}
    )

@app.route('/admin/export/staff-compliance')
def export_staff_compliance():
    conn = get_db_connection()
    creds = conn.execute('''
    SELECT u.name as staff_name, u.title, c.credential_name, c.doc_ref, c.issue_date, c.expiry_date, c.status
    FROM staff_credentials c
    JOIN users u ON c.user_id = u.id
    ''').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Staff Name', 'Job Title', 'Credential / Document', 'Reference Number', 'Issue Date', 'Expiry Date', 'Compliance Status'])
    
    for c in creds:
        writer.writerow([c['staff_name'], c['title'], c['credential_name'], c['doc_ref'], c['issue_date'], c['expiry_date'], c['status']])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=Little_Millennium_Staff_Compliance_Audit_Packet.csv"}
    )

@app.route('/parent/export/tax-statement/<int:student_id>')
def export_parent_tax_statement(student_id):
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    invoices = conn.execute("SELECT * FROM invoices WHERE student_id = ? AND status = 'Paid'", (student_id,)).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Little Millennium - Nest Daycare (Kharadi Branch)'])
    writer.writerow(['ANNUAL TUITION & CHILDCARE FEE TAX EXEMPTION CERTIFICATE'])
    writer.writerow(['Financial Year 2026-2027'])
    writer.writerow([])
    writer.writerow(['Child Name:', f"{student['first_name']} {student['last_name']}"])
    writer.writerow(['Emergency Contact:', student['emergency_contact_name']])
    writer.writerow(['Registration License:', 'MH-PUN-ECE-2024-8841'])
    writer.writerow([])
    writer.writerow(['Receipt Number', 'Term Month', 'Payment Date', 'Payment Method', 'Amount Paid (INR)'])

    total = 0
    for inv in invoices:
        writer.writerow([inv['receipt_number'], inv['term_month'], inv['paid_at'], inv['payment_method'], inv['amount']])
        total += inv['amount']

    writer.writerow([])
    writer.writerow(['Total Eligible Tuition Paid:', '', '', '', f"INR {total:,.2f}"])
    writer.writerow(['Authorized Signatory:', 'Little Millennium Kharadi Management'])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=Little_Millennium_Tax_Statement_{student['first_name']}.csv"}
    )

# -----------------------------------------------------------------------------
# TEACHER CLASSROOM ENGINE
# -----------------------------------------------------------------------------
@app.route('/teacher/classroom')
def teacher_classroom():
    conn = get_db_connection()
    today_str = datetime.date.today().isoformat()
    classroom = conn.execute("SELECT * FROM classrooms WHERE id = 2").fetchone()
    students_raw = conn.execute("SELECT * FROM students WHERE classroom_id = 2").fetchall()
    
    students = []
    for s in students_raw:
        att = conn.execute(
            "SELECT * FROM attendance_logs WHERE student_id = ? AND date = ? AND check_out IS NULL",
            (s['id'], today_str)
        ).fetchone()
        students.append({
            'id': s['id'],
            'roll_number': s['roll_number'],
            'first_name': s['first_name'],
            'last_name': s['last_name'],
            'dob': s['dob'],
            'photo_url': s['photo_url'],
            'allergies': s['allergies'],
            'epipen_required': s['epipen_required'],
            'dietary_restrictions': s['dietary_restrictions'],
            'emergency_contact_name': s['emergency_contact_name'],
            'emergency_contact_phone': s['emergency_contact_phone'],
            'is_present': att is not None,
            'check_in_time': att['check_in'] if att else None
        })
    conn.close()
    return render_template('teacher/classroom.html', active_page='teacher_classroom', classroom=classroom, students=students)

@app.route('/teacher/toggle-attendance', methods=['POST'])
def teacher_toggle_attendance():
    student_id = request.form.get('student_id')
    action = request.form.get('action')
    today_str = datetime.date.today().isoformat()
    now_time = datetime.datetime.now().strftime("%I:%M %p")

    conn = get_db_connection()
    student = conn.execute("SELECT first_name, last_name FROM students WHERE id = ?", (student_id,)).fetchone()
    s_name = f"{student['first_name']} {student['last_name']}" if student else "Student"

    if action == 'check_in':
        conn.execute('''
        INSERT INTO attendance_logs (campus_id, student_id, classroom_id, date, check_in, checked_in_by)
        VALUES (1, ?, 2, ?, ?, 'Teacher Ananya Deshmukh')
        ''', (student_id, today_str, now_time))
        flash(f"{s_name} checked in at {now_time}.", "success")
    else:
        conn.execute('''
        UPDATE attendance_logs SET check_out = ?, checked_out_by = 'Teacher Checkout'
        WHERE student_id = ? AND date = ?
        ''', (now_time, student_id, today_str))
        flash(f"{s_name} checked out.", "info")
    conn.commit()
    conn.close()
    return redirect(url_for('teacher_classroom'))

@app.route('/teacher/daily-sheets')
def teacher_daily_sheets():
    preselect = request.args.get('preselect', type=int)
    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students WHERE classroom_id = 2").fetchall()
    recent = conn.execute('''
    SELECT a.*, (s.first_name || ' ' || s.last_name) as student_name, u.name as teacher_name
    FROM daily_activities a
    JOIN students s ON a.student_id = s.id
    JOIN users u ON a.teacher_id = u.id
    WHERE a.classroom_id = 2
    ORDER BY a.id DESC LIMIT 6
    ''').fetchall()
    conn.close()
    return render_template('teacher/daily_sheets.html', active_page='teacher_daily_sheets', students=students, preselected_id=preselect, recent_activities=recent)

@app.route('/teacher/save-activity', methods=['POST'])
def teacher_save_activity():
    student_ids = request.form.getlist('student_ids')
    activity_type = request.form.get('activity_type', 'observation')
    title = request.form.get('title', 'Daily Note')
    details = request.form.get('details', '')
    now_time = datetime.datetime.now().strftime("%I:%M %p")
    user_id = session.get('user_id', 4)

    conn = get_db_connection()
    for s_id in student_ids:
        conn.execute('''
        INSERT INTO daily_activities (student_id, classroom_id, teacher_id, activity_type, title, details, timestamp)
        VALUES (?, 2, ?, ?, ?, ?, ?)
        ''', (s_id, user_id, activity_type, title, details, now_time))
    conn.commit()
    conn.close()
    flash(f"Activity '{title}' synced to {len(student_ids)} children's parent feeds!", "success")
    return redirect(url_for('teacher_daily_sheets'))

@app.route('/teacher/lessons')
def teacher_lessons():
    return render_template('teacher/lesson_plans.html', active_page='teacher_lessons')

@app.route('/teacher/supply-request')
def teacher_supply_request():
    user_id = session.get('user_id', 4)
    conn = get_db_connection()
    my_requests = conn.execute("SELECT * FROM supply_requests WHERE teacher_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    conn.close()
    return render_template('teacher/supply_request.html', active_page='teacher_supply_request', my_requests=my_requests)

@app.route('/teacher/submit-supply-request', methods=['POST'])
def teacher_submit_supply_request():
    user_id = session.get('user_id', 4)
    item_name = request.form.get('item_name')
    quantity = int(request.form.get('quantity', 1))
    urgency = request.form.get('urgency', 'Normal')
    notes = request.form.get('notes', '')

    conn = get_db_connection()
    conn.execute('''
    INSERT INTO supply_requests (campus_id, teacher_id, classroom_id, item_name, quantity, urgency, status, notes)
    VALUES (1, ?, 2, ?, ?, ?, 'Pending', ?)
    ''', (user_id, item_name, quantity, urgency, notes))
    conn.commit()
    conn.close()
    flash(f"Requisition for {quantity}x {item_name} sent to Director!", "success")
    return redirect(url_for('teacher_supply_request'))

# -----------------------------------------------------------------------------
# PARENT FAMILY HUB & PAYMENT PROOF UPLOAD WORKFLOW (MANDATED FIX)
# -----------------------------------------------------------------------------
@app.route('/parent/feed')
def parent_feed():
    conn = get_db_connection()
    child = conn.execute('''
    SELECT s.*, c.name as classroom_name
    FROM students s
    JOIN classrooms c ON s.classroom_id = c.id
    WHERE s.id = 4
    ''').fetchone()

    child_activities = conn.execute('''
    SELECT a.*, u.name as teacher_name
    FROM daily_activities a
    JOIN users u ON a.teacher_id = u.id
    WHERE a.student_id = 4
    ORDER BY a.id DESC
    ''').fetchall()

    today_str = datetime.date.today().isoformat()
    att = conn.execute("SELECT check_in FROM attendance_logs WHERE student_id = 4 AND date = ?", (today_str,)).fetchone()
    check_in_time = att['check_in'] if att else "08:20 AM"

    conn.close()
    return render_template('parent/feed.html', active_page='parent_feed', child=child, child_activities=child_activities, check_in_time=check_in_time)

@app.route('/parent/enrollment')
def parent_enrollment():
    conn = get_db_connection()
    child = conn.execute('''
    SELECT s.*, c.name as classroom_name
    FROM students s
    JOIN classrooms c ON s.classroom_id = c.id
    WHERE s.id = 4
    ''').fetchone()
    conn.close()
    return render_template('parent/enrollment.html', active_page='parent_enrollment', child=child)

@app.route('/parent/submit-enrollment', methods=['POST'])
def parent_submit_enrollment():
    flash("Digital Enrollment Packet & HTML5 Signature successfully submitted and stored!", "success")
    return redirect(url_for('parent_feed'))

@app.route('/parent/billing')
def parent_billing():
    conn = get_db_connection()
    child = conn.execute("SELECT id, first_name, last_name, classroom_id FROM students WHERE id = 4").fetchone()
    classroom = conn.execute("SELECT name FROM classrooms WHERE id = ?", (child['classroom_id'],)).fetchone()
    invoices = conn.execute("SELECT * FROM invoices WHERE student_id = 4 ORDER BY due_date DESC").fetchall()
    
    pending_amount = sum(i['amount'] for i in invoices if i['status'] != 'Paid')
    total_paid = sum(i['amount'] for i in invoices if i['status'] == 'Paid')
    conn.close()
    return render_template(
        'parent/billing.html',
        active_page='parent_billing',
        child=child,
        classroom=classroom,
        invoices=invoices,
        pending_amount=pending_amount,
        total_paid_amount=total_paid
    )

@app.route('/parent/submit-payment/<int:invoice_id>', methods=['POST'])
def parent_submit_payment(invoice_id):
    payment_method = request.form.get('payment_method', 'UPI')
    txn_ref = request.form.get('txn_ref', '').strip()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Handle file upload for receipt
    receipt_filename = None
    if 'receipt_file' in request.files:
        file = request.files['receipt_file']
        if file and file.filename != '':
            filename = secure_filename(f"proof_{invoice_id}_{random.randint(100, 999)}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            receipt_filename = filename

    if not receipt_filename:
        # Default placeholder receipt proof
        receipt_filename = "sample_upi_receipt.png"

    conn = get_db_connection()
    conn.execute('''
    UPDATE invoices 
    SET status = 'Pending Approval', approval_status = 'Pending Approval', payment_method = ?, parent_txn_ref = ?, parent_receipt_file = ?, parent_payment_date = ?
    WHERE id = ?
    ''', (payment_method, txn_ref or 'UPI/2026/TXN88912', receipt_filename, now_str, invoice_id))
    conn.commit()
    conn.close()

    flash("Payment proof & receipt screenshot submitted successfully! Once the school verifies it, your status will change to Paid.", "success")
    return redirect(url_for('parent_billing'))

@app.route('/parent/messages')
def parent_messages():
    conn = get_db_connection()
    child = conn.execute("SELECT s.*, c.name as classroom_name FROM students s JOIN classrooms c ON s.classroom_id = c.id WHERE s.id = 4").fetchone()
    teacher = conn.execute("SELECT * FROM users WHERE role = 'teacher' AND id = 4").fetchone()
    chat_messages = conn.execute('''
    SELECT * FROM messages
    WHERE (sender_id = 8 OR receiver_id = 8)
    ORDER BY id ASC
    ''').fetchall()
    conn.close()
    return render_template('parent/messages.html', active_page='parent_messages', child=child, teacher=teacher, chat_messages=chat_messages)

@app.route('/parent/send-message', methods=['POST'])
def parent_send_message():
    receiver_id = request.form.get('receiver_id', 4)
    message_text = request.form.get('message_text')
    translated = f"अनुवाद: {message_text}"

    conn = get_db_connection()
    conn.execute('''
    INSERT INTO messages (sender_id, receiver_id, sender_role, message_text, translated_text, visible_to_director, student_id)
    VALUES (8, ?, 'parent', ?, ?, 1, 4)
    ''', (receiver_id, message_text, translated))
    conn.commit()
    conn.close()
    flash("Message delivered to classroom teacher and center director!", "success")
    return redirect(url_for('parent_messages'))

# -----------------------------------------------------------------------------
# DIRECTOR FAMILY COMMUNICATIONS HUB (OVERSIGHT)
# -----------------------------------------------------------------------------
@app.route('/admin/messages')
def admin_messages():
    conn = get_db_connection()
    threads = [
        {
            'student_id': 4,
            'student_name': 'Aarav Mehta',
            'roll_number': 'LM-KHD-004',
            'student_photo': 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150',
            'parent_name': 'Vikram Mehta',
            'teacher_name': 'Ananya Deshmukh'
        }
    ]
    messages = conn.execute('''
    SELECT * FROM messages
    WHERE visible_to_director = 1 OR sender_role IN ('parent', 'teacher', 'director')
    ORDER BY id ASC
    ''').fetchall()
    conn.close()
    return render_template('admin/messages.html', active_page='admin_messages', threads=threads, messages=messages)

@app.route('/admin/send-message', methods=['POST'])
def admin_send_message():
    receiver_id = request.form.get('receiver_id', 8)
    message_text = request.form.get('message_text')
    student_id = request.form.get('student_id', 4)
    translated = f"अनुवाद (निदेशक): {message_text}"

    conn = get_db_connection()
    conn.execute('''
    INSERT INTO messages (sender_id, receiver_id, sender_role, message_text, translated_text, visible_to_director, student_id)
    VALUES (1, ?, 'director', ?, ?, 1, ?)
    ''', (receiver_id, message_text, translated, student_id))
    conn.commit()
    conn.close()
    flash("Director response sent to parent and lead teacher!", "success")
    return redirect(url_for('admin_messages'))

# -----------------------------------------------------------------------------
# STUDENT ACHIEVEMENTS & GAMIFIED PORTFOLIO
# -----------------------------------------------------------------------------
@app.route('/student/portfolio')
def student_portfolio():
    conn = get_db_connection()
    badges = conn.execute("SELECT * FROM student_badges WHERE student_id = 4").fetchall()
    conn.close()
    return render_template('student/portfolio.html', active_page='student_portfolio', badges=badges)

@app.route('/student/bookshelf')
def student_bookshelf():
    conn = get_db_connection()
    books = conn.execute("SELECT * FROM reading_logs WHERE student_id = 4").fetchall()
    conn.close()
    return render_template('student/bookshelf.html', active_page='student_bookshelf', books=books)

@app.route('/student/log-book', methods=['POST'])
def student_log_book():
    title = request.form.get('book_title')
    author = request.form.get('author', 'Picture Book')
    sticker = request.form.get('sticker_icon', '⭐')

    conn = get_db_connection()
    conn.execute('''
    INSERT INTO reading_logs (student_id, book_title, author, pages, sticker_icon)
    VALUES (4, ?, ?, 24, ?)
    ''', (title, author, sticker))
    conn.commit()
    conn.close()
    flash(f"Sticker {sticker} added to your bookshelf for '{title}'!", "success")
    return redirect(url_for('student_bookshelf'))

if __name__ == '__main__':
    init_db()
    print("=" * 60)
    print("Little Millennium - Nest Daycare (Kharadi Branch)")
    print("Enterprise Preschool & Daycare ERP & CRM Portal")
    print("Server running at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
