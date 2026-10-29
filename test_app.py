import unittest
from app import app
from database import get_db_connection

class TestLittleMillenniumERP(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_login_page_renders(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Little Millennium', response.data)
        self.assertIn(b'Instant 1-Click Demo Logins', response.data)
        self.assertIn(b'central-processing-loader', response.data)

    def test_quick_login_director(self):
        response = self.client.post('/quick-login', data={'role': 'director'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Executive Command Center', response.data)
        self.assertIn(b'Live Regulatory Student-to-Teacher Ratios', response.data)

    def test_quick_login_teacher(self):
        response = self.client.post('/quick-login', data={'role': 'teacher'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Classroom Roster', response.data)

    def test_quick_login_parent(self):
        response = self.client.post('/quick-login', data={'role': 'parent'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Family Hub', response.data)
        self.assertIn(b'Live Classroom Moments', response.data)

    def test_quick_login_student(self):
        response = self.client.post('/quick-login', data={'role': 'student'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'My Fun Achievements', response.data)
        self.assertIn(b'Tap Any Badge to Hear Fanfare', response.data)

    def test_admin_subroutes(self):
        self.client.post('/quick-login', data={'role': 'director'}, follow_redirects=True)
        routes = ['/admin/ratios', '/admin/crm', '/admin/billing', '/admin/staff', '/admin/inventory', '/admin/meals']
        for r in routes:
            resp = self.client.get(r)
            self.assertEqual(resp.status_code, 200, f"Route {r} failed with status {resp.status_code}")

    def test_export_endpoints(self):
        self.client.post('/quick-login', data={'role': 'director'}, follow_redirects=True)
        
        # 1. Billing CSV
        resp = self.client.get('/admin/export/billing')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Invoice Number', resp.data)
        self.assertEqual(resp.mimetype, 'text/csv')

        # 2. Leads CSV
        resp = self.client.get('/admin/export/leads')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Child Name', resp.data)
        self.assertEqual(resp.mimetype, 'text/csv')

        # 3. Staff compliance CSV
        resp = self.client.get('/admin/export/staff-compliance')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Staff Name', resp.data)
        self.assertEqual(resp.mimetype, 'text/csv')

    def test_parent_payment_upload_and_school_approval_flow(self):
        # 1. Parent submits payment proof
        self.client.post('/quick-login', data={'role': 'parent'}, follow_redirects=True)
        resp = self.client.post('/parent/submit-payment/3', data={
            'payment_method': 'UPI (GPay)',
            'txn_ref': 'UPI/2026/PUN89410'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        
        # Verify invoice is now 'Pending Approval', NOT 'Paid'
        conn = get_db_connection()
        inv = conn.execute("SELECT * FROM invoices WHERE id = 3").fetchone()
        self.assertEqual(inv['status'], 'Pending Approval')
        self.assertEqual(inv['approval_status'], 'Pending Approval')
        self.assertEqual(inv['parent_txn_ref'], 'UPI/2026/PUN89410')

        # 2. Admin logs in and approves payment
        self.client.post('/quick-login', data={'role': 'director'}, follow_redirects=True)
        resp = self.client.post('/admin/approve-parent-payment/3', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Verify now status is Paid and receipt is generated
        inv = conn.execute("SELECT * FROM invoices WHERE id = 3").fetchone()
        conn.close()
        self.assertEqual(inv['status'], 'Paid')
        self.assertEqual(inv['approval_status'], 'Approved')
        self.assertTrue(inv['receipt_number'].startswith('REC-LM-'))

    def test_adjustable_tuition_fee_amount(self):
        self.client.post('/quick-login', data={'role': 'director'}, follow_redirects=True)
        # Log payment with adjusted amount of 13200
        resp = self.client.post('/admin/log-payment', data={
            'invoice_id': '4',
            'amount': '13200',
            'payment_method': 'Cash'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        conn = get_db_connection()
        inv = conn.execute("SELECT * FROM invoices WHERE id = 4").fetchone()
        conn.close()
        self.assertEqual(inv['amount'], 13200.0)
        self.assertEqual(inv['status'], 'Paid')

    def test_auto_generate_invoices(self):
        self.client.post('/quick-login', data={'role': 'director'}, follow_redirects=True)
        resp = self.client.post('/admin/generate-invoices', data={
            'term_month': 'December 2026',
            'due_date': '2026-12-10'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) FROM invoices WHERE term_month = 'December 2026'").fetchone()[0]
        conn.close()
        self.assertGreater(count, 0)

    def test_triparty_messaging_and_roll_numbers(self):
        # 1. Parent sends message to teacher
        self.client.post('/quick-login', data={'role': 'parent'}, follow_redirects=True)
        resp = self.client.post('/parent/send-message', data={
            'receiver_id': '4',
            'message_text': 'Aarav will arrive 15 minutes late today due to dental checkup.'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # 2. Director checks /admin/messages
        self.client.post('/quick-login', data={'role': 'director'}, follow_redirects=True)
        resp = self.client.get('/admin/messages')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'dental checkup', resp.data)
        self.assertIn(b'LM-KHD-004', resp.data)

        # 3. Director replies
        resp = self.client.post('/admin/send-message', data={
            'receiver_id': '8',
            'message_text': 'Noted, thank you for informing the center!'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # 4. Parent checks /parent/messages and sees director reply
        self.client.post('/quick-login', data={'role': 'parent'}, follow_redirects=True)
        resp = self.client.get('/parent/messages')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Noted, thank you', resp.data)

    def test_fee_management_hub_renders(self):
        self.client.post('/quick-login', data={'role': 'director'}, follow_redirects=True)
        resp = self.client.get('/admin/fees')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Dedicated Fee Management Hub', resp.data)
        self.assertIn(b'Annual Expected Fees', resp.data)
        self.assertIn(b'Collected Fees YTD', resp.data)
        self.assertIn(b'Carried-Forward Arrears', resp.data)
        self.assertIn(b'Advance / Extra Credits', resp.data)
        self.assertIn(b'Auto-Rollover & Carry Forward', resp.data)

    def test_adjust_student_monthly_and_annual_fee(self):
        self.client.post('/quick-login', data={'role': 'director'}, follow_redirects=True)
        resp = self.client.post('/admin/adjust-student-fee', data={
            'student_id': '1',
            'monthly_base_fee': '16500',
            'annual_fee': '198000',
            'notes': 'Sibling discount updated'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        conn = get_db_connection()
        s = conn.execute("SELECT monthly_base_fee, annual_fee FROM students WHERE id = 1").fetchone()
        conn.close()
        self.assertEqual(s['monthly_base_fee'], 16500.0)
        self.assertEqual(s['annual_fee'], 198000.0)

    def test_partial_payment_auto_deduct_and_balance_split(self):
        self.client.post('/quick-login', data={'role': 'director'}, follow_redirects=True)
        
        # 1. Create a test invoice for student 2 with due 18000
        conn = get_db_connection()
        inv_num = "INV-TEST-SPLIT-001"
        conn.execute("DELETE FROM fee_payments WHERE invoice_id IN (SELECT id FROM invoices WHERE invoice_number LIKE ?)", (f"{inv_num}%",))
        conn.execute("DELETE FROM invoices WHERE invoice_number LIKE ?", (f"{inv_num}%",))
        conn.execute('''
        INSERT INTO invoices (campus_id, student_id, parent_id, invoice_number, term_month, amount, base_fee, balance_pending, due_date, status)
        VALUES (1, 2, 7, ?, 'October 2026', 18000.0, 18000.0, 18000.0, '2026-10-10', 'Pending')
        ''', (inv_num,))
        conn.commit()
        test_inv = conn.execute("SELECT id FROM invoices WHERE invoice_number = ?", (inv_num,)).fetchone()
        test_inv_id = test_inv['id']
        conn.close()

        # 2. Record partial payment of 11000
        resp = self.client.post('/admin/record-split-payment', data={
            'invoice_id': str(test_inv_id),
            'student_id': '2',
            'paid_amount': '11000',
            'payment_method': 'UPI'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # 3. Check original invoice: amount=11000, status='Paid', receipt generated
        conn = get_db_connection()
        orig = conn.execute("SELECT * FROM invoices WHERE id = ?", (test_inv_id,)).fetchone()
        self.assertEqual(orig['status'], 'Paid')
        self.assertEqual(orig['amount'], 11000.0)
        self.assertEqual(orig['amount_paid'], 11000.0)
        self.assertEqual(orig['balance_pending'], 0.0)
        self.assertTrue(orig['receipt_number'].startswith('REC-LM-'))

        # 4. Check new pending split balance invoice: amount=7000, status='Pending'
        bal_inv = conn.execute("SELECT * FROM invoices WHERE invoice_number LIKE ? AND student_id = 2", (f"{inv_num}-BAL%",)).fetchone()
        self.assertIsNotNone(bal_inv)
        self.assertEqual(bal_inv['amount'], 7000.0)
        self.assertEqual(bal_inv['balance_pending'], 7000.0)
        self.assertEqual(bal_inv['status'], 'Pending')

        # 5. Check transaction in fee_payments table
        payment_log = conn.execute("SELECT * FROM fee_payments WHERE invoice_id = ?", (test_inv_id,)).fetchone()
        self.assertIsNotNone(payment_log)
        self.assertEqual(payment_log['amount_paid'], 11000.0)
        self.assertEqual(payment_log['balance_remaining'], 7000.0)
        conn.close()

    def test_overpayment_credit_wallet_and_next_month_rollover(self):
        self.client.post('/quick-login', data={'role': 'director'}, follow_redirects=True)

        # 1. Setup a test invoice with due 10000 for student 5
        conn = get_db_connection()
        inv_num = "INV-TEST-OVERPAY-005"
        conn.execute("DELETE FROM invoices WHERE invoice_number = ?", (inv_num,))
        conn.execute("UPDATE students SET credit_balance = 0 WHERE id = 5")
        conn.execute('''
        INSERT INTO invoices (campus_id, student_id, parent_id, invoice_number, term_month, amount, base_fee, balance_pending, due_date, status)
        VALUES (1, 5, 8, ?, 'October 2026', 10000.0, 10000.0, 10000.0, '2026-10-10', 'Pending')
        ''', (inv_num,))
        conn.commit()
        inv = conn.execute("SELECT id FROM invoices WHERE invoice_number = ?", (inv_num,)).fetchone()
        inv_id = inv['id']
        conn.close()

        # 2. Overpay: student pays 13500 (extra 3500)
        resp = self.client.post('/admin/record-split-payment', data={
            'invoice_id': str(inv_id),
            'student_id': '5',
            'paid_amount': '13500',
            'payment_method': 'UPI'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Verify invoice is paid and student credit balance is 3500
        conn = get_db_connection()
        inv_check = conn.execute("SELECT status, balance_pending FROM invoices WHERE id = ?", (inv_id,)).fetchone()
        self.assertEqual(inv_check['status'], 'Paid')
        s_check = conn.execute("SELECT credit_balance, monthly_base_fee FROM students WHERE id = 5").fetchone()
        self.assertEqual(s_check['credit_balance'], 3500.0)
        base_fee = s_check['monthly_base_fee'] or 14500.0
        conn.close()

        # 3. Rollover to November 2026
        resp = self.client.post('/admin/rollover-fees', data={
            'target_month': 'November 2026'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Verify that for student 5, the November 2026 invoice auto-deducted the 3500 credit and carried forward arrears
        conn = get_db_connection()
        nov_inv = conn.execute("SELECT * FROM invoices WHERE student_id = 5 AND term_month = 'November 2026'").fetchone()
        self.assertIsNotNone(nov_inv)
        self.assertEqual(nov_inv['credit_adjusted'], 3500.0)
        expected_net_due = base_fee + float(nov_inv['arrears_carried_forward']) - 3500.0
        self.assertEqual(nov_inv['amount'], expected_net_due)
        
        # Verify previous unpaid invoices were marked 'Carried Forward'
        old_invs = conn.execute("SELECT status FROM invoices WHERE student_id = 5 AND term_month != 'November 2026' AND term_month != 'October 2026'").fetchall()
        for oi in old_invs:
            self.assertEqual(oi['status'], 'Carried Forward')

        # Verify student's credit balance is now 0 (applied in full)
        s_after = conn.execute("SELECT credit_balance FROM students WHERE id = 5").fetchone()
        self.assertEqual(s_after['credit_balance'], 0.0)
        conn.close()

if __name__ == '__main__':
    unittest.main()
