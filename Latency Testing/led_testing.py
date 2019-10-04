import cv2
import numpy as np
import datetime
# import led_toggle
from file_hsv import FileHSV
import utils


def log(info):
    """
    Modify to log properly.
    :param info:
    :return:
    """
    print(info)


cam = cv2.VideoCapture(0)
cam.set(15, -10)

hsv_handler = FileHSV(name='led', up=1)

kernel = np.array([[0, 1, 0],
                   [1, 1, 1],
                   [0, 1, 0]], dtype=np.uint8)

# led_toggle.on()
led_time = datetime.datetime.now()
log(f'{led_time.__str__()};')

# datetime.timedelta(led_time.microsecond - datetime.datetime.now().microsecond) < datetime.timedelta(microseconds=75000)

orginal = cam.read()[1]
cv2.imwrite('start.jpg', orginal)

while True:
    orginal = cam.read()[1]
    frame = orginal.copy()

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mask = utils.hsv_mask(frame, hsv_handler.get_hsv())

    mask = utils.morphology(mask, kernel)

    contours = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
    if contours:

        fitered_contours = []

        for cnt in contours:
            if 1000 < cv2.contourArea(cnt) < 10000:
                fitered_contours.append(cnt)

        if fitered_contours:
            detect_time = datetime.datetime.now()
            log(f'{datetime.timedelta(detect_time.microsecond - led_time.microsecond).microseconds};')
            cv2.drawContours(orginal, contours, -1, (255, 255, 255), 3)

            cv2.imwrite('led.jpg', orginal)

            # led_toggle.off()
            break