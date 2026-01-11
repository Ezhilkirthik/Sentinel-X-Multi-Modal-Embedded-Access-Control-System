import framebuf
from micropython import const
import time

class Matrix8x8(framebuf.FrameBuffer):
    def __init__(self, spi, cs, num_matrices=4):
        self.spi = spi
        self.cs = cs
        self.cs.init(cs.OUT, value=1)
        
        # Dimensions
        self.num_matrices = num_matrices
        self.width = 8 * num_matrices
        self.height = 8
        
        # 1 bit per pixel buffer
        self.buffer = bytearray(self.width * self.height // 8)
        
        # Initialize FrameBuffer with MONO_HLSB format
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_HLSB)
        
        self.init_display()

    def _write_cmd(self, command, data):
        # We must push the command to ALL chained matrices.
        # This fixes the "M2-M4 always on" issue by ensuring 
        # the configuration reaches the later chips.
        self.cs(0)
        for _ in range(self.num_matrices):
            self.spi.write(bytearray([command, data]))
        self.cs(1)

    def init_display(self):
        # Registers
        _NOOP = const(0x0)
        _DIGIT0 = const(0x1)
        _DECODEMODE = const(0x9)
        _INTENSITY = const(0xA)
        _SCANLIMIT = const(0xB)
        _SHUTDOWN = const(0xC)
        _DISPLAYTEST = const(0xF)

        # Sequence to ensure all chips are reset correctly
        for command, data in (
            (_SHUTDOWN, 0),       # 1. Shutdown mode (turn off)
            (_DISPLAYTEST, 0),    # 2. TURN OFF TEST MODE (Fixes "All On" issue)
            (_SCANLIMIT, 7),      # 3. Scan all 8 digits
            (_DECODEMODE, 0),     # 4. No decode (use raw pixels)
            (_INTENSITY, 2),      # 5. Set brightness (Low: 2)
        ):
            self._write_cmd(command, data)
        
        time.sleep(0.1) # Short pause
        self._write_cmd(_SHUTDOWN, 1) # 6. Wake up

    def brightness(self, value):
        # value 0 to 15
        if value < 0: value = 0
        if value > 15: value = 15
        self._write_cmd(0xA, value)

    def show(self):
        # Send buffer to the chips
        for y in range(8):
            self.cs(0)
            for m in range(self.num_matrices):
                # Calculate which byte in the buffer corresponds to:
                # Row 'y' for Matrix 'm'
                # The logic assumes standard horizontal layout
                byte_val = self.buffer[(y * self.num_matrices) + m]
                
                # Send Row Address (y+1) and Data (byte_val)
                self.spi.write(bytearray([y + 1, byte_val]))
            self.cs(1)
