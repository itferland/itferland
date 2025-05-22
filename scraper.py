import requests
from bs4 import BeautifulSoup
import sqlite3
import datetime
import hashlib
import os

# Define Database Path
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'leads.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_details_hash(details: str) -> str:
    # Ensure details is a string, even if None is passed, to prevent errors during hashing
    details_str = str(details if details is not None else '').lower().strip()
    return hashlib.md5(details_str.encode('utf-8')).hexdigest()

def scrape_inquiries() -> list:
    url = "https://example.com/moving-inquiries" # Placeholder URL
    headers = {"User-Agent": "Mozilla/5.0"}
    leads = []

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    for item in soup.find_all('div', class_='inquiry'): # Example selector
        title_elem = item.find('h2')
        link_elem = item.find('a')
        description_elem = item.find('p', class_='description') # Hypothetical description

        if title_elem and link_elem:
            title = title_elem.get_text(strip=True)
            lead_url = link_elem.get('href')
            # Ensure lead_url is absolute
            if lead_url and not lead_url.startswith(('http://', 'https://')):
                base_url_parts = url.split('/')
                base_url = f"{base_url_parts[0]}//{base_url_parts[2]}"
                lead_url = base_url + lead_url if lead_url.startswith('/') else base_url + '/' + lead_url


            description = description_elem.get_text(strip=True) if description_elem else "No description available."
            
            details = f"Title: {title} - URL: {lead_url} - Description: {description}"

            lead_data = {
                'name': None,  # Typically not available directly from such listings
                'email': None, # Typically not available directly
                'details': details,
                'source': 'scraper',
                'timestamp': datetime.datetime.now().isoformat()
            }
            leads.append(lead_data)
        else:
            # Optionally log if essential elements are missing for an item
            print(f"Skipping item, missing title or link: {item.prettify()}")

    return leads

def save_leads(leads_to_save: list) -> int:
    conn = get_db_connection()
    saved_count = 0
    processed_count = len(leads_to_save)

    try:
        for lead in leads_to_save:
            details = lead.get('details')
            # Ensure details is not None before hashing, as generate_details_hash expects a string
            if details is None:
                print(f"Skipped lead due to missing details: {lead}") # Log or handle as appropriate
                continue

            details_hash = generate_details_hash(details)

            cursor = conn.cursor()
            cursor.execute("SELECT id FROM leads WHERE unique_hash = ?", (details_hash,))
            existing_lead = cursor.fetchone()
            # It's good practice to close cursors, though for simple operations,
            # Python's garbage collection often handles it when the cursor object goes out of scope.
            # However, explicit closing is safer, especially in loops or complex functions.
            cursor.close() 

            if existing_lead is None:
                try:
                    conn.execute(
                        'INSERT INTO leads (name, email, details, source, timestamp, unique_hash) VALUES (?, ?, ?, ?, ?, ?)',
                        (lead.get('name'), lead.get('email'), details, lead.get('source'), lead.get('timestamp'), details_hash)
                    )
                    conn.commit()
                    saved_count += 1
                    print(f"Saved new lead: {details[:100]}...")
                except sqlite3.Error as e:
                    print(f"Error saving lead {details[:100]}...: {e}")
                    conn.rollback() # Rollback on error for this specific lead
            else:
                print(f"Skipped duplicate lead: {details[:100]}...")
    except Exception as e:
        print(f"An error occurred during the save_leads process: {e}")
    finally:
        if conn:
            conn.close()

    print(f"Total leads processed: {processed_count}, New leads saved: {saved_count}")
    return saved_count

if __name__ == '__main__':
    print("Starting scraper...")
    scraped_leads = scrape_inquiries()

    if scraped_leads:
        print(f"Found {len(scraped_leads)} potential leads.")
        save_leads(scraped_leads)
    else:
        print("No new leads found or error during scraping.")
    
    print("Scraper finished.")
