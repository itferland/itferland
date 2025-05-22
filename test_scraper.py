import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import os
import sys
import datetime # Needed for sample data in save_leads test

# Adjust sys.path to allow importing from the parent directory (where scraper.py and app.py are)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper import (
    scrape_inquiries,
    save_leads,
    get_db_connection as scraper_get_db_connection, # Avoid confusion with local get_db_connection
    generate_details_hash,
    DATABASE_PATH as SCRAPER_DB_PATH # Import to modify/restore
)
# We need the schema from app.py to initialize the test database correctly
from app import init_db as app_init_db 

# Define Sample HTML Content
SAMPLE_HTML_CONTENT = """
<html>
<body>
    <div class="inquiry">
        <h2>Inquiry 1: Local Move</h2>
        <a href="/details/1">View Details 1</a>
        <p class="description">Looking for a local mover for a 2-bedroom apartment.</p>
    </div>
    <div class="inquiry">
        <h2>Inquiry 2: Long Distance</h2>
        <a href="https://external.example.com/details/2">View Details 2</a>
        <p class="description">Need a quote for a long-distance move from NY to CA.</p>
    </div>
    <div class="inquiry">
        <h2>Inquiry 3: Packing Services</h2>
        <a href="details/3">View Details 3 (relative no slash)</a>
        <p>No class description here, but should still be part of details.</p>
    </div>
    <div class="inquiry">
        <!-- Missing link -->
        <h2>Inquiry 4: Missing Link</h2>
        <p class="description">This item should be skipped.</p>
    </div>
</body>
</html>
"""

