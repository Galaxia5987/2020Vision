import math

import cv2
import numpy as np
from networktables import NetworkTables
from picamera import PiCamera
from picamera.array import PiRGBArray
from time import sleep

target_real = 1.475
f = 940
horizontalFov = 62.2


def connection_listener(connected, info):
    if connected:
        print('Successfully connected.\n{}'.format(info))
    else:
        print('Failed to connect.\n{}'.format(info))


server = '10.59.87.2'
NetworkTables.setUpdateRate(0.01)
NetworkTables.initialize(server=server)
NetworkTables.addConnectionListener(connection_listener, immediateNotify=True)
table = NetworkTables.getTable('Vision')


def set_item(key, value):
    """
    Add a value to SmartDashboard.

    :param key: The name the value will be stored under and displayed.
    :param value: The information the key will hold.
    """
    table.putValue(key, value)


def get_item(key, default_value):
    """
    Get a value from SmartDashboard.

    :param key: The name the value is stored under.
    :param default_value: The value returned if key holds none.
    :return: The value that the key holds, default_value if it holds none.
    """
    return table.getValue(key, default_value)


set_item('FPS', 30)
set_item('Latency (ms)', 0)

camera = PiCamera()
origin_res = camera.resolution
res = (320, 240)
focal_ratio = res[0] / origin_res[0]
camera.resolution = res
camera.brightness = 40
camera.exposure_mode = 'sports'
camera.exposure_compensation = -10
camera.framerate = get_item('FPS', 30)
rawCapture = PiRGBArray(camera, size=res)


def get_center(cnt: np.array) -> (float, float):
    """
    See: cv2.moments()
    :param cnt: A contour.
    :return: X and Y coordinate of the center pixel.
    """
    # Get center of the contour
    moment = cv2.moments(cnt)
    try:
        x = int(moment['m10'] / moment['m00'])
        y = int(moment['m01'] / moment['m00'])
        return x, y
    except ZeroDivisionError:
        return None, None


def calc_horizontal_offset(pixelX):
    focal = res[0] / (2 * math.tan(horizontalFov / 2))
    return math.degrees(math.atan((pixelX - (res[0] / 2)) / focal))


window = cv2.namedWindow('HSV')
callback = lambda x: None

cv2.createTrackbar('lowH', 'HSV', 0, 179, callback)
cv2.createTrackbar('highH', 'HSV', 0, 179, callback)
cv2.setTrackbarPos('highH', 'HSV', 90)
cv2.setTrackbarPos('lowH', 'HSV', 61)

cv2.createTrackbar('lowS', 'HSV', 0, 255, callback)
cv2.createTrackbar('highS', 'HSV', 0, 255, callback)
cv2.setTrackbarPos('highS', 'HSV', 255)
cv2.setTrackbarPos('lowS', 'HSV', 87)

cv2.createTrackbar('lowV', 'HSV', 0, 255, callback)
cv2.createTrackbar('highV', 'HSV', 0, 255, callback)
cv2.setTrackbarPos('highV', 'HSV', 255)
cv2.setTrackbarPos('lowV', 'HSV', 66)

kernel = np.array([[0, 1, 0],
                   [1, 1, 1],
                   [0, 1, 0]], dtype=np.uint8)


def get_hsv():
    low_h = cv2.getTrackbarPos('lowH', 'HSV')
    high_h = cv2.getTrackbarPos('highH', 'HSV')
    low_s = cv2.getTrackbarPos('lowS', 'HSV')
    high_s = cv2.getTrackbarPos('highS', 'HSV')
    low_v = cv2.getTrackbarPos('lowV', 'HSV')
    high_v = cv2.getTrackbarPos('highV', 'HSV')

    low = [low_h, low_s, low_v]
    high = [high_h, high_s, high_v]

    return {'low': low, 'high': high}


def rectangularity(cnt):
    _, _, w, h = cv2.boundingRect(cnt)
    area = cv2.contourArea(cnt)

    return area / (w * h)


# def y_angle(frame, ytarget):
#     yframe = frame.shape[0] / 2
#     return math.atan2((ytarget - yframe), f * focal_ratio) * (180 / math.pi)
#
#
# def distance_by_tan(angle, height_delta):
#     return height_delta / math.tan(angle)


for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    sleep(get_item('Latency (ms)', 0) / 1000)
    camera.framerate = get_item('FPS', 30)
    frame = frame.array
    # clear the stream in preparation for the next frame
    rawCapture.truncate(0)
    frame_copy = frame.copy()

    hsv = get_hsv()

    frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(frame_hsv, np.array(hsv['low']), np.array(hsv['high']))
    mask = cv2.dilate(mask, kernel)
    mask = cv2.erode(mask, kernel)
    mask_bitwise = cv2.bitwise_and(frame, frame, mask=mask)

    contours = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 2:
        contours = contours[0]
    else:
        contours = contours[1]

    filtered_contours = []

    if contours:
        for cnt in contours:
            if cv2.contourArea(cnt) > 50:
                filtered_contours.append(cnt)
        cv2.drawContours(frame_copy, contours, -1, (255, 0, 0), 3)

    if filtered_contours:
        filtered_contours.sort(key=cv2.contourArea)
        target = filtered_contours[-1]
        # (x, y), _ = cv2.minEnclosingCircle(target)
        # target_pixels = cv2.contourArea(cnt)

        distance = ((cv2.contourArea(target) / (res[0] * res[1]) * 100) ** -0.507) * 0.918
        # distance = ((f * target_real) / target_pixels ) * focal_ratio

        # focal = (1 * target_pixels) / (target_real * focal_ratio)
        cv2.drawContours(frame_copy, filtered_contours, -1, (0, 0, 255), 3)
        # cv2.putText(frame_copy, str(distance * 100), (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 1,
        #           cv2.LINE_AA)
        angle = calc_horizontal_offset(get_center(target)[0])
        set_item('distance', distance)
        set_item('angle', angle)

        print(distance, angle)
    else:
        set_item('distance', 0)
        set_item('angle', 0)
    cv2.imshow('frame', frame_copy)
    cv2.imshow('mask', mask_bitwise)

    k = cv2.waitKey(1) & 0xFF
    if k in (27, 113):
        cv2.destroyAllWindows()
        break
