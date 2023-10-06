import math
import pyautogui
import statistics
from PIL import Image, ImageDraw

# Value guesses
height_to_lock_radius = 0.3785 / 2.0
lock_radius_to_key_distance_x = 0.555 # The horizontal distance between columns of keys
lock_radius_to_key_distance_y = 0.544 # The vertical distance between rows of keys
lock_radius_to_key_radius = 0.185 # The radius of a key ring
lock_ring_stride = 0.165 # The distance between individual lock rings

class Screenshot(object):

    def __init__(self, filename=None):
        if filename:
            self.im = Image.open(filename)
        else:
            self.im = pyautogui.screenshot()
        self.px = self.im.load()
        self.test_output_im = self.im.copy()
        self.draw = ImageDraw.Draw(self.test_output_im)
        self.lock_radius_px = self.im.height * height_to_lock_radius
        self.key_distance_x = self.lock_radius_px * lock_radius_to_key_distance_x
        self.key_distance_y = self.lock_radius_px * lock_radius_to_key_distance_y

    def save_debug_image(self, filename):
        self.test_output_im.save(filename)

    # Given an x,y coordinate in the image,
    # Return the subjective brightness value there, where out-of-image pixels are assumed to be black
    def brightness(self, x, y):
        try:
            r,g,b = self.px[x, y]
            return (0.21*r + 0.72*g + 0.07*b) / 255.0
        except IndexError:
            return 0.0
        except ValueError:
            return 0.0

    def read_lock(self):
        lock_rings = [0,0,0,0]
        for ring_number in range(4):
            for rotation_number in range(32):
                r = self.lock_radius_px * (1.0 - (lock_ring_stride*ring_number))
                theta = 2*math.pi*(((rotation_number - 8) % 32) / 32.0)
                x, y = (r*math.cos(theta) + (self.im.width / 2.0),
                        r*math.sin(theta) + (self.im.height / 2.0))
                threshold = 0.01 # TODO, keep it screen-res independent (scale this box depending) but I'm too lazy for now
                brightnesses = []
                for dx in [-2,-1,0,1,2]:
                    for dy in [-2,-1,0,1,2]:
                        brightnesses.append(self.brightness(x+dx, y+dy))
                if statistics.stdev(brightnesses) < threshold:
                    lock_rings[ring_number] |= (1 << rotation_number)
                    self.draw.ellipse((x-10, y-10, x+10, y+10), fill = None, outline ='green')
                else:
                    self.draw.ellipse((x-10, y-10, x+10, y+10), fill = None, outline ='red')
                self.draw.text((x,y), f"{rotation_number}", fill=(255, 255, 0))
            if lock_rings[ring_number] == 0xffffffff:
                lock_rings = lock_rings[:ring_number]
                break
        return lock_rings

    def walk_pixel_to_dark(self, threshold, orig_x, orig_y, step_x, step_y):
        cx, cy = orig_x, orig_y
        while self.brightness(cx, cy) > threshold:
            cx, cy = cx + step_x, cy + step_y
        return cx, cy

    def find_first_key(self):
        min_x = int(self.im.width*.7)
        max_x = int(self.im.width*.95)
        min_y = int(self.im.height*.25)
        max_y = int(self.im.height*.75)
        self.draw.line([(min_x,0),(min_x,self.im.height)], fill='cyan')
        self.draw.line([(max_x,0),(max_x,self.im.height)], fill='cyan')
        self.draw.line([(0,min_y),(self.im.width,min_y)], fill='cyan')
        self.draw.line([(0,max_y),(self.im.width,max_y)], fill='cyan')

        # Walk through the region where the keys might be with a stride of 10px
        # in both directions and gather the average and stdev of the brightness
        brightnesses = []
        grid_step = 20 # TODO sense resolution of image and adjust
        for x in range(min_x, max_x, grid_step):
            for y in range(min_y, max_y, grid_step):
                brightnesses.append(self.brightness(x, y))
        stdev_brightness = statistics.stdev(brightnesses)
        mean_brightness = statistics.mean(brightnesses)

        # Any pixels with a sufficiently anomalous brightness might be in the spot
        # in the center of the first key
        candidates = []
        for x in range(min_x, max_x, grid_step):
            for y in range(min_y, max_y, grid_step):
                b = self.brightness(x, y)
                if b > (mean_brightness + 3*stdev_brightness):
                    candidates.append((x,y))
        
        max_radius = 0
        best_point = (0,0)
        debug_info = []
        for candidate in candidates:
            cx, cy = candidate
            threshold = mean_brightness + stdev_brightness
            x_plus_x, x_plus_y = self.walk_pixel_to_dark(threshold, cx, cy, 1, 0)
            x_minus_x, x_minus_y = self.walk_pixel_to_dark(threshold, cx, cy, -1, 0)
            y_plus_x, y_plus_y = self.walk_pixel_to_dark(threshold, cx, cy, 0, 1)
            y_minus_x, y_minus_y = self.walk_pixel_to_dark(threshold, cx, cy, 0, -1)
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
                self.draw.ellipse((cx-10, cy-10, cx+10, cy+10), fill = None, outline ='red')
                continue
            else:
                self.draw.ellipse((cx-10, cy-10, cx+10, cy+10), fill = None, outline ='green')
            if radius > max_radius:
                best_point = (center_x, center_y)
                max_radius = radius
        fkx, fky = best_point
        self.draw.ellipse((fkx-10, fky-10, fkx+10, fky+10), fill = None, outline ='blue')
        return best_point

    def key_at(self, key_x, key_y):
        brightnesses = []
        for rotation_number in range(32):
            r = lock_radius_to_key_radius * self.im.height * height_to_lock_radius
            theta = 2*math.pi*(((rotation_number - 8) % 32) / 32.0)
            (x0, y0) = (r*math.cos(theta), r*math.sin(theta))
            (x, y) = x0+key_x, y0+key_y
            self.draw.ellipse((x-1, y-1, x+1, y+1), fill = 'yellow', outline ='yellow')
            brightnesses.append(self.brightness(x, y))
        if statistics.stdev(brightnesses) < 0.07: # arbitrary threshold
            return 0
        mean_brightness = statistics.mean(brightnesses)
        key = 0
        for rotation_number in range(32):
            r = lock_radius_to_key_radius * self.im.height * height_to_lock_radius
            theta = 2*math.pi*(((rotation_number - 8) % 32) / 32.0)
            (x0, y0) = (r*math.cos(theta), r*math.sin(theta))
            (x, y) = x0+key_x, y0+key_y
            if brightnesses[rotation_number] > mean_brightness:
                key |= (1 << rotation_number)
                self.draw.line([(key_x,key_y),(x,y)], fill='cyan')
        return key

    def read_all_key_states(self):
        result = []
        first_key_center = self.find_first_key()
        for row_num in range(3):
            for col_num in range(4):
                x, y = (first_key_center[0] + int(col_num*self.key_distance_x),
                        first_key_center[1] + int(row_num*self.key_distance_y))
                self.draw.ellipse((x-5, y-5, x+5, y+5), fill = 'purple', outline ='purple')
                result.append(self.key_at(x, y))
        return result

