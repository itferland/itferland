import sqlite3
import hashlib
import logging
from datetime import datetime
from flask import Flask, request, jsonify

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['DATABASE'] = 'leads.db'

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            details TEXT,
            source TEXT,
            timestamp TEXT,
            unique_hash TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

def generate_lead_hash(email, details):
    combined_string = f"{email.lower().strip()}{details.lower().strip()}"
    return hashlib.md5(combined_string.encode('utf-8')).hexdigest()

@app.route('/leads', methods=['POST'])
def save_lead():
    try:
        data = request.get_json()
        if not data:
            logging.warning("Received empty or invalid JSON payload.")
            return jsonify({'error': 'Invalid JSON payload'}), 400

        name = data.get('name')
        email = data.get('email')
        details = data.get('details')

        if not all([name, email, details]):
            logging.warning(f"Missing required fields. Received: name='{name}', email='{email}', details='{details}'")
            return jsonify({'error': 'Missing required fields: name, email, and details are required.'}), 400

        source = "form"
        timestamp = datetime.now().isoformat()
        lead_hash = generate_lead_hash(email, details)

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM leads WHERE unique_hash = ?", (lead_hash,))
            existing_lead = cursor.fetchone()

            if existing_lead:
                logging.info(f"Duplicate lead detected: {email} (Hash: {lead_hash})")
                return jsonify({'status': 'Duplicate lead'}), 409
            else:
                conn.execute(
                    "INSERT INTO leads (name, email, details, source, timestamp, unique_hash) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, email, details, source, timestamp, lead_hash)
                )
                conn.commit()
                logging.info(f"Lead saved: {email} (Hash: {lead_hash})")
                return jsonify({'status': 'Lead saved'}), 201
        except sqlite3.Error as db_err:
            if conn:
                conn.rollback()
            logging.error(f"Database error while processing lead for {email}: {db_err}")
            return jsonify({'error': 'Database operation failed'}), 500
        finally:
            if conn:
                conn.close()
    except Exception as e:
        # Attempt to get email for logging, if possible
        email_for_log = request.get_json().get('email', 'N/A') if request.is_json else 'N/A'
        logging.error(f"Unexpected error in save_lead for email '{email_for_log}': {e}", exc_info=True)
        return jsonify({'error': 'An internal server error occurred'}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
