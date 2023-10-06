from screenshot import Screenshot
import solving

for n in [1,2,3,4]:
    screenshot = Screenshot(f'testcases/{n}.png')
    lock_rings = screenshot.read_lock()
    key_rings = screenshot.read_all_key_states()
    print([hex(l) for l in lock_rings])
    moves = solving.solve(lock_rings, key_rings)
    print(moves)
    screenshot.save_debug_image(f'{n}_annotated.png')

# Wait for input keystroke
# Take a screenshot
# Read the game state
# Solve the game
# Input the control sequence