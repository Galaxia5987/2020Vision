import cv2
import numpy as np,math
import utils,constants

from targets.target_base import TargetBase


class Target(TargetBase):
    """A green square"""

    def __init__(self, main):
        super().__init__(main)
        self.exposure = -8

    def create_mask(self, frame, hsv):
        mask = utils.hsv_mask(frame, hsv)
        mask = utils.binary_thresh(mask, 127)
        mask = utils.erode(mask, self.kernel_big)
        mask = utils.closing_morphology(mask, kernel_d=self.kernel_small, kernel_e=self.kernel_small, itr=3)

        return mask

    @staticmethod
    def filter_contours(contours, hierarchy):
        correct_contours = []
        all_children = []
        if contours:
            for cnt in contours:
                width, height = cv2.boundingRect(cnt)[2:4]
                rectArea = width*height
                try:
                    rectArea_on_cntArea = abs(rectArea/cv2.contourArea(cnt))
                except ZeroDivisionError:
                    rectArea_on_cntArea = -2
                if 1.5>rectArea_on_cntArea>0.6:
                    if rectArea > 1000:
                        all_children.extend(utils.get_children(cnt, contours, hierarchy))
                        correct_contours.append(cnt)

                for cnt in all_children:
                    try:
                        correct_contours.remove(cnt)
                    except ValueError:
                        continue
        return correct_contours


    @staticmethod
    def draw_contours(filtered_contours, original):
        if filtered_contours:
            for cnt in filtered_contours:
                rect = cv2.minAreaRect(cnt)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                cv2.drawContours(original, [box], 0, (0, 0, 255), 2)


    def measurements(self, frame, contours):
        distances = []
        distance = None
        angle = None
        if contours and self.main.results.camera == 'realsense':
            for cnt in contours:
                (x, y) = utils.center(cnt)
                distances.append(self.main.display.camera_provider.get_distance(x, y))
            distance = min(distances)
            closest = contours[distances.index(distance)]
            (x, y) = utils.center(closest)
            angle = utils.angle(constants.FOCAL_LENGTHS['realsense'], x, frame)
            if distance:
                cv2.putText(frame, str(int(distance * 100)), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 1,
                            cv2.LINE_AA)

        elif contours:
            for cnt in contours:
                (x, y) = utils.center(cnt)
                f = constants.FOCAL_LENGTHS[self.main.results.camera]

                width, height = cv2.boundingRect(cnt)[2:4]
                distances.append(utils.distance(f, constants.GAME_PIECE_SIZES['square']['segment'],
                                              width))
                angle = utils.angle(f, x, frame)
            distance = distances[0]
        if distance:
            cv2.putText(frame, str(int(distance*100))+" cm", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 2, (225, 0, 0), 1,
                        cv2.LINE_AA)

        return distance, angle, None, None



