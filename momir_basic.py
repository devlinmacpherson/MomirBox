import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
from gpiozero import RotaryEncoder, Button
from signal import pause
import time
import sqlite3
import textwrap
import io
import os  # <--- NEW: Allows us to send the shutdown command
from escpos.printer import File

# --- 1. Setup OLED & State ---
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

# TWEAK 1: Flip the display upside down (0 is default, 2 is 180 degrees)
oled.rotation = 2 

cmc_value = 1
MIN_CMC = 0
MAX_CMC = 16

# Flag to prevent printing when we want to shut down
is_shutting_down = False 

# IMPORTANT: Ensure this points to your NEW massive database!
DB_PATH = "momir_library_art.db"

# --- 2. Initialize Printer (Once, at startup) ---
try:
    p = File("/dev/usb/lp0")
except Exception as e:
    print(f"Could not connect to printer: {e}")

# --- 3. Font Setup ---
try:
    text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    giant_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 45)
except:
    text_font = ImageFont.load_default()
    giant_font = ImageFont.load_default()

# --- 4. Database Fetch ---
def get_random_creature(cmc):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, mana_cost, type_line, power, toughness, oracle_text, art_blob 
            FROM creatures WHERE cmc = ? ORDER BY RANDOM() LIMIT 1
        """, (cmc,))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        print(f"Database Error: {e}")
        return None

# --- 5. Revised Print Function ---
def print_receipt(cmc):
    creature = get_random_creature(cmc)
    if not creature:
        return False

    name, mana_cost, type_line, power, toughness, oracle_text, art_blob = creature
    
    # Clean up symbols for the printer
    type_line = type_line.replace('—', '-') if type_line else ""
    if oracle_text:
        oracle_text = oracle_text.replace('—', '-').replace('•', '*').replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")

    try:
        p.hw("init") 
        
        # 1. NAME 
        p.set(align='left', bold=True, width=1, height=1)
        p.text(f"{name}\n")

        # 2. MANA VALUES
        p.set(align='left', bold=False)
        p.text(f"Cost: {mana_cost} (CMC: {cmc})\n\n")

        # 3. ARTWORK 
        if art_blob:
            image_data = io.BytesIO(art_blob)
            card_art = Image.open(image_data)
            p.set(align='center')
            p.image(card_art)
            p.text("\n")

        # 4. TYPE LINE
        p.set(align='left')
        for line in textwrap.wrap(type_line, width=32):
            p.text(f"{line}\n")
        p.text("-" * 32 + "\n")

        # 5. ORACLE TEXT
        if oracle_text:
            for line in textwrap.wrap(oracle_text, width=32):
                p.text(f"{line}\n")
            p.text("-" * 32 + "\n")

        # 6. P/T 
        pt_string = f"{power}/{toughness}"
        p.set(align='right', bold=True)
        p.text(pt_string + "\n\n\n\n\n")
        
        return True

    except Exception as e:
        print(f"Printer error: {e}")
        return False

# --- 6. Interface logic ---
def update_display():
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), "CMC:", font=text_font, fill=255)
    cmc_str = str(cmc_value)
    left, top, right, bottom = draw.textbbox((0, 0), cmc_str, font=giant_font)
    draw.text(((oled.width - (right - left)) // 2, 15), cmc_str, font=giant_font, fill=255)
    oled.image(image)
    oled.show()

def turned_left():
    global cmc_value
    if cmc_value > MIN_CMC:
        cmc_value -= 1
        update_display()

def turned_right():
    global cmc_value
    if cmc_value < MAX_CMC:
        cmc_value += 1
        update_display()

# --- NEW: Safe Shutdown Function ---
def shutdown_pi():
    global is_shutting_down
    is_shutting_down = True
    
    # Show "Shutting Down..." on OLED
    img = Image.new("1", (oled.width, oled.height))
    d = ImageDraw.Draw(img)
    d.text((10, 25), "Shutting Down...", font=text_font, fill=255)
    oled.image(img)
    oled.show()
    
    print("Initiating safe shutdown...")
    time.sleep(2) # Give the user a moment to see the screen
    os.system("sudo poweroff")

# --- REVISED: Print logic triggers on release, unless shutting down ---
def button_released():
    global is_shutting_down
    
    # If the user held the button to shut down, don't print!
    if is_shutting_down:
        return

    # Show "Summoning..."
    img = Image.new("1", (oled.width, oled.height))
    d = ImageDraw.Draw(img)
    d.text((25, 25), "Summoning...", font=text_font, fill=255)
    oled.image(img)
    oled.show()

    if print_receipt(cmc_value):
        time.sleep(0.5)
        update_display()
    else:
        d.rectangle((0,0,128,64), fill=0)
        d.text((20, 25), "Printer Error!", font=text_font, fill=255)
        oled.image(img)
        oled.show()
        time.sleep(2)
        update_display()

# --- 7. Setup & Start ---
rotor = RotaryEncoder(17, 27, wrap=False)

# TWEAK 2: Swapped the assigned functions to reverse the dial direction
rotor.when_rotated_clockwise = turned_left
rotor.when_rotated_counter_clockwise = turned_right

# NEW: Set hold_time to 3 seconds
button = Button(22, pull_up=True, bounce_time=0.1, hold_time=3.0)

# NEW: Assign our release and hold actions
button.when_released = button_released
button.when_held = shutdown_pi

update_display()
print("Momir Master v3.2 (Safe Shutdown Enabled) Ready.")
pause()