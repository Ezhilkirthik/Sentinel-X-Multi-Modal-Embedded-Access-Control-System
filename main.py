from machine import Pin, SPI, UART, I2C
import time
import max7219
from ssd1306 import SSD1306_I2C

# --- CONFIGURATION ---
SECRET_PATTERN = [0, 0, 1]   # Touch: Tap, Tap, Hold
MASTER_PASSWORD = "1234"     # THE PASSWORD
TOLERANCE_MS = 500
RELAY_OPEN_TIME = 3
NUM_MATRICES = 4

# --- HARDWARE SETUP ---
# 1. LED Matrix (SPI)
spi = SPI(0, baudrate=10000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(19))
cs = Pin(17, Pin.OUT)
matrix = max7219.Matrix8x8(spi, cs, num_matrices=NUM_MATRICES)

# 2. OLED Display (I2C)
i2c = I2C(0, sda=Pin(4), scl=Pin(5))
oled = SSD1306_I2C(128, 64, i2c)

# 3. Inputs/Outputs
touch = Pin(16, Pin.IN, Pin.PULL_DOWN)
relay = Pin(15, Pin.OUT)
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

def update_oled(state, extra_info=""):
    oled.fill(0)
    # Header
    oled.text("Ezhilkirthik", 15, 0)
    oled.text("Lock System", 20, 10)
    oled.hline(0, 20, 128, 1) # Draw a line
    
    if state == "LOCKED":
        oled.text("STATUS: LOCKED", 10, 30)
        oled.text("Door is Locked", 10, 45)
        
    elif state == "UNLOCKED":
        oled.text("STATUS: OPEN", 10, 30)
        oled.text("Door Unlocked", 10, 45)
        
    elif state == "DENIED":
        oled.text("ACCESS DENIED!", 10, 30)
        oled.text(extra_info, 10, 45)
        
    elif state == "CHECKING":
        oled.text("Verifying...", 10, 30)
        oled.text(extra_info, 10, 45)

    oled.show()

def show_static_matrix(msg):
    matrix.fill(0)
    spacing = 7 
    total_text_width = (len(msg) * spacing) + 1
    display_width = NUM_MATRICES * 8
    start_x = (display_width - total_text_width) // 2
    for i, char in enumerate(msg):
        x = start_x + (i * spacing)
        matrix.text(char, x, 0, 1)
    matrix.show()

def scroll_matrix(msg, speed=0.03):
    total_width = NUM_MATRICES * 8
    msg_width = len(msg) * 8
    for i in range(total_width, -msg_width, -1):
        matrix.fill(0)
        matrix.text(msg, i, 0, 1)
        matrix.show()
        time.sleep(speed)

def show_progress(count):
    for i in range(count):
        matrix.pixel(i, 7, 1)
    matrix.show()

def trigger_unlock(method):
    print(f"SUCCESS: Unlocked via {method}")
    
    # 1. Update OLED & Matrix
    update_oled("UNLOCKED")
    relay.value(1) # Open
    scroll_matrix("WELCOME :)")
    
    # 2. Wait
    time.sleep(RELAY_OPEN_TIME) 
    
    # 3. Re-Lock
    relay.value(0) # Close
    update_oled("LOCKED")
    scroll_matrix("LOCKED")
    show_static_matrix("CLOSE")

# --- MAIN LOGIC ---
print("System Ready.")
relay.value(0)
matrix.brightness(5)
update_oled("LOCKED")
show_static_matrix("CLOSE")

input_sequence = []
last_release_time = time.ticks_ms()
is_pressing = False
press_start = 0

while True:
    current_time = time.ticks_ms()
  
    # 1. BLUETOOTH CHECK 
    if uart.any():
        try:
            data = uart.read()
            # Just get the text message (Password)
            password = data.decode('utf-8').strip()
            
            print(f"Bluetooth Received: {password}")
            
            # Show "Verifying" on OLED
            update_oled("CHECKING", "Remote Access")
            
            if password == MASTER_PASSWORD:
                trigger_unlock("Bluetooth")
            else:
                update_oled("DENIED", "Wrong Password")
                scroll_matrix("DENIED")
                time.sleep(2)
                update_oled("LOCKED")
                show_static_matrix("CLOSE")
        except:
            pass

    # 2. TOUCH PATTERN CHECK
    if touch.value() == 1 and not is_pressing:
        is_pressing = True
        press_start = current_time
        matrix.pixel(0, 0, 1)
        matrix.show()
        
    elif touch.value() == 0 and is_pressing:
        is_pressing = False
        duration = time.ticks_diff(current_time, press_start)
        last_release_time = current_time
        
        if duration < TOLERANCE_MS: input_sequence.append(0)
        else: input_sequence.append(1)
            
        show_static_matrix("CLOSE")
        show_progress(len(input_sequence))

    # Pattern Timeout Logic
    if len(input_sequence) > 0 and \
       time.ticks_diff(current_time, last_release_time) > 2000 and \
       not is_pressing:
        
        # Show "Verifying" on OLED
        update_oled("CHECKING", "Checking Pattern")
        
        if input_sequence == SECRET_PATTERN:
            trigger_unlock("Touch")
        else:
            update_oled("DENIED", "Wrong Pattern")
            scroll_matrix("WRONG")
            time.sleep(1)
            update_oled("LOCKED")
            show_static_matrix("CLOSE")
        input_sequence = []

    time.sleep(0.02)
