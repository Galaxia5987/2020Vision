import utils
import hsv.reflector as rf
import cv2, constants
import numpy as np
from targets.target_base import TargetBase
class Target(TargetBase):
    def __init__(self, main):
        super().__init__(self, main)
        old_res = self.main.display.camera.resolution


    def mask(self, frame):
        #start mask
        mask = utils.hsv_mask(frame,rf)
        mask = cv2.threshold(mask, 127, 225, 0)[1]
        mask = cv2.erode(mask, kernel=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8), iterations=1)
        mask = cv2.dilate(mask, kernel=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8), iterations=1)

        return mask

    def find_reflector(self,contours):
        correct_contours = []
        for con in contours:
            area = cv2.contourArea(con)
            width,height = cv2.boundingRect()[2:3]
            box_area = width*height
            if (0.9 < box_area/area < 1.15 and 8 > len(utils.points(con)) > 3):
                correct_contours.extend()
            return correct_contours

    def draw_contours(self, filtered_contours, original):
        if filtered_contours:
            for cnt in filtered_contours:
                (a, b), radius = cv2.minEnclosingCircle(cnt)
                center = int(a), int(b)
                cv2.circle(original, center, int(radius), (0, 255, 0), 5)

    def measurements(self, frame, contours):
        distances = []
        distance = None
        angle = None
        x = None
        y = None
        if contours and self.main.results.camera == 'realsense':
            for cnt in contours:
                (x, y) = utils.center(cnt)
                distances.append(self.main.display.camera_provider.get_distance(x, y))
            distance = min(distances)
            closest = contours[distances.index(distance)]
            (x, y) = utils.center(closest)
            angle = utils.angle(constants.FOCAL_LENGTHS['realsense'], x, frame)
        elif contours:
            res = (320, 240)
            contours.sort(key=cv2.contourArea)
            target = contours[-1]
            F = constants.FOCAL_LENGTHS[self.main.results.camera]
            distance = ((cv2.contourArea(target) / (res[0] * res[1]) * 100) ** -0.507) * 0.918
            angle = utils.angle(F, x, frame)

            """find resolution ratio"""
            F = 940
            new_res = self.main.display.camera.resolution
            f = F*(self.old_res/new_res)
        if f:
            cv2.putText(frame, str(f), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 1,
                        cv2.LINE_AA)

        return angle, distance, None, None
