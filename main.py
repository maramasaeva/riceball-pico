from machine import Pin, I2C
from sh1106 import SH1106_I2C
from riceball_frames import FRAMES
from new_frames import FRAMES as NEW_FRAMES
from greetings import MORNING, AFTERNOON, EVENING
from quotes import QUOTES

import time
import random
import gc
import ujson

# Pico W Wi-Fi + NTP
import network
import ntptime

# ----------------------------
# USER SETTINGS
# ----------------------------
# WiFi credentials
# Note: Pico W only supports 2.4GHz networks (not 5GHz)
# Make sure your WiFi network is 2.4GHz compatible
WIFI_NETWORKS = [
    ("telenet-689152F", "hQ8mswjp7kaS"),
    ("marrgiela", "K3t3lb!nK!3"),
]

# Belgium: CET is +1, CEST is +2. This is a simple fixed offset.
# If you want DST-aware later, we can add it.
TZ_OFFSET_HOURS = 1

# Animation smoothness
FRAME_DELAY = 0.08     # matches your smooth loop
CONNECT_POLL_SLEEP = 0.0  # we already sleep per frame; keep extra sleep at 0

# TEST MODE: Set to a date string (MM-DD format) to test that date's quote
# Set to None to use actual current date
TEST_DATE = None  # Example: "12-27" to test December 27th

# ----------------------------
# OLED SETUP
# ----------------------------
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400_000)
oled = SH1106_I2C(128, 64, i2c)

# ----------------------------
# KAOMOJI BITMAP FONTS
# ----------------------------
# 8x8 pixel bitmaps for kaomoji characters
# Each glyph is 8 bytes (one byte per row, MSB first)
# Format: each byte represents a row, bits go left to right
# To add more kaomoji: add entries here with 8 bytes representing the 8x8 bitmap
# Use online tools or design your own 8x8 pixel pattern
KAOMOJI_GLYPHS = {
    # Face parts
    'ᴗ': [0x00, 0x00, 0x00, 0x1C, 0x22, 0x22, 0x1C, 0x00],  # Smiling mouth (upward curve)
    'ˬ': [0x00, 0x00, 0x00, 0x00, 0x3E, 0x00, 0x00, 0x00],  # Small mouth (horizontal line)
    '͈': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x00],  # Combining mark (small dot below)
    'ᗜ': [0x00, 0x00, 0x3C, 0x42, 0x42, 0x42, 0x3C, 0x00],  # Face/eye (circle)
    'ᗢ': [0x00, 0x00, 0x1C, 0x22, 0x22, 0x1C, 0x00, 0x00],  # Small face
    
    # Stars and decorative
    '⋆': [0x00, 0x08, 0x14, 0x22, 0x41, 0x22, 0x14, 0x08],  # Star (pointed)
    '☆': [0x00, 0x08, 0x14, 0x22, 0x41, 0x22, 0x14, 0x08],  # White star
    '★': [0x08, 0x1C, 0x3E, 0x7F, 0x3E, 0x1C, 0x08, 0x00],  # Black/filled star
    '⊹': [0x00, 0x08, 0x14, 0x22, 0x14, 0x08, 0x00, 0x00],  # Small star variant
    'ꕤ': [0x00, 0x08, 0x1C, 0x2A, 0x41, 0x2A, 0x1C, 0x08],  # Decorative star
    
    # Hearts
    '♡': [0x00, 0x0C, 0x12, 0x21, 0x21, 0x12, 0x0C, 0x00],  # Heart outline
    '❤': [0x0C, 0x1E, 0x3F, 0x7F, 0x3F, 0x1E, 0x0C, 0x00],  # Filled heart (if needed)
    '𐙚': [0x00, 0x0C, 0x12, 0x21, 0x21, 0x12, 0x0C, 0x00],  # Heart variant
    
    # Dots and punctuation
    '·': [0x00, 0x00, 0x00, 0x18, 0x18, 0x00, 0x00, 0x00],  # Middle dot (bold)
    '˖': [0x00, 0x00, 0x00, 0x18, 0x18, 0x00, 0x00, 0x00],  # Plus dot (same as middle dot)
    '˚': [0x00, 0x0C, 0x12, 0x0C, 0x00, 0x00, 0x00, 0x00],  # Degree ring (top)
    '̊': [0x00, 0x0C, 0x12, 0x0C, 0x00, 0x00, 0x00, 0x00],   # Ring above (same)
    'ﾟ': [0x00, 0x00, 0x0C, 0x12, 0x0C, 0x00, 0x00, 0x00],  # Half-width circle
    '.': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C],  # Period (bottom)
    
    # Math/symbols
    '₊': [0x00, 0x00, 0x08, 0x08, 0x3E, 0x08, 0x08, 0x00],  # Subscript plus
    '⏱': [0x00, 0x1E, 0x21, 0x41, 0x41, 0x21, 0x1E, 0x00],  # Timer/hourglass
    'ᐟ': [0x00, 0x00, 0x00, 0x04, 0x08, 0x10, 0x20, 0x00],  # Slash variant
    
    # Accents and marks
    'ˆ': [0x00, 0x00, 0x18, 0x24, 0x42, 0x00, 0x00, 0x00],  # Circumflex (top)
    '˵': [0x00, 0x00, 0x42, 0x24, 0x18, 0x00, 0x00, 0x00],  # Curved accent (bottom arc)
    '˶': [0x00, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x00],  # Tilde/wavy (full)
    
    # Brackets
    '⸜': [0x00, 0x00, 0x20, 0x10, 0x08, 0x10, 0x20, 0x00],  # Left bracket variant
    '⸝': [0x00, 0x00, 0x04, 0x08, 0x10, 0x08, 0x04, 0x00],  # Right bracket variant
    '˂': [0x00, 0x00, 0x10, 0x08, 0x04, 0x08, 0x10, 0x00],  # Less than variant
    '˃': [0x00, 0x00, 0x04, 0x08, 0x10, 0x08, 0x04, 0x00],  # Greater than variant
    
    # Other
    'ᵕ': [0x00, 0x00, 0x00, 0x00, 0x3E, 0x00, 0x00, 0x00],  # Small dash (horizontal)
}

