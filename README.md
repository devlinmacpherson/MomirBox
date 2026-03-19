# MomirBox 

MomirBox is a standalone hardware project that generates and prints random Magic: The Gathering creature tokens based on Converted Mana Cost (CMC), simulating the Momir Basic format.

It uses a Raspberry Pi to host a local SQLite database of Scryfall Oracle data, a rotary encoder to select the CMC, an OLED screen for the interface, and a USB thermal receipt printer to output the card text and dithered artwork.

## Hardware Requirements

* **Raspberry Pi:** Any model with USB and GPIO capabilities (Pi 3, Pi 4, or Zero 2 W).
* **58mm USB Thermal Receipt Printer:** A model with a 5V input voltage is highly recommended to simplify power management. I used [this one] (https://a.co/d/01qTDcjr). 
* **SSD1306 OLED Display:** 128x64 resolution, I2C interface.
* **Rotary Encoder:** Standard encoder with a built-in push-button switch (e.g., KY-040).
* **Power Supply:** A 5V / 6A (or higher) DC power supply. I used [this one](https://a.co/d/04z9gR1Y). It came with a barrel jack screw terminal that I wired the thermal printers power and ground to. I striped a micro-usb cable to also power the raspberry pi through the same screw terminals.
* **Mini-USB to USB-A cable:** To connect the Thermal printer to the Raspberry Pi

## Wiring & Pinout

**OLED Display (I2C)**
* VCC -> 3.3V (Pin 1)
* GND -> Ground (Pin 9)
* SDA -> GPIO 2 (Pin 3)
* SCL -> GPIO 3 (Pin 5)

**Rotary Encoder**
* CLK (or A) -> GPIO 17
* DT (or B) -> GPIO 27
* SW (Button) -> GPIO 22
* VCC (+) -> 3.3V
* GND -> Ground

**Thermal Printer**
* Connect via USB to any available port on the Raspberry Pi. The code defaults to `/dev/usb/lp0`.

## Software Setup

### 1. Install Dependencies
Run the following commands to install the required system packages and Python libraries:

```bash
sudo apt update
sudo apt install python3-pip libopenjp2-7 libtiff5 nodejs npm -y
pip3 install adafruit-circuitpython-ssd1306 Pillow gpiozero python-escpos
```

### 2. User Permissions
Add your user to the `lp` and `dialout` groups to grant the Python script permission to communicate with the USB printer:

```bash
sudo usermod -a -G lp pi
sudo usermod -a -G dialout pi
```
Reboot the Raspberry Pi to apply the group changes.

### 3. Building the Database
Due to GitHub file size limits, the `momir_library_art.db` file is not included in this repository. You must generate it locally.

1. Download the "Oracle Cards" JSON file from Scryfall's Bulk Data page. [link](https://scryfall.com/docs/api/bulk-data)
2. Place the JSON file in the same directory as the included `db_builder.py` script.
3. Run the builder script: `python3 db_builder.py`
4. This process downloads and dithers artwork for every creature in the database. It will take a few hours depending on your internet connection. Once complete, ensure the resulting `.db` file is in the same directory as `momir_basic.py`.

### 4. Running on Boot (PM2)
To run the device as a headless appliance, configure PM2 to start the script automatically.

```bash
sudo npm install -g pm2
pm2 start momir_basic.py --interpreter python3 --name "momir"
pm2 startup
```
Copy and execute the output command provided by PM2, then save the process list:
```bash
pm2 save
```

## Usage

1.  **Boot:** Connect power. The Pi will boot and load the script within roughly 30 seconds.
2.  **Select CMC:** Turn the rotary encoder to select a value between 0 and 16.
3.  **Print:** Press and immediately release the rotary encoder button. 
4.  **Shutdown:** Press and hold the rotary encoder button for 3 seconds. The OLED will display a shutdown message. Wait for the Raspberry Pi's activity LED to stop blinking before removing power to avoid SD card corruption.