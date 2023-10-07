from PIL import Image, ImageGrab
import time
import pyautogui
import pydirectinput
import sys
import win32gui

from screenshot import Screenshot
import solving
import control

sf_pil = None

if len(sys.argv) > 1:
    filename = sys.argv[1]
    sf_pil = Image.open(filename)
else:
    hwnd = win32gui.FindWindow(None, r'Starfield')
    win32gui.SetForegroundWindow(hwnd)
    win32gui.SetActiveWindow(hwnd)
    dimensions = win32gui.GetWindowRect(hwnd)

    time.sleep(2.0)
    pydirectinput.press('esc')

    # Hack because fullscreen Starfield gives 0x0 dimensions
    if dimensions[0] == 0 or dimensions[1] == 0:
        sf_pil = ImageGrab.grab(dimensions)
    else:
        sf_pil = pyautogui.screenshot()

screenshot = Screenshot(sf_pil)
lock_rings = screenshot.read_lock()
key_rings = screenshot.read_all_key_states()
screenshot.save_debug_image('screen.png', 'debug.png')
moves = solving.solve(lock_rings, key_rings)
control_sequence = control.inputs_for_solution(moves, key_rings)
print(f"Control sequence: {control_sequence}")

if len(sys.argv) <= 1:
    pydirectinput.typewrite(control_sequence)