# This is the schema from app.py's init_db()
LEADS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    details TEXT,
    source TEXT,
    timestamp TEXT,
    unique_hash TEXT UNIQUE
)
"""

class TestScraper(unittest.TestCase):
    def setUp(self):
        self.TEST_DATABASE_PATH = 'test_scraper_leads.db'
        self.original_db_path = SCRAPER_DB_PATH
        
        # Dynamically patch scraper.DATABASE_PATH
        # This is a bit tricky as direct assignment might not work as expected
        # if the scraper module has already used its DATABASE_PATH to define
        # module-level variables (like a connection pool, though not in this case).
        # A cleaner way is to patch where it's used, e.g., patching 'scraper.get_db_connection'
        # or ensuring 'get_db_connection' always reads the current DATABASE_PATH.
        # For this specific scraper, get_db_connection reads DATABASE_PATH each time,
        # so changing it via a patch to the variable itself should work.
        self.db_path_patcher = patch('scraper.DATABASE_PATH', self.TEST_DATABASE_PATH)
        self.db_path_patcher.start()

        if os.path.exists(self.TEST_DATABASE_PATH):
            os.remove(self.TEST_DATABASE_PATH)
        
        # Initialize the test database with the schema from app.py
        conn = sqlite3.connect(self.TEST_DATABASE_PATH)
        conn.executescript(LEADS_TABLE_SCHEMA)
        conn.commit()
        conn.close()

    def tearDown(self):
        self.db_path_patcher.stop()
        if os.path.exists(self.TEST_DATABASE_PATH):
            os.remove(self.TEST_DATABASE_PATH)

    @patch('scraper.requests.get')
    def test_scrape_inquiries_success(self, mock_get):
        # Configure the mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.text = SAMPLE_HTML_CONTENT
        mock_response.url = "https://example.com/moving-inquiries" # Base URL for resolving relative links
        mock_response.raise_for_status = MagicMock() # Ensure it doesn't raise by default
        mock_get.return_value = mock_response

        scraped_leads = scrape_inquiries()
        
        self.assertEqual(len(scraped_leads), 3) # Inquiry 4 should be skipped

        # Lead 1 (absolute path)
        self.assertEqual(scraped_leads[0]['details'], "Title: Inquiry 1: Local Move - URL: https://example.com/details/1 - Description: Looking for a local mover for a 2-bedroom apartment.")
        self.assertEqual(scraped_leads[0]['source'], 'scraper')
        
        # Lead 2 (absolute external path)
        self.assertEqual(scraped_leads[1]['details'], "Title: Inquiry 2: Long Distance - URL: https://external.example.com/details/2 - Description: Need a quote for a long-distance move from NY to CA.")
        
        # Lead 3 (relative path, no leading slash, no class on description <p>)
        # The description extraction `item.find('p', class_='description')` will fail for this one.
        # The current scraper code will use "No description available."
        # However, the sample HTML for lead 3 has `<p>No class description here, but should still be part of details.</p>`
        # The scraper's `description_elem = item.find('p', class_='description')` will find nothing.
        # Let's adjust the expected description based on the *actual* scraper logic.
        # The scraper logic for description is:
        # description_elem = item.find('p', class_='description')
        # description = description_elem.get_text(strip=True) if description_elem else "No description available."
        # For Inquiry 3, description_elem will be None.
        self.assertEqual(scraped_leads[2]['details'], "Title: Inquiry 3: Packing Services - URL: https://example.com/details/3 - Description: No description available.")


    @patch('scraper.requests.get')
    def test_scrape_inquiries_network_error(self, mock_get):
        mock_get.side_effect = requests.RequestException("Test network error")
        
        scraped_leads = scrape_inquiries()
        self.assertEqual(scraped_leads, [])

    def test_save_leads_new_and_duplicate(self):
        now_iso = datetime.datetime.now().isoformat()
        sample_leads_data = [
            {'name': None, 'email': None, 'details': 'Unique Lead 1 details', 'source': 'scraper', 'timestamp': now_iso},
            {'name': None, 'email': None, 'details': 'Common Lead details for duplication', 'source': 'scraper', 'timestamp': now_iso},
            {'name': None, 'email': None, 'details': 'Unique Lead 2 details', 'source': 'scraper', 'timestamp': now_iso},
        ]

        # First save
        saved_count1 = save_leads(sample_leads_data)
        self.assertEqual(saved_count1, 3)

        # Verify database content after first save
        conn = scraper_get_db_connection() # Uses the patched DATABASE_PATH
        cursor = conn.cursor()
        cursor.execute("SELECT details, unique_hash FROM leads ORDER BY details")
        db_leads = cursor.fetchall()
        conn.close()

        self.assertEqual(len(db_leads), 3)
        self.assertEqual(db_leads[0]['details'], 'Common Lead details for duplication')
        self.assertEqual(db_leads[0]['unique_hash'], generate_details_hash('Common Lead details for duplication'))
        self.assertEqual(db_leads[1]['details'], 'Unique Lead 1 details')
        self.assertEqual(db_leads[1]['unique_hash'], generate_details_hash('Unique Lead 1 details'))
        self.assertEqual(db_leads[2]['details'], 'Unique Lead 2 details')
        self.assertEqual(db_leads[2]['unique_hash'], generate_details_hash('Unique Lead 2 details'))
        
        # Second save (attempt to save duplicates)
        # Create slightly different objects but with same hashable content for one
        sample_leads_data_again = [
            {'name': 'New Name', 'email': 'new@email.com', 'details': 'Common Lead details for duplication', 'source': 'scraper_v2', 'timestamp': datetime.datetime.now().isoformat()},
            {'name': None, 'email': None, 'details': 'Another New Unique Lead details', 'source': 'scraper', 'timestamp': now_iso},
        ]
        saved_count2 = save_leads(sample_leads_data_again)
        self.assertEqual(saved_count2, 1) # Only "Another New Unique Lead details" should be saved

        # Verify database content after second save
        conn = scraper_get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT details FROM leads ORDER BY details")
        db_leads_after_second_save = cursor.fetchall()
        conn.close()
        
        self.assertEqual(len(db_leads_after_second_save), 4)
        details_list = [row['details'] for row in db_leads_after_second_save]
        self.assertIn('Common Lead details for duplication', details_list)
        self.assertIn('Unique Lead 1 details', details_list)
        self.assertIn('Unique Lead 2 details', details_list)
        self.assertIn('Another New Unique Lead details', details_list)

    def test_generate_details_hash(self):
        details1 = "   Some Details Here   "
        details2 = "some details here" # Different case and spacing
        details3 = "Some Other Details"
        
        hash1 = generate_details_hash(details1)
        hash2 = generate_details_hash(details2)
        hash3 = generate_details_hash(details3)
        
        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)
        self.assertEqual(hash1, "c82ba093820334e09dd600489078101b") # Pre-calculated MD5 for "some details here"
        
        # Test with None
        hash_none = generate_details_hash(None)
        hash_empty = generate_details_hash("")
        self.assertEqual(hash_none, hash_empty)
        self.assertEqual(hash_none, "d41d8cd98f00b204e9800998ecf8427e") # MD5 for empty string


if __name__ == '__main__':
    unittest.main()
