"""
Momir Master - Database Builder Script
Parses Scryfall Oracle bulk data (JSON), downloads creature artwork, 
processes it for 1-bit thermal printing, and compiles a SQLite database.
"""

import json
import sqlite3
import os
import time
import requests
import io
from PIL import Image

# --- Configuration ---
SCRYFALL_FILE = 'scryfall.json'
DATABASE_FILE = 'momir_library_art.db'

# Standard pixel width for 58mm thermal printers
PRINTER_WIDTH = 384 

# SAFETY SWITCH: Set to True to process only 20 cards for rapid testing.
# Set to False to process the entire library (~17,800 creatures, takes 1-2 hours).
TEST_MODE = True  

def build_database():
    """Reads Scryfall JSON, processes creature data/art, and builds the SQLite DB."""
    if not os.path.exists(SCRYFALL_FILE):
        print(f"Error: Could not find '{SCRYFALL_FILE}'.")
        return

    # --- Database Initialization ---
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS creatures")
    cursor.execute("""
        CREATE TABLE creatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            cmc INTEGER,
            mana_cost TEXT,
            type_line TEXT,
            power TEXT,
            toughness TEXT,
            oracle_text TEXT,
            art_blob BLOB
        )
    """)

    print(f"Loading '{SCRYFALL_FILE}' into memory...")
    with open(SCRYFALL_FILE, 'r', encoding='utf-8') as f:
        cards = json.load(f)

    creature_count = 0
    error_count = 0
    
    print("Beginning download and image processing...")
    if TEST_MODE:
        print("TEST MODE ENABLED: Only processing 20 cards.")

    # --- Data Extraction & Image Processing Loop ---
    for card in cards:
        if TEST_MODE and creature_count >= 20:
            break

        type_line = card.get('type_line', '')
        
        # Filter strictly for creatures
        if 'Creature' in type_line:
            name = card.get('name', 'Unknown')
            cmc = int(card.get('cmc', 0))
            art_url = None
            
            # Handle Double-Faced Cards (DFCs) by targeting the front face
            if 'card_faces' in card and 'power' not in card:
                front = card['card_faces'][0]
                power = front.get('power', '?')
                toughness = front.get('toughness', '?')
                oracle_text = front.get('oracle_text', '')
                mana_cost = front.get('mana_cost', '')
                if 'image_uris' in front:
                    art_url = front['image_uris'].get('art_crop')
            else:
                # Standard single-faced cards
                power = card.get('power', '?')
                toughness = card.get('toughness', '?')
                oracle_text = card.get('oracle_text', '')
                mana_cost = card.get('mana_cost', '')
                if 'image_uris' in card:
                    art_url = card['image_uris'].get('art_crop')

            art_blob = None
            
            # --- Image Download and Formatting ---
            if art_url:
                try:
                    response = requests.get(art_url, timeout=10)
                    response.raise_for_status()
                    
                    img = Image.open(io.BytesIO(response.content))
                    
                    # Calculate proportional height to maintain aspect ratio
                    w_percent = (PRINTER_WIDTH / float(img.size[0]))
                    h_size = int((float(img.size[1]) * float(w_percent)))
                    
                    # Resize image using high-quality downsampling
                    img = img.resize((PRINTER_WIDTH, h_size), Image.Resampling.LANCZOS)
                    
                    # Convert to 1-bit black and white. PIL inherently applies 
                    # Floyd-Steinberg dithering here, which is ideal for thermal printers.
                    img = img.convert('1') 
                    
                    # Save the dithered image array as PNG bytes for SQLite storage
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    art_blob = img_byte_arr.getvalue()
                    
                except Exception as e:
                    print(f"Failed to process art for {name}: {e}")
                    error_count += 1
                
                # Scryfall API compliance: Ensure a minimum 100ms delay between requests
                time.sleep(0.1)

            # Insert the formatted data and image blob into the database
            cursor.execute("""
                INSERT INTO creatures (name, cmc, mana_cost, type_line, power, toughness, oracle_text, art_blob)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, cmc, mana_cost, type_line, power, toughness, oracle_text, art_blob))
            
            creature_count += 1
            if creature_count % 50 == 0:
                print(f"Processed {creature_count} creatures...")

    # Save and close database connection
    conn.commit()
    conn.close()

    print("\n=== SUCCESS ===")
    print(f"Saved {creature_count} creatures to '{DATABASE_FILE}'.")
    if error_count > 0:
        print(f"Failed to download art for {error_count} cards.")

if __name__ == "__main__":
    build_database()