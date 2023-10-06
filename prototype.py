import math
import statistics
from PIL import Image, ImageDraw

# Given a key ring,
# Return the key ring rotated the specified amount, 0 to 31
def rotate_key(key_ring, num_rotations):
    return ((key_ring << num_rotations) | (key_ring >> (32-num_rotations))) & 0xffffffff

# Given a lock ring and a key ring,
# Return a list of num_rotations values that can work
def legal_rotations(lock_ring, key_ring):
    return [i for i in range(32) if (lock_ring | rotate_key(key_ring,i)) == lock_ring]

# Given a lock ring, a list of key rings, and a list of key availability
# Return a list of (key ring index, rotation count) tuples that can work
def legal_moves(lock_ring, key_rings):
    for i in range(len(key_rings)):
        for num_rotations in legal_rotations(lock_ring, key_rings[i]):
            yield (i, num_rotations)

# Given the game situation and a move,
# Return the game situation after the move
def apply_move(lock_rings, key_rings, key_index, num_rotations):
    lock_rings[0] &= ~rotate_key(key_rings[key_index], num_rotations)
    key_rings[key_index] = 0xffffffff
    if lock_rings[0] == 0:
        lock_rings = lock_rings[1:]
    return (lock_rings, key_rings)

# Given a list of lock rings and a list of key rings,
# Return a solution as a list of key ring indices and rotation counts
def solve(lock_rings, key_rings, moves_list=[]):
    if len(lock_rings) == 0:
        return moves_list
    lock_ring = lock_rings[0]
    for (key_index, num_rotations) in legal_moves(lock_ring, key_rings):
        (new_lock_rings, new_key_rings) = apply_move(lock_rings, key_rings, key_index, num_rotations)
        solution = solve(new_lock_rings, new_key_rings, moves_list + [(key_index, num_rotations)])
        if solution:
            return solution
    return None


# ratio of the screen's half-height in pixels to the lock's radius as measured to the middle of the outer ring
half_height_to_lock_radius = 0.3785
# how many lock-radiuses are in a key-to-key-distance?
lock_radius_to_key_distance_x = 0.556 # Guess
lock_radius_to_key_distance_y = 0.544 # Guess
lock_radius_to_key_radius = 0.19 # Guess

# Given a lock ring number (outermost is 0) and a slot rotation number (0 on top and clockwise around),
# Return the screen-resolution-independent polar coordinates in the image to test the brightness of.
# Pretend the outermost lock ring is a thick unit circle at the origin.
def lock_test_polar_coords(ring_number, rotation_number):
    ring_stride = 0.165 # Scratch measurements of random screenshots 0.17 0.16
    r = 1.0 - (ring_stride*ring_number)
    shifted_rotation_number = (rotation_number - 8) % 32
    # rot_num_math_order = (32-shifted_rotation_number) % 32
    theta = 2*math.pi*(shifted_rotation_number / 32.0)
    return (r, theta)

# Given a set of polar coordinates,
# Return the corresponding rectangular coordinates
def polar_to_rectangular(r, theta):
    return (r*math.cos(theta), r*math.sin(theta))

# Given a lock ring number (outermost is 0) and a slot rotation number (0 on top and clockwise around),
# Return the screen-resolution-independent rectangular coordinates in the image to test the brightness of.
# Pretend the outermost lock ring is a thick unit circle at the origin.
def lock_test_rectangular_coords(ring_number, rotation_number):
    (r, theta) = lock_test_polar_coords(ring_number, rotation_number)
    return polar_to_rectangular(r, theta)

# Given a set of rectangular coordinates and the image size and scale,
# Return the screen coordinates
def rectangular_to_screen(x, y, im_width, im_height):
    half_width = im_width / 2.0
    half_height = im_height / 2.0
    pixels_per_unit = half_height * half_height_to_lock_radius # Arbitrarily measured, outer ring radius / half-height ratio
    return (pixels_per_unit * x + half_width, pixels_per_unit * y + half_height)

# Given a lock ring number (outermost is 0) and a slot rotation number (0 on top and clockwise around),
# Return the on-screen pixel coordinates to test the brightness of.
def lock_test_screen_coords(ring_number, rotation_number, im_width, im_height):
    (x, y) = lock_test_rectangular_coords(ring_number, rotation_number)
    return rectangular_to_screen(x, y, im_width, im_height)

