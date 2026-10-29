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

if __name__ == '__main__':
    unittest.main()
