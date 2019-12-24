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
            if 8 > len(utils.points(con)) > 4 and 0.9 < utils.rectangularity(con,"check") < 1.15 and cv2.contourArea(con) > 100:
                correct_contours.append(con)
        return correct_contours

    @staticmethod
    def draw_contours(filtered_contours, original):
        if filtered_contours:
            cv2.drawContours(original,filtered_contours, -1, (200,70,100), 3)

    @staticmethod
    def measurements(frame, cnt):
        if cnt:
            cnt = cnt[0]
            xframe =frame.shape[1]/2
            yframe = frame.shape[0]
            xtarget, ytarget = utils.center(cnt)

            x = xtarget - xframe
            f = constants.FOCAL_LENGTHS['cv']
            width_target = constants.TARGET_SIZES['reflector']['width']
            x1, x2, x3, y1, y2, y3 = utils.rectangularity(cnt, "return")
            xp = max(math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2), (math.sqrt((x2 - x3) ** 2 + (y2 - y3) ** 2)))
            try:
                distance = (f * width_target) / xp
            except ZeroDivisionError:
                distance = None
            angle = math.atan2(x,f)

            cv2.putText(frame,str(angle*(180/math.pi)),(xtarget,ytarget),cv2.FONT_HERSHEY_SIMPLEX ,1,(255, 0, 0),3)
            cv2.putText(frame, str(distance), (xtarget, ytarget-100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
            cv2.line(frame, (int(xframe), 0), (int(xframe), int(yframe)), (0, 255, 0), 2)
            return angle*(180/math.pi), distance, None, None
        return None, None, None, None