def draw_kaomoji_glyph(char, x, y):
    """Draw a single kaomoji glyph at position x, y (top-left)."""
    if char not in KAOMOJI_GLYPHS:
        return False  # Glyph not found
    
    glyph = KAOMOJI_GLYPHS[char]
    for row in range(8):
        byte_val = glyph[row]
        for col in range(8):
            if byte_val & (0x80 >> col):
                oled.pixel(x + col, y + row, 1)
    return True

def get_char_width(char):
    """Get width of a character (8 for normal ASCII, 8 for kaomoji glyphs)."""
    if char in KAOMOJI_GLYPHS:
        return 8
    # Check if it's ASCII printable
    if 32 <= ord(char) <= 126:
        return 8
    # Unknown character - use 8 as default
    return 8

def render_text_with_kaomoji(text, x, y, max_width=128):
    """
    Render text that can include both ASCII and kaomoji characters.
    Returns the x position after the text.
    Unknown characters are skipped (no block shown).
    """
    current_x = x
    for char in text:
        if char in KAOMOJI_GLYPHS:
            # Draw kaomoji glyph
            if draw_kaomoji_glyph(char, current_x, y):
                current_x += 8
        elif 32 <= ord(char) <= 126:
            # Normal ASCII character
            oled.text(char, current_x, y)
            current_x += 8
        # Skip unsupported characters (don't advance x, don't show block)
        
        # Check if we've exceeded max width
        if current_x >= max_width:
            break
    
    return current_x

# ----------------------------
# DRAWING
# ----------------------------
def draw_frame(frame):
    # Fast pixel drawing from packed bits (your working approach)
    oled.fill(0)
    i = 0
    for y in range(64):
        for x in range(0, 128, 8):
            b = frame[i]
            # unrolled bit check loop (still readable, keeps it quick)
            if b & 0x01: oled.pixel(x + 0, y, 1)
            if b & 0x02: oled.pixel(x + 1, y, 1)
            if b & 0x04: oled.pixel(x + 2, y, 1)
            if b & 0x08: oled.pixel(x + 3, y, 1)
            if b & 0x10: oled.pixel(x + 4, y, 1)
            if b & 0x20: oled.pixel(x + 5, y, 1)
            if b & 0x40: oled.pixel(x + 6, y, 1)
            if b & 0x80: oled.pixel(x + 7, y, 1)
            i += 1
    oled.show()

def clear():
    oled.fill(0)
    oled.show()

# 16 chars wide (128px / 8px font), 8 lines tall (64px / 8px)
def sanitize_text(text):
    """
    Keep text as-is - we now support kaomoji rendering.
    Only replace line breaks with spaces.
    """
    result = ""
    for ch in text:
        # Replace line breaks with spaces
        if ch in ['\n', '\r', '\t']:
            result += ' '
        else:
            # Keep all characters - we'll render kaomoji if available
            result += ch
    return result