# Given 0-255 RGB values in a tuple (r, g, b),
# Return the 0.0-1.0 subjective brightness value
def rgb_to_brightness(rgb):
    return (0.21*rgb[0] + 0.72*rgb[1] + 0.07*rgb[2]) / 255.0

# Given a px_data array and xy coords,
# Return the brightness value there in the 0.0-1.0 range
def test_brightness_at(px_data, x, y):
    try:
        return rgb_to_brightness(px_data[x, y])
    except IndexError:
        return 0.0

def walk_pixel_to_dark(px_data, threshold, orig_x, orig_y, step_x, step_y):
    cx, cy = orig_x, orig_y
    brightness = test_brightness_at(px_data, cx, cy)
    while brightness > threshold:
        cx += step_x
        cy += step_y
        brightness = test_brightness_at(px_data, cx, cy)
    return cx, cy

def find_first_key(px_data, im_width, im_height, draw):
    min_x = int(im_width*.7)
    max_x = int(im_width*.95)
    min_y = int(im_height*.25)
    max_y = int(im_height*.75)
    draw.line([(min_x,0),(min_x,im_height)], fill='cyan')
    draw.line([(max_x,0),(max_x,im_height)], fill='cyan')
    draw.line([(0,min_y),(im_width,min_y)], fill='cyan')
    draw.line([(0,max_y),(im_width,max_y)], fill='cyan')

    print(f"x from {min_x} to {max_x}")
    print(f"y from {min_y} to {max_y}")

    # Walk through the region where the keys might be with a stride of 10px
    # in both directions and gather the average and stdev of the brightness
    brightnesses = []
    grid_step = 20 # TODO sense resolution of image and adjust
    for x in range(min_x, max_x, grid_step):
        for y in range(min_y, max_y, grid_step):
            brightnesses.append(test_brightness_at(px_data, x, y))
    stdev_brightness = statistics.stdev(brightnesses)
    mean_brightness = statistics.mean(brightnesses)

    # Any pixels with a sufficiently anomalous brightness might be in the spot
    # in the center of the first key
    candidates = []
    for x in range(min_x, max_x, grid_step):
        for y in range(min_y, max_y, grid_step):
            b = test_brightness_at(px_data, x, y)
            if b > (mean_brightness + 3*stdev_brightness):
                candidates.append((x,y))
    
    max_radius = 0
    best_point = (0,0)

    debug_info = []

    for candidate in candidates:

        cx, cy = candidate

        threshold = mean_brightness + stdev_brightness
        (x_plus_x, x_plus_y) = walk_pixel_to_dark(px_data, threshold, cx, cy, 1, 0)
        (x_minus_x, x_minus_y) = walk_pixel_to_dark(px_data, threshold, cx, cy, -1, 0)
        (y_plus_x, y_plus_y) = walk_pixel_to_dark(px_data, threshold, cx, cy, 0, 1)
        (y_minus_x, y_minus_y) = walk_pixel_to_dark(px_data, threshold, cx, cy, 0, -1)
        
        center_x, center_y = (x_plus_x + x_minus_x) / 2.0, (y_plus_y + y_minus_y) / 2.0

        radius_measurements = [
            math.dist((center_x, center_y), (x_plus_x, x_plus_y)),
            math.dist((center_x, center_y), (x_minus_x, x_minus_y)),
            math.dist((center_x, center_y), (y_plus_x, y_plus_y)),
            math.dist((center_x, center_y), (y_minus_x, y_minus_y)),
        ]
        radius = statistics.mean(radius_measurements)
        radius_stdev = statistics.stdev(radius_measurements)
        debug_info.append([cx, cy, center_x, center_y, radius, radius_stdev])
        if radius_stdev > 2.0: # TODO this fudge factor is arbitrary
            if draw:
                draw.ellipse((cx-10, cy-10, cx+10, cy+10), fill = None, outline ='red')
            continue
        else:
            if draw:
                draw.ellipse((cx-10, cy-10, cx+10, cy+10), fill = None, outline ='green')

        if radius > max_radius:
            best_point = (center_x, center_y)
            max_radius = radius
    [print(x) for x in debug_info]
    fkx, fky = best_point
    draw.ellipse((fkx-10, fky-10, fkx+10, fky+10), fill = None, outline ='blue')
    return best_point

# Given a lock ring number (outermost is 0) and a slot rotation number (0 on top and clockwise around),
# Return the screen-resolution-independent polar coordinates in the image to test the brightness of.
# Pretend the outermost lock ring is a thick unit circle at the origin.
def key_test_polar_coords(rotation_number):
    lock_radius_px = (im_height / 2.0) * half_height_to_lock_radius
    r = lock_radius_to_key_radius * lock_radius_px
    shifted_rotation_number = (rotation_number - 8) % 32
    theta = 2*math.pi*(shifted_rotation_number / 32.0)
    return (r, theta)

