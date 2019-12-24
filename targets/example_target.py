import cv2
import utils
import constants

from targets.target_base import TargetBase


class Target(TargetBase):
    """An example target."""

    @staticmethod
    def filter_contours(contours, hierarchy):
        correct_contours = []

        if contours is not None:
            for cnt in contours:
                if 1000 < cv2.contourArea(cnt) < 10000:
                    correct_contours.append(cnt)

        return correct_contours

    @staticmethod
    def draw_contours(filtered_contours, original):
        if not filtered_contours:
            return
        cv2.drawContours(original, filtered_contours, -1, (255, 255, 0), 3)

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
        return distance, angle, None, None
