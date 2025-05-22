import unittest
import json
import sqlite3
import os

# Add the parent directory to sys.path to allow importing app
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, init_db, get_db_connection

class TestAPI(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['DATABASE'] = 'test_leads.db'
        self.client = app.test_client()
        # Ensure a clean database for each test
        if os.path.exists(app.config['DATABASE']):
            os.remove(app.config['DATABASE'])
        init_db()

    def tearDown(self):
        if os.path.exists(app.config['DATABASE']):
            os.remove(app.config['DATABASE'])

    def test_save_lead_success(self):
        payload = {'name': 'Test User', 'email': 'test@example.com', 'details': 'Test details'}
        response = self.client.post('/leads', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {'status': 'Lead saved'})

        # Verify data in the database
        conn = get_db_connection()
        lead = conn.execute("SELECT * FROM leads WHERE email = ?", ('test@example.com',)).fetchone()
        conn.close()
        self.assertIsNotNone(lead)
        self.assertEqual(lead['name'], 'Test User')
        self.assertEqual(lead['details'], 'Test details')
        self.assertEqual(lead['source'], 'form')

    def test_save_lead_missing_fields(self):
        payload = {'name': 'Test User', 'details': 'Test details'} # Missing email
        response = self.client.post('/leads', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Missing required fields: name, email, and details are required.'})

        payload = {'email': 'test@example.com', 'details': 'Test details'} # Missing name
        response = self.client.post('/leads', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Missing required fields: name, email, and details are required.'})

        payload = {'name': 'Test User', 'email': 'test@example.com'} # Missing details
        response = self.client.post('/leads', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Missing required fields: name, email, and details are required.'})

    def test_save_lead_duplicate(self):
        payload = {'name': 'Duplicate User', 'email': 'duplicate@example.com', 'details': 'Duplicate details'}
        # First submission
        response1 = self.client.post('/leads', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response1.json, {'status': 'Lead saved'})

        # Second (duplicate) submission
        response2 = self.client.post('/leads', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response2.status_code, 409)
        self.assertEqual(response2.json, {'status': 'Duplicate lead'})

        # Verify only one entry in the database
        conn = get_db_connection()
        leads = conn.execute("SELECT * FROM leads WHERE email = ?", ('duplicate@example.com',)).fetchall()
        conn.close()
        self.assertEqual(len(leads), 1)

    def test_save_lead_invalid_json(self):
        # Malformed JSON
        response = self.client.post('/leads', data='{"name": "Test", "email": "test@example.com", "details": "Test details"', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Invalid JSON payload'})
        
        # Non-JSON data with correct content type
        response = self.client.post('/leads', data='This is not JSON', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Invalid JSON payload'})

    def test_save_lead_empty_payload(self):
        response = self.client.post('/leads', data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Missing required fields: name, email, and details are required.'})

if __name__ == '__main__':
    unittest.main()
