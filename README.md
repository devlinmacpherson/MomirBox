# MomirBox 

MomirBox is a standalone hardware project that generates and prints random Magic: The Gathering creature tokens based on Converted Mana Cost (CMC), simulating the Momir Basic format.

It uses a Raspberry Pi to host a local SQLite database of Scryfall Oracle data, a rotary encoder to select the CMC, an OLED screen for the interface, and a USB thermal receipt printer to output the card text and dithered artwork.

## Hardware Requirements

* **Raspberry Pi:** Any model with USB and GPIO capabilities (Pi 3, Pi 4, or Zero 2 W).
* **58mm USB Thermal Receipt Printer:** A model with a 5V input voltage is highly recommended to simplify power management.
* **SSD1306 OLED Display:** 128x64 resolution, I2C interface.
* **Rotary Encoder:** Standard encoder with a built-in push-button switch (e.g., KY-040).
* **Power Supply:** A 5V / 6A (or higher) DC power supply, a 1-to-2 DC barrel splitter, and a DC-to-USB adapter. This ensures the Pi and printer are powered simultaneously without brownouts during print jobs.

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