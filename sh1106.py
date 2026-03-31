from micropython import const
import framebuf

# SH1106 commands
_SET_CONTRAST        = const(0x81)
_SET_ENTIRE_ON       = const(0xA4)
_SET_NORM_INV        = const(0xA6)
_SET_DISP            = const(0xAE)
_SET_MEM_ADDR        = const(0x20)
_SET_COL_ADDR        = const(0x21)
_SET_PAGE_ADDR       = const(0x22)
_SET_DISP_START_LINE = const(0x40)
_SET_SEG_REMAP       = const(0xA1)
_SET_MUX_RATIO       = const(0xA8)
_SET_COM_OUT_DIR     = const(0xC8)
_SET_DISP_OFFSET     = const(0xD3)
_SET_COM_PIN_CFG     = const(0xDA)
_SET_DISP_CLK_DIV    = const(0xD5)
_SET_PRECHARGE       = const(0xD9)
_SET_VCOM_DESEL      = const(0xDB)
_SET_CHARGE_PUMP     = const(0x8D)

class SH1106_I2C(framebuf.FrameBuffer):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.external_vcc = external_vcc

        # SH1106 is 132 columns wide internally; we show 128.
        self.pages = self.height // 8
        self.buffer = bytearray(self.width * self.pages)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)

        self._cmd(0x00)  # set lower column address
        self._cmd(0x10)  # set higher column address
        self._cmd(0xB0)  # set page address

        self.init_display()

    def _cmd(self, cmd):
        self.i2c.writeto(self.addr, bytes([0x00, cmd]))

    def init_display(self):
        self._cmd(_SET_DISP | 0x00)               # off
        self._cmd(_SET_DISP_CLK_DIV)
        self._cmd(0x80)
        self._cmd(_SET_MUX_RATIO)
        self._cmd(self.height - 1)
        self._cmd(_SET_DISP_OFFSET)
        self._cmd(0x00)
        self._cmd(_SET_DISP_START_LINE | 0x00)
        self._cmd(_SET_CHARGE_PUMP)
        self._cmd(0x10 if self.external_vcc else 0x14)
        self._cmd(_SET_MEM_ADDR)
        self._cmd(0x00)                           # horizontal addressing (not fully used by SH1106)
        self._cmd(_SET_SEG_REMAP)
        self._cmd(_SET_COM_OUT_DIR)
        self._cmd(_SET_COM_PIN_CFG)
        self._cmd(0x12 if self.height == 64 else 0x02)
        self._cmd(_SET_CONTRAST)
        self._cmd(0x9F)
        self._cmd(_SET_PRECHARGE)
        self._cmd(0x22 if self.external_vcc else 0xF1)
        self._cmd(_SET_VCOM_DESEL)
        self._cmd(0x40)
        self._cmd(_SET_ENTIRE_ON)
        self._cmd(_SET_NORM_INV)
        self._cmd(_SET_DISP | 0x01)               # on
        self.fill(0)
        self.show()

    def show(self):
        # SH1106 uses pages; each page is 8px tall. Need to set page + column each time.
        for page in range(self.pages):
            self._cmd(0xB0 + page)                # page address
            self._cmd(0x02)                       # lower column start address (2 = common offset)
            self._cmd(0x10)                       # higher column start address
            start = self.width * page
            end = start + self.width
            # 0x40 = data stream
            self.i2c.writeto(self.addr, b'\x40' + self.buffer[start:end])
