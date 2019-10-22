import utils
import cv2
import numpy as np
from targets.target_base import TargetBase
import constants
import math

class Target(TargetBase):
    def __init__(self, main):
        super().__init__(main)
        self.exposure = -5

    @staticmethod
    def mask(frame, hsv):
        #start mask
        mask = utils.hsv_mask(frame,hsv)
        mask = cv2.threshold(mask, 127, 225, 0)[1]
        mask = cv2.erode(mask, kernel=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8), iterations=1)
        mask = cv2.dilate(mask, kernel=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8), iterations=1)

        return mask

    @staticmethod
    def filter_contours(contours, hierarchy):
        correct_contours = []
        for con in contours:
            if 8 > len(utils.points(con)) > 4 and 0.9 < utils.rectangularity(con) < 1.15 and cv2.contourArea(con) > 100:
                correct_contours.append(con)
        return correct_contours

    @staticmethod
    def draw_contours(filtered_contours, original):
        if filtered_contours:
            cv2.drawContours(original,filtered_contours, -1, (200,70,100), 3)

    @staticmethod
    def measurements(frame, cnt):
        xframe =frame.shape[1]/2
        xtarget = cv2.minEnclosingCircle(cnt)[0][0]
        xtarget *= -1
        x = xtarget - xframe
        f = constants.FOCAL_LENGTHS['cv']

