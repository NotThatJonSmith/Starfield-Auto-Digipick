from PIL import Image, ImageGrab, ImageDraw
import argparse
import pyautogui
import pydirectinput
import sys
import time
import win32gui

from screenshot_reader import ScreenshotReader
import solving

# TODO, would like to be able to solve from any current solvable state of the game
# Right now the only reason that's not possible is
#   the first ring having hardcoded specialness
#   the selected key being assumed as key 0 in the grid.
# Both are pretty easy fixes, just a bit of a chore for later

# Return a PIL Image of Starfield
def take_starfield_screenshot():
    hwnd = win32gui.FindWindow(None, r'Starfield')
    win32gui.SetForegroundWindow(hwnd)
    win32gui.SetActiveWindow(hwnd)
    dimensions = win32gui.GetWindowRect(hwnd)
    # When Starfield is focused it goes to the pause menu, which takes some time
    time.sleep(1.5)
    # Get out of pause
    pydirectinput.press('esc')
    # Hack because fullscreen Starfield gives 0x0 dimensions
    if dimensions[0] == 0 or dimensions[1] == 0:
        return ImageGrab.grab(dimensions)
    return pyautogui.screenshot()

parser = argparse.ArgumentParser(
    prog='Starfield-Auto-Digipick',
    description='Automatically solve the digipicking minigame',
)

parser.add_argument('-d', '--dry_run', action='store_true')
parser.add_argument('-g', '--debug', action='store_true')
parser.add_argument('-i', '--from-image')
args = parser.parse_args(sys.argv[1:])

t0 = time.time()

sf_pil = Image.open(args.from_image) if args.from_image else take_starfield_screenshot()

debug_pil = None
debug_draw = None
if args.debug:
    debug_pil = sf_pil.copy()
    debug_draw = ImageDraw.Draw(debug_pil)
reader = ScreenshotReader(sf_pil, debug_draw)

t1 = time.time()

lock_rings = reader.read_lock()

t2 = time.time()

key_rings = reader.read_all_key_states()

t3 = time.time()

if args.debug:
    debug_pil.save('debug.png')
    sf_pil.save('screen.png')

t4 = time.time()

moves = solving.solve(lock_rings, key_rings)

t5 = time.time()

control_sequence = solving.moves_to_keystrokes(moves, key_rings)
print(f"Control sequence: {control_sequence}")

t6 = time.time()

print(f"""Timing summary (milliseconds))
    screenshot prep:    {int(1000*(t1-t0))}
    reading lock:       {int(1000*(t2-t1))}
    reading keys:       {int(1000*(t3-t2))}
    saving images:      {int(1000*(t4-t3))}
    game solving:       {int(1000*(t5-t4))}
    control sequencing: {int(1000*(t6-t5))}
""")

if not args.dry_run:
    pydirectinput.typewrite(control_sequence)