def blink_cursor(text, x=0, y=0, duration_s=1.0, blink_rate=0.5):
    """
    Show text with blinking cursor after it, supporting kaomoji.
    duration_s: how long to blink (use None for infinite)
    """
    deadline = None
    if duration_s is not None:
        deadline = time.ticks_add(time.ticks_ms(), int(duration_s * 1000))
    
    cursor_on = True
    last_blink = time.ticks_ms()
    
    # Calculate text width (accounting for kaomoji)
    text_width = 0
    for ch in text:
        text_width += get_char_width(ch)
    
    while True:
        now = time.ticks_ms()
        if duration_s is not None:
            if time.ticks_diff(deadline, now) <= 0:
                break
        
        # Toggle cursor every blink_rate seconds
        if time.ticks_diff(now, last_blink) >= int(blink_rate * 1000):
            cursor_on = not cursor_on
            last_blink = now
        
        # Draw text + cursor
        oled.fill(0)
        render_text_with_kaomoji(text, x, y, max_width=128)
        if cursor_on:
            # Draw cursor (underscore at end of text)
            cursor_x = x + text_width
            if cursor_x < 128:
                oled.text("_", cursor_x, y)
        oled.show()
        time.sleep(0.1)

def blink_cursor_two_lines(line1, line2, duration_s=1.0, blink_rate=0.5, last_line_y=10):
    """
    Show two lines of text with blinking cursor after the last line, supporting kaomoji.
    last_line_y: Y position of the last line (default 10 for line 2, but can be 8, 16, 24 for multi-line)
    """
    deadline = None
    if duration_s is not None:
        deadline = time.ticks_add(time.ticks_ms(), int(duration_s * 1000))
    
    cursor_on = True
    last_blink = time.ticks_ms()
    
    # Calculate last line width (accounting for kaomoji)
    last_line_width = 0
    for ch in line2:
        last_line_width += get_char_width(ch)
    
    while True:
        now = time.ticks_ms()
        if duration_s is not None:
            if time.ticks_diff(deadline, now) <= 0:
                break
        
        # Toggle cursor every blink_rate seconds
        if time.ticks_diff(now, last_blink) >= int(blink_rate * 1000):
            cursor_on = not cursor_on
            last_blink = now
        
        # Draw lines + cursor
        oled.fill(0)
        render_text_with_kaomoji(line1, 0, 0, max_width=128)
        render_text_with_kaomoji(line2, 0, last_line_y, max_width=128)
        if cursor_on:
            cursor_x = last_line_width
            if cursor_x < 128:
                oled.text("_", cursor_x, last_line_y)
        oled.show()
        time.sleep(0.1)

