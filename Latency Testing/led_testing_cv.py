import cv2
import numpy as np
import datetime
import led_toggle
from time import sleep

import os, sys, inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import file_hsv
import utils

led_toggle.__init__()


def log(info):
    """
    Modify to log properly.
    :param info:
    :return:
    """
    print(info)


cam = cv2.VideoCapture(0)
cam.set(15, -5)
# cam.set(11, 7)

hsv_handler = file_hsv.FileHSV(name='led', up=1)
print(hsv_handler.get_hsv())

kernel = np.array([[0, 1, 0],
                   [1, 1, 1],
                   [0, 1, 0]], dtype=np.uint8)

led_toggle.on()
led_time = datetime.datetime.now()
log(f'On: {float(led_time.microsecond)};')

orginal = cam.read()[1]
cv2.imwrite('start.jpg', orginal)

stop = False

while not stop:
    orginal = cam.read()[1]
    frame = orginal.copy()

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mask = utils.hsv_mask(frame, hsv_handler.get_hsv())

    mask = utils.morphology(mask, kernel)
    # this line adds ~100 ms delay!!

    contours = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
    if contours:
        filtered_contours = []

        for cnt in contours:
            if 1000 < cv2.contourArea(cnt):
                filtered_contours.append(cnt)

        if filtered_contours:
        # the filtering removed another ~300 ms...

            detect_time = datetime.datetime.now()
            log(f'Delay: {(float(detect_time.microsecond) - float(led_time.microsecond)) / 1000};')
            cv2.drawContours(orginal, contours, -1, (255, 0, 0), 3)
            # and this shrinks it by 300 to 20 ms

            cv2.imwrite('led.jpg', orginal)

            led_toggle.off()
            stop = True

    if float(datetime.datetime.now().microsecond) - float(led_time.microsecond) >= 500:
        led_toggle.off()
        sleep(1)
        led_toggle.on()
        led_time = datetime.datetime.now()
        continue
