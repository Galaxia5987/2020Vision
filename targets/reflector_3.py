import utils
import cv2
import numpy as np
from targets.target_base import TargetBase
import constants
import math

class Target(TargetBase):
    def __init__(self, main):
        super().__init__(main)
        self.exposure = -7.5

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
        if contours:
            for con in contours:
                area = cv2.contourArea(con)
                convex = cv2.convexHull(con)
                convex_area = cv2.contourArea(convex)
                if 1.5 > (convex_area/2)/area > 0.7 or 0.9 < utils.rectangularity(con,"check") < 1.15:
                    extLeft = tuple(con[con[:, :, 0].argmin()][0])
                    extTop = tuple(con[con[:, :, 1].argmin()][0])
                    extBot = tuple(con[con[:, :, 1].argmax()][0])
                    distanceTop = (extTop[0]-extLeft[0])/(extTop[1]-extLeft[1])
                    distanceBot = (extBot[0]-extLeft[0])/(extBot[0]-extLeft[0])
                    print(correct_contours)
                    if distanceBot < distanceTop:
                        correct_contours.append(con)
        return correct_contours

    @staticmethod
    def draw_contours(filtered_contours, original):
        if filtered_contours:
            cv2.drawContours(original,filtered_contours, -1, (200,70,100), 3)

    def measurements(self, frame, contours):
        distances = []
        distance = None
        angle = None
        x = None
        y = None
        for cnt in contours:
            (x, y) = utils.center(cnt)
            if contours and self.main.results.camera == 'realsense':

                distances.append(self.main.display.camera_provider.get_distance(x, y))
                distance = min(distances)
                closest = contours[distances.index(distance)]
                (x, y) = utils.center(closest)
                angle = utils.angle(constants.FOCAL_LENGTHS['realsense'], x, frame)
            elif contours:
                (x, y) = utils.center(cnt)
                height = cv2.boundingRect(cnt)[3]
                F = constants.FOCAL_LENGTHS[self.main.results.camera]
                distance = utils.distance(F,0.22,height)
                angle = utils.angle(F, x, frame)

        if distance:
            cv2.putText(frame, str(distance), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 1,
                        cv2.LINE_AA)

        return angle, distance, None, None