def scroll_quote_with_cursor(lines_list, duration_s=None, blink_rate=0.5, scroll_delay_s=2.0):
    """
    Show multiple lines of text with scrolling for long quotes.
    Shows 6 lines at a time, scrolling down to reveal more lines.
    After showing all lines, displays blinking cursor on last line.
    
    lines_list: List of lines to display (can be more than 6)
    duration_s: How long to display (None for infinite after scrolling)
    blink_rate: Cursor blink rate in seconds
    scroll_delay_s: How long to show each 6-line segment before scrolling
    """
    if not lines_list:
        return
    
    max_lines_visible = 6  # OLED can show 6 lines (0, 10, 20, 30, 40, 50)
    total_lines = len(lines_list)
    
    # If quote fits on screen (6 lines or less), just show it with cursor (no scrolling)
    if total_lines <= max_lines_visible:
        blink_cursor_multi_line(lines_list, duration_s=duration_s, blink_rate=blink_rate)
        return
    
    # Quote is longer than 6 lines - implement scrolling
    # Calculate how many scroll segments we need
    num_segments = ((total_lines - 1) // max_lines_visible) + 1
    
    # Show each segment for scroll_delay_s seconds
    for segment in range(num_segments):
        start_idx = segment * max_lines_visible
        end_idx = min(start_idx + max_lines_visible, total_lines)
        visible_lines = lines_list[start_idx:end_idx]
        
        # Show this segment for scroll_delay_s seconds
        segment_start = time.ticks_ms()
        segment_duration = int(scroll_delay_s * 1000)
        
        while time.ticks_diff(time.ticks_ms(), segment_start) < segment_duration:
            # Draw visible lines
            oled.fill(0)
            for i, line in enumerate(visible_lines):
                y_pos = i * 10
                render_text_with_kaomoji(line, 0, y_pos, max_width=128)
            oled.show()
            time.sleep(0.1)
    
    # After scrolling through all segments, show final segment (last 6 lines) with blinking cursor
    final_start = max(0, total_lines - max_lines_visible)
    final_lines = lines_list[final_start:]
    blink_cursor_multi_line(final_lines, duration_s=duration_s, blink_rate=blink_rate)

def blink_cursor_multi_line(lines_list, duration_s=None, blink_rate=0.5):
    """
    Show multiple lines of text with blinking cursor after the last line, supporting kaomoji.
    lines_list: List of lines to display (assumed to fit on screen, <= 6 lines)
    duration_s: How long to blink (None for infinite)
    """
    if not lines_list:
        return
    
    deadline = None
    if duration_s is not None:
        deadline = time.ticks_add(time.ticks_ms(), int(duration_s * 1000))
    
    cursor_on = True
    last_blink = time.ticks_ms()
    
    # Calculate last line width (accounting for kaomoji)
    last_line = lines_list[-1]
    last_line_width = 0
    for ch in last_line:
        last_line_width += get_char_width(ch)
    
    # Calculate y position of last line
    last_line_y = (len(lines_list) - 1) * 10
    
    while True:
        now = time.ticks_ms()
        if duration_s is not None:
            if time.ticks_diff(deadline, now) <= 0:
                break
        
        # Toggle cursor every blink_rate seconds
        if time.ticks_diff(now, last_blink) >= int(blink_rate * 1000):
            cursor_on = not cursor_on
            last_blink = now
        
        # Draw all lines + cursor
        oled.fill(0)
        for i, line in enumerate(lines_list):
            y_pos = i * 10
            render_text_with_kaomoji(line, 0, y_pos, max_width=128)
        
        if cursor_on:
            cursor_x = last_line_width
            if cursor_x < 128:
                oled.text("_", cursor_x, last_line_y)
        oled.show()
        time.sleep(0.1)

def type_text(text, x=0, y=0, char_delay=0.03, clear_first=True):
    """
    Typewriter that writes left-to-right, supporting both ASCII and kaomoji.
    Automatically wraps to next line if text is too long.
    Returns: (typed_text, wrapped_lines) where wrapped_lines is None if single line, or list of lines if wrapped.
    """
    # Sanitize text first (only replace line breaks)
    text = sanitize_text(text)
    
    # Check if text needs wrapping
    lines = wrap_text_to_lines(text, max_chars_per_line=16, max_lines=6)
    
    if len(lines) == 1:
        # Single line - use original logic
        if clear_first:
            oled.fill(0)
        buf = ""
        for ch in text:
            buf += ch
            oled.fill(0)
            render_text_with_kaomoji(buf, x, y, max_width=128)
            oled.show()
            time.sleep(char_delay)
        return buf, None  # Return typed text and None for lines (single line)
    else:
        # Multiple lines - use type_multi_line
        first_line, last_line = type_multi_line(lines, char_delay=char_delay)
        return first_line if first_line else last_line, lines

def type_two_lines(line1, line2, char_delay=0.02):
    """
    Types line1 on row 0 and line2 on row 1, supporting kaomoji.
    Keeps both visible while typing.
    """
    # Sanitize text first (only replace line breaks)
    line1 = sanitize_text(line1)
    line2 = sanitize_text(line2)
    
    l1 = ""
    l2 = ""
    # type line1
    for ch in line1:
        l1 += ch
        oled.fill(0)
        render_text_with_kaomoji(l1, 0, 0, max_width=128)
        render_text_with_kaomoji(l2, 0, 10, max_width=128)
        oled.show()
        time.sleep(char_delay)
    # type line2
    for ch in line2:
        l2 += ch
        oled.fill(0)
        render_text_with_kaomoji(l1, 0, 0, max_width=128)
        render_text_with_kaomoji(l2, 0, 10, max_width=128)
        oled.show()
        time.sleep(char_delay)
    return l1, l2  # Return typed lines for cursor blinking

def wrap_text_to_lines(text, max_chars_per_line=16, max_lines=None):
    """
    Wrap text into lines at word boundaries.
    Returns list of lines.
    If max_lines is None, wraps to unlimited lines.
    If max_lines is set, truncates at that many lines.
    """
    words = text.split()
    if not words:
        return [""]
    
    lines = []
    current_line = ""
    
    for i, word in enumerate(words):
        # Build test line
        if current_line:
            test_line = current_line + " " + word
        else:
            test_line = word
        
        if len(test_line) <= max_chars_per_line:
            # Word fits on current line
            current_line = test_line
        else:
            # Word doesn't fit - save current line and start new one
            if current_line:
                lines.append(current_line)
                if max_lines is not None and len(lines) >= max_lines:
                    # We've reached max lines - append remaining words to last line
                    remaining = " ".join(words[i:])
                    if len(remaining) <= max_chars_per_line:
                        lines[-1] = lines[-1] + " " + remaining
                    else:
                        # Truncate if needed
                        lines[-1] = lines[-1][:max_chars_per_line-3] + "..."
                    break
            # Start new line with current word
            if len(word) > max_chars_per_line:
                # Word is too long, truncate it
                current_line = word[:max_chars_per_line-3] + "..."
            else:
                current_line = word
    
    # Add final line if we haven't reached max_lines (or if max_lines is None)
    if current_line and (max_lines is None or len(lines) < max_lines):
        lines.append(current_line)
    
    return lines if lines else [""]

def type_multi_line(lines_list, char_delay=0.02):
    """
    Type multiple lines of text, displaying up to 6 lines.
    Uses y positions: 0, 10, 20, 30, 40, 50 to match existing code style.
    """
    if len(lines_list) == 0:
        return "", ""
    elif len(lines_list) == 1:
        typed, _ = type_text(lines_list[0], char_delay=char_delay)
        return typed, ""
    elif len(lines_list) == 2:
        l1, l2 = type_two_lines(lines_list[0], lines_list[1], char_delay=char_delay)
        return l1, l2
    else:
        # 3-6 lines - type them all
        # Use y positions: 0, 10, 20, 30, 40, 50 (matching type_two_lines which uses 0, 10)
        lines = [""] * 6  # Initialize 6 line buffers
        
        # Type each line
        for line_idx in range(min(len(lines_list), 6)):
            if not lines_list[line_idx]:
                continue
                
            for ch in lines_list[line_idx]:
                lines[line_idx] += ch
                oled.fill(0)
                # Render all lines typed so far
                for i in range(min(line_idx + 1, 6)):
                    if lines[i]:
                        y_pos = i * 10
                        render_text_with_kaomoji(lines[i], 0, y_pos, max_width=128)
                oled.show()
                time.sleep(char_delay)
        
        # Return first line and last non-empty line for cursor blinking
        last_line = ""
        for i in range(5, -1, -1):
            if lines[i]:
                last_line = lines[i]
                break
        return lines[0] if lines[0] else "", last_line

def type_quote_long(quote, char_delay=0.02):
    """
    Types a quote, wrapping to up to 6 lines if needed.
    Uses word boundaries and displays all text.
    """
    # Sanitize quote first (only replace line breaks)
    q = sanitize_text(quote.replace("\n", " ").strip())
    
    if not q:
        return "", ""
    
    # Wrap text to up to 6 lines for typing animation (max 16 chars per line)
    # Note: Full quote may have more lines, but typing animation only shows first 6
    lines = wrap_text_to_lines(q, max_chars_per_line=16, max_lines=6)
    
    if len(lines) == 0:
        return "", ""
    elif len(lines) <= 2:
        # 1-2 lines - use existing functions
        if len(lines) == 1:
            typed, _ = type_text(lines[0], char_delay=char_delay)
            return typed, ""
        else:
            l1, l2 = type_two_lines(lines[0], lines[1], char_delay=char_delay)
            return l1, l2
    else:
        # 3-6 lines - use multi-line function
        l1, last_line = type_multi_line(lines, char_delay=char_delay)
        return l1, last_line

def show_two_lines(line1, line2, hold_s=2.0):
    oled.fill(0)
    render_text_with_kaomoji(line1, 0, 0, max_width=128)
    render_text_with_kaomoji(line2, 0, 10, max_width=128)
    oled.show()
    time.sleep(hold_s)

# ----------------------------
# TIME FORMATTING
# ----------------------------
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]

