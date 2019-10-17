import utils
import hsv.reflector as rf
import cv2
import math
import numpy as np
from targets.target_base import TargetBase
class Target(TargetBase):
    def mask(frame):
        #start mask
        mask = utils.hsv_mask(frame,rf)
        mask = cv2.threshold(mask, 127, 225, 0)[1]
        mask = cv2.erode(mask, kernel=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8), iterations=1)
        mask = cv2.dilate(mask, kernel=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8), iterations=1)

        return mask

    def find_reflector(self,contours):
        correct_contours = []
        for con in contours:
            convex = cv2.convexHull(con)
            convex_area = cv2.contourArea(convex)
            box = utils.box(con)
            x1 = box[0][0]
            x2 = box[1][0]
            x3 = box[2][0]
            y1 = box[0][1]
            y2 = box[1][1]
            y3 = box[2][1]
            box_area = math.sqrt((x1-x2)**2+(y1-y2)**2)*(math.sqrt((x2-x3)**2+(y2-y3)**2))
            if (0.9 < box_area/convex_area < 1.15 and 12 > len(utils.points(con)) > 6):
                correct_contours.extend()
            return correct_contours

    def draw_contours(filtered_contours, original):
        if filtered_contours:
            for cnt in filtered_contours:
                (a, b), radius = cv2.minEnclosingCircle(cnt)
                center = int(a), int(b)
                cv2.circle(original, center, int(radius), (0, 255, 0), 5)