def key_test_rectangular_coords(rotation_number):
    r, theta = key_test_polar_coords(rotation_number)
    return polar_to_rectangular(r,theta)

def find_all_key_centers(px_data, im_width, im_height, draw):
    first_key_center = find_first_key(px_data, im_width, im_height, draw)
    lock_radius_px = (im_height / 2.0) * half_height_to_lock_radius
    key_distance_x = lock_radius_px * lock_radius_to_key_distance_x
    key_distance_y = lock_radius_px * lock_radius_to_key_distance_y
    potential_keys = []
    for row_num in range(3):
        for col_num in range(4):
            x, y = (first_key_center[0] + int(col_num*key_distance_x),
                    first_key_center[1] + int(row_num*key_distance_y))
            if draw:
                draw.ellipse((x-5, y-5, x+5, y+5), fill = 'purple', outline ='purple')
            potential_keys.append((x,y))
    return potential_keys

def read_one_key_state(px_data, key_x, key_y, im_width, im_height, draw):
    brightnesses = []
    print(f"Looking at key at {key_x}, {key_y}")
    for rotation_number in range(32):
        (x0, y0) = key_test_rectangular_coords(rotation_number)
        (x, y) = x0+key_x, y0+key_y
        if draw:
            draw.ellipse((x-1, y-1, x+1, y+1), fill = 'yellow', outline ='yellow')
        brightnesses.append(test_brightness_at(px_data, x, y))
    stdev_brightness = statistics.stdev(brightnesses)
    if stdev_brightness < 0.07: # arbitrary threshold
        print("Key not present")
        return 0
    mean_brightness = statistics.mean(brightnesses)
    key = 0
    for i in range(32):
        if brightnesses[i] > mean_brightness:
            key |= (1 << i)
    return key

def read_all_key_states(px_data, im_width, im_height, draw):
    keys = []
    for (kx, ky) in find_all_key_centers(px_data, im_width, im_height, draw):
        keys.append(read_one_key_state(px_data, kx, ky, im_width, im_height, draw))
    return keys

# Given a screenshot,
# Return the lock rings array, and
# Optionally, save off a test-output image showing what the script sees
def get_lock_rings_from_screenshot(px_data, im_width, im_height, draw=None):
    lock_rings = [0,0,0,0]
    for ring_number in range(4):
        for rotation_number in range(32):
            (x, y) = lock_test_screen_coords(ring_number, rotation_number, im_width, im_height)
            threshold = 0.01
            # TODO, keep it screen-res independent (scale this box depending) but I'm too lazy for now
            brightnesses = []
            for dx in [-2,-1,0,1,2]:
                for dy in [-2,-1,0,1,2]:
                    brightnesses.append(test_brightness_at(px_data, x+dx, y+dy))
            stdev_brightness = statistics.stdev(brightnesses)
            if stdev_brightness < threshold:
                lock_rings[ring_number] |= (1 << rotation_number)
                if draw:
                    draw.ellipse((x-10, y-10, x+10, y+10), fill = None, outline ='green')
            else:
                if draw:
                    draw.ellipse((x-10, y-10, x+10, y+10), fill = None, outline ='red')
            if draw:
                draw.text((x,y), f"{rotation_number}", fill=(255, 255, 0))
        if lock_rings[ring_number] == 0xffffffff:
            lock_rings = lock_rings[:ring_number]
            break
    return lock_rings

for n in [1,2,3,4]:
    # screenshot = pyautogui.screenshot()
    screenshot = Image.open(f'testcases/{n}.png')
    test_image = screenshot.copy()
    draw = ImageDraw.Draw(test_image)
    px_data = screenshot.load()
    im_width, im_height = screenshot.width, screenshot.height
    lock_rings = get_lock_rings_from_screenshot(px_data, im_width, im_height, draw)
    print([hex(l) for l in lock_rings])
    key_rings = read_all_key_states(px_data, im_width, im_height, draw)
    moves = solve(lock_rings, key_rings)
    # print(moves)
    test_image.save(f'{n}_annotated.png')


# test_lock = [0b101, 0b0001000100010001]
# test_keys = [0b100000001, 0b1010, 0x10000010]
print(solve(test_lock, test_keys))

