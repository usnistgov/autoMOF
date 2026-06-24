import cv2
import imutils
from matplotlib import pyplot as plt
from time import sleep
plt.ion()

from north_simple_camera import SimpleCamera, SimplePhoto
import im_proc
 
cam = SimpleCamera(0)
sleep(1)
pic = cam.capture()
crop_cords=[615, 350, 630, 650]
cropped, original = im_proc.crop_img(pic.img, *crop_cords)
 
#vial_img = "C:\\Users\\djlok\\Desktop\\north projects\\vision\\photo 1_test.bmp"
#vial_img = cv2.imread(vial_img, cv2.IMREAD_COLOR)
vial_img = cropped

#def measure_px_height():
#    vial_img = r"C:\Users\drmxlt\Documents\robot_setup\test1\SAMPLE_20250306-143248.png"
#    vial_img = cv2.imread(vial_img, cv2.IMREAD_COLOR)


# Have images, do analysis
vial_img_g = cv2.split(vial_img)[0]

# perform gaussian blur
vial_img_g = cv2.GaussianBlur(vial_img_g, (7, 7), 0)

# Use values histogram to find a threshold
plt.hist(vial_img_g.ravel(), 256, [0, 256])

t_vial = 115

# perform manual thresholding
(TV, vial_threshed) = cv2.threshold(vial_img_g, t_vial, 255, cv2.THRESH_BINARY)

# apply opening operation (see htatps://en.wikipedia.org/wiki/Opening_(morphology))
kern = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
vial_open = cv2.morphologyEx(vial_threshed, cv2.MORPH_OPEN, kern)

# find countours
contours_vial = imutils.grab_contours(
    cv2.findContours(vial_open.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE))
# sort contours by area
areas_vial = [cv2.contourArea(contour) for contour in contours_vial]
(contours_vial, areas_vial) = zip(*sorted(zip(contours_vial, areas_vial), key=lambda a: a[1]))

# draw bounding box (Vial)
vial_copy = vial_img.copy()
(x, y, w, h) = cv2.boundingRect(contours_vial[-1])  # bounds of largest contour
cv2.rectangle(vial_copy, (x, y), (x + w, y + h), (0, 0, 255), 2)
cv2.putText(vial_copy, "Liquid", (x + 10, y + 20), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 2)
print(f"Vial liquid level: {h}px")

# print(f"Aspect ratio: %.3f" % (float(w) / float(h)))
image2show=im_proc.place_on_original(vial_copy,pic.img,crop_cords)
cv2.imshow("Vial (bounded)", image2show)
plt.show()
plt.pause(0.01)

cv2.imshow("Vial (threshold)", vial_threshed)
plt.show()
 
#return h

