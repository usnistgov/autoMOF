import cv2
import numpy as np
from north_simple_camera import SimpleCamera, SimplePhoto
from time import sleep

def crop_img(img, x1, y1, x2, y2):
    cropped_img = img[y1:y2, x1:x2].copy()
    on_original = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    on_original = cv2.cvtColor(on_original, cv2.COLOR_GRAY2BGR)
    on_original = cv2.blur(on_original, (15, 15))
    on_original[y1:y2, x1:x2] = cropped_img
    return cropped_img, on_original

def get_color(img):
       
    return np.array(img.mean(axis=0).mean(axis=0), dtype=np.uint8)
if __name__ == "__main__":
    cam = SimpleCamera(2)

    sleep(5)  # let camera object load

    pic = cam.capture()
    print(pic.get_size())
    cropped, original = crop_img(pic.img, *[500, 130, 840, 375])
    avg_color = get_color(cropped)
    #SimplePhoto(original).show()
    avg_color_tile = SimplePhoto(np.tile(avg_color, reps=(200, 200, 1)))
    #avg_color_tile.show()
    print(avg_color)
    print(np.flipud(avg_color))