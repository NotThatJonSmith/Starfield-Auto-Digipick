from PIL import Image, ImageGrab
import time
import pyautogui
import pydirectinput
import sys
import win32gui

from screenshot_reader import ScreenshotReader
import solving

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

sf_pil = Image.open(sys.argv[1]) if len(sys.argv) > 1 else take_starfield_screenshot()
reader = ScreenshotReader(sf_pil)
lock_rings = reader.read_lock()
key_rings = reader.read_all_key_states()
# TODO, would like to be able to solve from any current solvable state of the game
# Right now the only reason that's not possible is
#   the first ring having hardcoded specialness
#   the selected key being assumed as key 0 in the grid.
# Both are pretty easy fixes, just a bit of a chore for later
reader.save_debug_image('screen.png', 'debug.png')
moves = solving.solve(lock_rings, key_rings)
control_sequence = solving.moves_to_keystrokes(moves, key_rings)
print(f"Control sequence: {control_sequence}")

if len(sys.argv) <= 1:
    pydirectinput.typewrite(control_sequence)