def localtime_tuple():
    # MicroPython time.localtime() gives (year, month, mday, hour, minute, second, weekday, yearday)
    # Apply fixed offset for local clock.
    t = time.time() + (TZ_OFFSET_HOURS * 3600)
    return time.localtime(t)

def pick_greeting(hour):
    if hour < 12:
        return random.choice(MORNING)
    elif hour < 18:
        return random.choice(AFTERNOON)
    else:
        return random.choice(EVENING)

def load_override_quotes():
    """
    Load quote overrides from override_dates.json file.
    Returns a dictionary with date strings (YYYY-MM-DD or MM-DD) as keys and quotes as values.
    Returns empty dict if file doesn't exist or can't be parsed.
    """
    try:
        with open("override_dates.json", "r") as f:
            content = f.read().strip()
            # Parse JSON
            overrides = ujson.loads(content)
            return overrides
    except OSError as e:
        # File doesn't exist
        return {}
    except ValueError as e:
        # JSON parse error (e.g., trailing comma, invalid syntax)
        # Return empty dict - JSON file has syntax errors
        return {}
    except Exception as e:
        # Other issue, return empty dict
        return {}

def load_used_quotes():
    """
    Load used quotes from used_quotes.json file.
    Returns a set of quotes that have been used before.
    Returns empty set if file doesn't exist or can't be parsed.
    """
    try:
        with open("used_quotes.json", "r") as f:
            content = f.read().strip()
            if not content or content == "{}":
                return set()
            data = ujson.loads(content)
            # Convert list of quotes to set for fast lookup
            if isinstance(data, dict) and "used" in data:
                return set(data["used"])
            elif isinstance(data, list):
                return set(data)
            else:
                return set()
    except OSError:
        # File doesn't exist, return empty set
        return set()
    except (ValueError, TypeError):
        # JSON parse error or wrong format
        return set()
    except Exception:
        # Other issue
        return set()

