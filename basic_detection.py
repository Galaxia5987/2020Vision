import cv2
import numpy as np

port = input('Camera port: ')

try:
    camera = cv2.VideoCapture(int(port))
except:
    camera = cv2.VideoCapture(0)

exposure = input('Exposure: ')

try:
    camera.set(15, int(exposure))
except:
    camera.set(15, 0)

window = cv2.namedWindow('HSV')
callback = lambda x: None

cv2.createTrackbar('lowH', 'HSV', 0, 179, callback)
cv2.createTrackbar('highH', 'HSV', 0, 179, callback)
cv2.setTrackbarPos('highH', 'HSV', 179)

cv2.createTrackbar('lowS', 'HSV', 0, 255, callback)
cv2.createTrackbar('highS', 'HSV', 0, 255, callback)
cv2.setTrackbarPos('highS', 'HSV', 255)

cv2.createTrackbar('lowV', 'HSV', 0, 255, callback)
cv2.createTrackbar('highV', 'HSV', 0, 255, callback)
cv2.setTrackbarPos('highV', 'HSV', 255)

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


while True:
    try:
        frame = camera.read()[1]
        frame_copy = frame.copy()
    except AttributeError:
        continue

    hsv = get_hsv()

    frame_hsv = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(frame_hsv, np.array(hsv['low']), np.array(hsv['high']))
    mask = cv2.dilate(mask, kernel)
    mask = cv2.erode(mask, kernel)
    mask_bitwise = cv2.bitwise_and(frame, frame, mask=mask)

    contours = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 2:
        contours = contours[0]
    else:
        contours = contours[1]

    if contours:
        cv2.drawContours(frame, contours, -1, (0, 255, 0), 3)

    cv2.imshow('frame', frame)
    cv2.imshow('mask', mask_bitwise)

    k = cv2.waitKey(1) & 0xFF
    if k in (27, 113):
        cv2.destroyAllWindows()
        break
