import cv2

import utils
import constants
from targets.target_base import TargetBase


class Target(TargetBase):
    """The cargo in the 2019."""
    def __init__(self, main):
        super().__init__(main)
        self.exposure = 25

    def create_mask(self, frame, hsv):
        mask = utils.hsv_mask(frame, hsv)
        mask = utils.binary_thresh(mask, 127)

        edge = self.edge_detection(frame, mask)

        mask = utils.bitwise_not(mask, edge)
        mask = utils.erode(mask, self.kernel_big)
        mask = utils.closing_morphology(mask, kernel_d=self.kernel_small, kernel_e=self.kernel_small, itr=3)

        return mask

    def edge_detection(self, frame, mask):
        edge = utils.canny_edge_detection(frame)
        edge = utils.binary_thresh(edge, 127)
        edge = utils.array8(edge)
        edge = utils.dilate(edge, self.kernel_big)
        edge = utils.opening_morphology(edge, kernel_e=self.kernel_small, kernel_d=self.kernel_small, itr=3)
        edge = utils.bitwise_and(edge, mask)

        return edge

    @staticmethod
    def filter_contours(contours, hierarchy):
        correct_contours = []
        all_children = []
        if contours:
            for cnt in contours:
                if cv2.contourArea(cnt) < 500:
                    continue
                if utils.solidity(cnt) > 0.8:
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
                (a, b), radius = cv2.minEnclosingCircle(cnt)
                center = int(a), int(b)
                cv2.circle(original, center, int(radius), (0, 255, 0), 5)

    def measurements(self, frame, contours):
        data = []
        distances = []
        data[1] = None #distance
        data[0] = None #angle
        if contours and self.main.results.camera == 'realsense':
            for cnt in contours:
                (x, y) = utils.center(cnt)
                distances.append(self.main.display.camera_provider.get_distance(x, y))
            data[0] = min(distances)
            closest = contours[distances.index(data[1])]
            (x, y) = utils.center(closest)
            data[1] = utils.angle(constants.FOCAL_LENGTHS['realsense'], x, frame)
            if data[1]:
                cv2.putText(frame, str(int(data[1] * 100)), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 1,
                            cv2.LINE_AA)
        return data