def save_used_quote(quote):
    """
    Save a quote to used_quotes.json so it won't be reused on another day.
    """
    try:
        # Load existing used quotes
        used = load_used_quotes()
        # Add the new quote
        used.add(quote)
        # Save back to file
        data = {"used": list(used)}
        with open("used_quotes.json", "w") as f:
            ujson.dump(data, f)
    except Exception:
        # If saving fails, continue anyway (don't break the flow)
        pass

def format_date_string(t):
    """
    Format time tuple as MM-DD string (ignoring year for quote matching).
    t: (year, month, mday, hour, minute, second, weekday, yearday)
    """
    month, mday = t[1], t[2]
    return "%02d-%02d" % (month, mday)

def get_quote_for_today():
    """
    Get the quote for today. Checks override_dates.json first,
    then falls back to a date-seeded random quote (same quote all day).
    
    Uses TEST_DATE if set, otherwise uses actual current date.
    """
    # Load overrides
    overrides = load_override_quotes()
    
    # Get date to use (either test date or actual date)
    if TEST_DATE:
        # Use test date (MM-DD format)
        date_str = TEST_DATE.strip()  # Ensure no whitespace
        # Parse test date to get month and day for seeding
        try:
            month_str, day_str = date_str.split('-')
            month = int(month_str)
            mday = int(day_str)
        except:
            # Fallback: use actual date if test date parsing fails
            t = localtime_tuple()
            date_str = format_date_string(t)
            month, mday = t[1], t[2]
    else:
        # Use actual current date
        t = localtime_tuple()
        date_str = format_date_string(t)  # Format as MM-DD (no year)
        month, mday = t[1], t[2]
    
    # Check if today's date is in overrides
    # First try exact MM-DD match
    if date_str in overrides:
        return overrides[date_str]
    
    # Also check YYYY-MM-DD format keys and extract MM-DD part
    for key, value in overrides.items():
        key_clean = str(key).strip()  # Ensure it's a string and strip whitespace
        # If key is in YYYY-MM-DD format (10 characters: YYYY-MM-DD), extract MM-DD
        if len(key_clean) == 10 and key_clean[4] == '-' and key_clean[7] == '-':
            # Extract MM-DD part (skip first 5 chars "YYYY-")
            key_mm_dd = key_clean[5:]  # Gets "12-27" from "2025-12-27"
            if key_mm_dd == date_str:
                return value
        # Also check if key is already in MM-DD format (5 characters: MM-DD)
        elif len(key_clean) == 5 and key_clean[2] == '-' and key_clean == date_str:
            return value
    
    # No override found, use date-seeded random quote (same quote all day)
    # But exclude quotes that have been used before
    used_quotes = load_used_quotes()
    available_quotes = [q for q in QUOTES if q not in used_quotes]
    
    # If all quotes have been used, reset and start over
    if not available_quotes:
        available_quotes = list(QUOTES)
        # Clear used quotes file to start fresh
        try:
            with open("used_quotes.json", "w") as f:
                ujson.dump({"used": []}, f)
        except Exception:
            pass
    
    # Seed random with date (month and day) so same date = same quote
    random.seed(month * 100 + mday)  # e.g., Dec 27 = 12*100 + 27 = 1227
    quote = random.choice(available_quotes)
    
    # Save this quote as used (so it won't be reused on another day)
    save_used_quote(quote)
    
    return quote

def format_time_lines(t):
    # t: (Y, M, D, h, m, s, weekday, yearday)
    _, month, mday, hh, mm, _, wday, _ = t
    # Format with am/pm
    hour_12 = hh % 12
    if hour_12 == 0:
        hour_12 = 12
    am_pm = "am" if hh < 12 else "pm"
    line1 = "its %d:%02d %s" % (hour_12, mm, am_pm)
    # MicroPython weekday: 0=Mon ... 6=Sun
    wd = WEEKDAYS[wday] if 0 <= wday < 7 else "day"
    mo = MONTHS[month - 1] if 1 <= month <= 12 else "month"
    line2 = "%s, %s %d" % (wd, mo, mday)
    return line1, line2

