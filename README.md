# Sentinel-X: Multi-Modal Embedded Access Control System

![Language](https://img.shields.io/badge/Language-MicroPython-blue?style=for-the-badge&logo=python)
![Hardware](https://img.shields.io/badge/Hardware-RP2040%20%7C%20OLED%20%7C%20MAX7219-red?style=for-the-badge)
![Protocol](https://img.shields.io/badge/Protocols-SPI%20%7C%20I2C%20%7C%20UART-green?style=for-the-badge)

## 📖 Overview
**Sentinel-X** is a deterministic embedded security framework designed for the Raspberry Pi Pico (RP2040). It implements a **hybrid authentication architecture** combining tactile temporal pattern recognition (Touch) and wireless credential verification (Bluetooth via UART).

Unlike standard lock systems, this project utilizes a non-blocking state machine to manage inputs while simultaneously driving a dual-display feedback system (OLED status monitor + LED Matrix ticker) to provide real-time user interaction data.

---

## 🚀 Key Features

### 🔐 Dual-Factor Authentication
1.  **Temporal Pattern Recognition (Tactile):**
    * Uses a capacitive touch sensor to detect specific rhythmic input patterns (e.g., *Tap, Tap, Hold*).
    * Algorithm calculates signal duration logic (`<500ms` = Dot, `>500ms` = Dash) to validate against a secret sequence.
2.  **Wireless UART Verification (Remote):**
    * Asynchronous Bluetooth data packet handling via UART.
    * Remote password validation for hands-free access control.

### 👁️ Dual-Channel Visual Feedback
* **OLED HUD (I2C):** Displays system status (LOCKED, VERIFYING, DENIED), logs access attempts, and provides administrative feedback.
* **LED Matrix Ticker (SPI):** Provides high-visibility scrolling notifications and progress bars during pattern entry.

### ⚡ Hardware Control
* **Electromechanical Relay Integration:** Direct control of solenoid locks or magnetic strikes with auto-relocking logic.
* **State Machine Logic:** Prevents race conditions between touch inputs and Bluetooth signals.

---

## 🛠️ Hardware Architecture

### Components
* **Microcontroller:** Raspberry Pi Pico (RP2040)
* **Visual Output:**
    * 0.96" SSD1306 OLED Display
    * 4-in-1 MAX7219 8x8 Dot Matrix Module
* **Input/Comm:**
    * TTP223 Capacitive Touch Sensor
    * HC-05/HC-06 Bluetooth Module
* **Actuation:** 5V Relay Module

### 🔌 Pinout Configuration

| Component | Protocol | Pin (GP) | Function |
| :--- | :--- | :--- | :--- |
| **MAX7219** | SPI0 | **18** | SCK (Clock) |
| | | **19** | MOSI (Data) |
| | | **17** | CS (Chip Select) |
| **SSD1306** | I2C0 | **4** | SDA |
| | | **5** | SCL |
| **Bluetooth** | UART0 | **0** | TX (Connects to RX) |
| | | **1** | RX (Connects to TX) |
| **Touch** | GPIO | **16** | Input (Pull Down) |
| **Relay and Buzzer** | GPIO | **15** | Output (Lock Control)|

---

## 🧩 Software Design

The system runs on a `while True` loop that acts as a **Polled State Machine**:

1.  **Idle State:** System monitors UART buffer and Touch pin state. Displays "LOCKED/CLOSE".
2.  **Input Acquisition:**
    * *Bluetooth:* Interrupt-free polling of the UART buffer.
    * *Touch:* Measures `time.ticks_ms()` between signal rising and falling edges to distinguish short presses from long holds.
3.  **Validation Layer:** Compares buffer/sequence against `MASTER_PASSWORD` or `SECRET_PATTERN`.
4.  **Actuation State:** Triggers relay, updates OLED to "OPEN", and initiates a scrolling matrix message.
5.  **Reset:** Auto-locks after `RELAY_OPEN_TIME` (3 seconds).

### Code Snippet: Temporal Logic
# Distinguishing a 'Tap' from a 'Hold'
```duration = time.ticks_diff(current_time, press_start)
if duration < TOLERANCE_MS:
    input_sequence.append(0) # Short Press
else:
    input_sequence.append(1) # Long Press
```
## ⚙️ Installation & Setup
Flash MicroPython: Ensure your Pico is running the latest MicroPython firmware.

Dependencies: Upload the following libraries to the Pico:

- max7219.py

- ssd1306.py

Configuration: Edit in main.py to set your credentials:

SECRET_PATTERN = [0, 0, 1]   # 0=Short, 1=Long
MASTER_PASSWORD = "1234",

Run: Execute main.py. The system defaults to LOCKED state on boot.

## 🔮 Future Roadmap
MQTT Integration: Add Wi-Fi (Pico W) to log entry attempts to a cloud dashboard.

EEPROM Storage: Store passwords in non-volatile memory so they persist without hardcoding.

Rolling Code Security: Implement OTP (One Time Password) logic for Bluetooth access.

## 👨‍💻 Author 
Ezhilkirthik M 

Embedded Systems Enthusiast
