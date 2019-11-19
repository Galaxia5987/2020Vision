from targets.target_base import TargetBase
import utils,cv2
import numpy as np
import constants
class Target(TargetBase):
    def mask(frame,hsv):
        #
        mask = utils.hsv_mask(frame,hsv)
        mask = cv2.threshold(mask, 127, 225, 0)[1]
        mask = cv2.erode(mask, kernel=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8), iterations=1)
        mask = cv2.dilate(mask, kernel=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8), iterations=1)

        return mask


    @staticmethod
    def filter_contours(contours, hierarchy):
        #filters contours of balls

        correct_contours = []

        if contours:
            for cnt in contours:
                circle = cv2.minEnclosingCircle(cnt)[1]
                circle = circle*circle*3.14
                if 0.9 < circle / cv2.contourArea(cnt) < 1.15:
                    correct_contours.append(cnt)

        return correct_contours

    def measurements(self,frame,contours):
        """
        Return the angle and distance from a single target.
        :param frame: The frame, used for angle measurement
        :param cnt: The contour of the target
        """
        if contours:
            focal = constants.FOCAL_LENGTHS['cv']
            cnt = contours[0]
            angle = utils.angle(focal,cv2.minEnclosingCircle(cnt)[0][0], frame)
            (x,y) = cv2.minEnclosingCircle(cnt)[0]
            cv2.putText(frame, str(angle),(int(x), int(y)),cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 1, cv2.LINE_AA)
            if self.main.results.camera == 'realsense':
                distance = self.main.display.camera_provider.get_distance(int(x), int(y))
                cv2.putText(frame, str(distance), (int(x), int(y-1000)), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 255), 1,cv2.LINE_AA)
            else:
                distance = None




            return angle, distance, None, None
        else:
            return None, None, None, None

    @staticmethod
    def draw_contours(filtered_contours, original):
        if not filtered_contours:
            return
        cv2.drawContours(original, filtered_contours, -1, (255, 255, 0), 3)