# ----------------------------
# WIFI + NTP (NON-BLOCKING FEEL)
# ----------------------------
def start_wifi():
    """
    Start WiFi connection with better error handling and debugging.
    Tries multiple networks from WIFI_NETWORKS.
    """
    wlan = network.WLAN(network.STA_IF)
    
    # Deactivate first to ensure clean state
    wlan.active(False)
    time.sleep(0.1)
    wlan.active(True)
    time.sleep(0.1)
    
    # Disable power saving mode for better connection stability
    try:
        wlan.config(pm=0xa11140)  # Disable power saving
    except Exception:
        pass
    
    # Check if already connected
    if wlan.isconnected():
        return wlan
    
    # Try each network in order
    for ssid, password in WIFI_NETWORKS:
        try:
            wlan.connect(ssid, password)
            # Give it a moment to start the connection process
            time.sleep(0.2)
            
            # If it connects quickly, we're done
            if wlan.isconnected():
                return wlan
        except Exception:
            # Try next network
            pass
    
    # Return wlan even if not connected (your existing wait_for_wifi handles failure)
    return wlan


def wait_for_wifi_with_animation(wlan, timeout_s=20):
    """
    Wait for WiFi connection with "looking 4 wifi . . ." text and blinking cursor.
    Shows "no wifi :(" if connection fails after timeout.
    """
    # Type the message once (with wrapping support)
    text = "looking 4 wifi . . ."
    oled.fill(0)
    typed_text, wrapped_lines = type_text(text, x=0, y=0, char_delay=0.03, clear_first=False)
    
    # Get wrapped lines for proper cursor display
    if wrapped_lines is None:
        lines = [typed_text]
    else:
        lines = wrapped_lines
    
    # Now blink cursor while waiting
    deadline = time.ticks_add(time.ticks_ms(), int(timeout_s * 1000))
    cursor_on = True
    last_blink = time.ticks_ms()
    blink_rate = 0.5  # Blink every 500ms
    
    # Calculate text width for cursor position (on last line)
    if len(lines) > 0:
        last_line = lines[-1]
        last_line_width = 0
        for ch in last_line:
            last_line_width += get_char_width(ch)
    else:
        last_line_width = 0
    
    while not wlan.isconnected():
        now = time.ticks_ms()
        
        # Check timeout
        if time.ticks_diff(deadline, now) <= 0:
            # Show "no wifi :(" message
            oled.fill(0)
            type_text("no wifi :(", x=0, y=0, char_delay=0.03, clear_first=False)  # Just type, ignore return
            time.sleep(2.0)  # Show message for 2 seconds
            return False
        
        # Toggle cursor
        if time.ticks_diff(now, last_blink) >= int(blink_rate * 1000):
            cursor_on = not cursor_on
            last_blink = now
        
        # Draw text with blinking cursor
        oled.fill(0)
        # Draw all lines
        for i, line in enumerate(lines):
            y_pos = i * 10
            render_text_with_kaomoji(line, 0, y_pos, max_width=128)
        # Draw cursor on last line
        if cursor_on and len(lines) > 0:
            cursor_x = last_line_width
            if cursor_x < 128:
                last_line_y = (len(lines) - 1) * 10
                oled.text("_", cursor_x, last_line_y)
        oled.show()
        
        # Check connection status periodically
        time.sleep(0.1)
    
    return True

def try_ntp_sync_while_showing_wifi(timeout_s=10):
    """
    Try to sync time via NTP while continuing to show "looking 4 wifi . . ." with blinking cursor.
    Multiple attempts with retry logic.
    """
    text = "looking 4 wifi . . ."
    lines = wrap_text_to_lines(text, max_chars_per_line=16, max_lines=2)
    
    # Calculate cursor position
    if len(lines) > 0:
        last_line = lines[-1]
        last_line_width = 0
        for ch in last_line:
            last_line_width += get_char_width(ch)
    else:
        last_line_width = 0
    
    cursor_on = True
    last_blink = time.ticks_ms()
    blink_rate = 0.5
    
    attempts = 0
    max_attempts = 5
    deadline = time.ticks_add(time.ticks_ms(), int(timeout_s * 1000))
    
    while attempts < max_attempts and time.ticks_diff(deadline, time.ticks_ms()) > 0:
        try:
            ntptime.settime()
            # Verify time is reasonable (after 2020)
            t = time.localtime()
            if t[0] >= 2020:
                return True
        except Exception:
            pass
        
        attempts += 1
        
        # Continue showing "looking 4 wifi . . ." with blinking cursor
        now = time.ticks_ms()
        if time.ticks_diff(now, last_blink) >= int(blink_rate * 1000):
            cursor_on = not cursor_on
            last_blink = now
        
        # Draw text with blinking cursor
        oled.fill(0)
        for i, line in enumerate(lines):
            y_pos = i * 10
            render_text_with_kaomoji(line, 0, y_pos, max_width=128)
        if cursor_on and len(lines) > 0:
            cursor_x = last_line_width
            if cursor_x < 128:
                last_line_y = (len(lines) - 1) * 10
                oled.text("_", cursor_x, last_line_y)
        oled.show()
        
        time.sleep(1)  # Brief pause between attempts
    
    return False

