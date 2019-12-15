import cv2
import numpy as np
from networktables import NetworkTables
from picamera import PiCamera
from picamera.array import PiRGBArray

target_real = 0.046
f = 638.6086956521739

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

camera = PiCamera()
res = (320, 240)
camera.resolution = res
camera.exposure_mode = 'off'
camera.exposure_compensation = -25
rawCapture = PiRGBArray(camera, size=res)

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


window = cv2.namedWindow('HSV')
callback = lambda x: None

cv2.createTrackbar('lowH', 'HSV', 0, 179, callback)
cv2.createTrackbar('highH', 'HSV', 0, 179, callback)
cv2.setTrackbarPos('highH', 'HSV', 71)
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


for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
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
        contours.sort(key=cv2.contourArea)
        target = contours[0]
        (x, y), _ = cv2.minEnclosingCircle(target)
        target_pixels = cv2.boundingRect(target)[2]

        distance = (f * target_real) / target_pixels
        cv2.drawContours(frame_copy, filtered_contours, -1, (0, 0, 255), 3)
        print(distance)
        # cv2.putText(frame_copy, str(distance * 100), (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 1,
        #             cv2.LINE_AA)
        if distance:
            set_item('Distance', distance)

    cv2.imshow('frame', frame_copy)
    cv2.imshow('mask', mask_bitwise)

    k = cv2.waitKey(1) & 0xFF
    if k in (27, 113):
        cv2.destroyAllWindows()
        break