# ----------------------------
# STARTUP FLOW
# ----------------------------
def play_startup_animation_loops(loops=3):
    for _ in range(loops):
        for frame in FRAMES:
            draw_frame(frame)
            time.sleep(FRAME_DELAY)

def play_new_animation_loops(loops=1):
    """Play the new animation (from new_frames)"""
    for _ in range(loops):
        for frame in NEW_FRAMES:
            draw_frame(frame)
            time.sleep(FRAME_DELAY)

def main():
    # Note: random seeding for quotes is done in get_quote_for_today() based on date
    # This ensures the same quote is shown all day, not different quotes on reboot
    gc.collect()

    # 1) startup animation - exactly 3 loops (no more)
    play_startup_animation_loops(loops=3)

    # 2) Connect to WiFi with visual feedback
    wlan = start_wifi()
    wifi_ok = wait_for_wifi_with_animation(wlan, timeout_s=20)

    # 3) Sync time via NTP if WiFi connected (keep showing "looking 4 wifi . . ." until synced)
    ntp_ok = False
    if wifi_ok:
        ntp_ok = try_ntp_sync_while_showing_wifi(timeout_s=10)

    # 4) greeting (typed) + blinking cursor (2 seconds)
    t = localtime_tuple()
    greeting = pick_greeting(t[3])
    typed_greeting, greeting_lines = type_text(greeting, x=0, y=0, char_delay=0.03, clear_first=True)
    # Handle wrapped greeting text
    if greeting_lines is None:
        # Single line
        blink_cursor(typed_greeting, x=0, y=0, duration_s=2.0)
    elif len(greeting_lines) == 2:
        # Two lines
        blink_cursor_two_lines(greeting_lines[0], greeting_lines[1], duration_s=2.0)
    else:
        # 3-6 lines
        blink_cursor_multi_line(greeting_lines, duration_s=2.0)

    # 5) show time and date in new format + blinking cursor (2 seconds)
    t = localtime_tuple()
    line1, line2 = format_time_lines(t)
    typed_l1, typed_l2 = type_two_lines(line1, line2, char_delay=0.02)
    blink_cursor_two_lines(typed_l1, typed_l2, duration_s=2.0)

    # 6) typed "ur quote of the day ..." split across two lines + blinking cursor (2 seconds)
    typed_l1, typed_l2 = type_two_lines("ur quote", "of the day . .", char_delay=0.03)
    blink_cursor_two_lines(typed_l1, typed_l2, duration_s=2.0)

    # 7) chosen quote with smart wrapping + scrolling for long quotes + blinking cursor (20 seconds)
    quote = get_quote_for_today()
    q = sanitize_text(quote.replace("\n", " ").strip())
    # Wrap without max_lines limit to get all lines (for scrolling)
    lines = wrap_text_to_lines(q, max_chars_per_line=16, max_lines=None)
    
    # Type the quote (only first 6 lines for typing animation)
    type_quote_long(quote, char_delay=0.02)
    
    # Display quote with scrolling if needed, then cursor for 20 seconds
    if len(lines) == 1:
        blink_cursor(lines[0], x=0, y=0, duration_s=20.0)
    elif len(lines) == 2:
        blink_cursor_two_lines(lines[0], lines[1], duration_s=20.0)
    elif len(lines) <= 6:
        # 3-6 lines - display all lines with cursor on last line
        blink_cursor_multi_line(lines, duration_s=20.0)
    else:
        # More than 6 lines - use scrolling mechanism
        scroll_quote_with_cursor(lines, duration_s=20.0, scroll_delay_s=2.0)
    
    # 8) Clear screen and play new animation after quote has been shown for 20 seconds
    clear()
    play_new_animation_loops(loops=1)

# Run on boot
main()

