import math

import cv2
import numpy as np

import constants
import utils
from targets.target_base import TargetBase


class Target(TargetBase):
    """The 2019 Slanted light reflection tape."""

    def __init__(self, main):
        super().__init__(main)
        self.exposure = 10

    def measurements(self, original, contours, rocket_hatch: bool = False, rocket_cargo: bool = False,
                     calculate: bool = True):
        pairs = self.get_pairs(contours)
        if not pairs:
            return None, None, None, None

        # if rocket_hatch:
        #     pair = self.get_lowest_pair(pairs)
        # elif rocket_cargo:
        #     pair = self.get_highest_pair(pairs)
        # else:
        #     pair = self.get_right_pair(pairs)
        pair = self.get_center_pair(pairs)

        angle = None
        horizontal_distance = None
        field_angle = None

        if calculate:
            angle, horizontal_distance, field_angle = self.calculate(pair, original)

        x, y, w, h = cv2.boundingRect(pair[0])
        x2, y2, w2, h2 = cv2.boundingRect(pair[1])

        # Put measurements on image
        utils.put_number(angle, x + w, y + h, original)
        if horizontal_distance is not None:
            utils.put_number(horizontal_distance * 100, x2, y2, original)
        utils.put_number(field_angle, x, y, original)
        return angle, horizontal_distance, field_angle, [pair, pairs]

    def calculate(self, pair, original):
        if pair is None: return None, None, None
        x, y, w, h = cv2.boundingRect(pair[0])
        x2, y2, w2, h2 = cv2.boundingRect(pair[1])
        bounding_box_center = math.sqrt(x ** 2 + (x2 + w2) ** 2) / 2
        angle = utils.angle(constants.FOCAL_LENGTHS[self.main.results.camera], int(bounding_box_center), original)

        horizontal_distance = None
        field_angle = None
        if self.main.results.camera == 'realsense':
            distances = []
            median_distances = []
            for tape in pair:
                for point in tape:
                    distances.append(self.main.display.camera_provider.get_distance(point[0][0], point[0][1]))
                median_distances.append(np.median(distances))
                distances = []

            rs_distance1 = median_distances[0]
            rs_distance2 = median_distances[1]
            if rs_distance1 and rs_distance2:
                rect1 = cv2.minAreaRect(pair[0])
                rect2 = cv2.minAreaRect(pair[1])
                points1 = cv2.boxPoints(rect1)
                points2 = cv2.boxPoints(rect2)
                point1 = min(points1, key=lambda x: x[1])
                point2 = min(points2, key=lambda x: x[1])
                rs_distance = (rs_distance1 + rs_distance2) / 2
                pixel_width = utils.pixel_width(constants.FOCAL_LENGTHS['realsense'],
                                                constants.TARGET_SIZES['2019']['outer_distance_between_tapes'],
                                                rs_distance)
                real_pixel_width = point1[0] - point2[0]
                try:
                    field_angle = math.degrees(math.acos(real_pixel_width / pixel_width))
                except ValueError:
                    field_angle = 0
                if rect1[1][1] < rect2[1][0]:
                    field_angle *= -1

                owned_game_piece = self.main.nt.get_item('game_piece',
                                                         'cargo') if self.main.results.networktables else 'cargo'
                robot = self.main.results.robot
                if owned_game_piece and robot:
                    try:
                        horizontal_distance = math.sqrt(
                            (rs_distance ** 2) -
                            ((constants.HEIGHT_FROM_CARPET['camera'][robot] -
                              constants.HEIGHT_FROM_CARPET['2019']['reflectors'][owned_game_piece]) ** 2)
                        )
                    except ValueError:
                        pass
                else:
                    horizontal_distance = rs_distance

        return angle, horizontal_distance, field_angle

    def get_distance(self, pair):
        rs_distance1 = self.main.display.camera_provider.get_distance(pair[0][0][0][0], pair[0][0][0][1])
        rs_distance2 = self.main.display.camera_provider.get_distance(pair[1][0][0][0], pair[1][0][0][1])
        return (rs_distance1 + rs_distance2) / 2

    def get_closest_pair(self, pairs: list):
        """
        :param pairs: List of pairs
        :return: Closest pair using distance.
        """
        if not pairs:
            return None
        return min(pairs, key=self.get_distance)

    def get_lowest_pair(self, pairs: list):
        """
        :param pairs: List of pairs
        :return: Lowest pair using bounding rect y
        """
        if not pairs:
            return None
        return max(pairs, key=lambda c: cv2.boundingRect(c[0])[1])

    def get_highest_pair(self, pairs: list):
        """
        :param pairs: List of pairs
        :return: Highest pair using bounding rect y
        """
        if not pairs:
            return None
        return min(pairs, key=lambda c: cv2.boundingRect(c[0])[1])

    def get_right_pair(self, pairs: list):
        """
        :param pairs: List of pair
        :return: Pair with the highest x
        """
        if not pairs:
            return None
        return max(pairs, key=lambda c: cv2.boundingRect(c[0])[0])

    def get_center_pair(self, pairs: list):
        """
        :param pairs: List of pairs
        :return: Most centered pair
        """
        if not pairs:
            return None

        def get_mid_x(pair):
            """
            :param pair: Reflector pair
            :return: Center x
            """
            return (cv2.boundingRect(pair[0])[0] + cv2.boundingRect(pair[1])[0]) / 2

        return min(pairs, key=lambda p: abs((self.main.display.camera_provider.get_resolution()[0] / 2) - get_mid_x(p)))

    @staticmethod
    def is_right_curvature(cnt):
        rect = cv2.minAreaRect(cnt)
        points = cv2.boxPoints(rect)

        point1 = sorted(points, key=lambda x: x[1])[-2]
        point2 = max(points, key=lambda x: x[1])

        a = (point1[1] - point2[1]) / (point1[0] - point2[0])
        return 0.2 < abs(a) <= 1

    def _is_correct(self, cnt):
        if cv2.contourArea(cnt) < 20:
            return False
        solidity = utils.solidity(cnt)
        approx = utils.approx_poly(cnt)
        return approx > 2 and 0.7 < solidity < 1 and self.is_right_curvature(cnt)

    def filter_contours(self, contours, hierarchy):
        return [cnt for cnt in contours if self._is_correct(cnt)]

    def get_pairs(self, filtered_contours):
        sorted_contours = sorted(filtered_contours, key=lambda cnt: cv2.boundingRect(cnt)[0])
        already_paired = []
        pairs = []
        for last_cnt, cnt in zip(sorted_contours, sorted_contours[1:]):
            if utils.np_array_in_list(cnt, already_paired) or utils.np_array_in_list(last_cnt, already_paired):
                continue
            rect1 = cv2.minAreaRect(last_cnt)
            rect2 = cv2.minAreaRect(cnt)
            points1 = cv2.boxPoints(rect1)
            points2 = cv2.boxPoints(rect2)

            r1_point1 = sorted(points1, key=lambda x: x[1])[-3]
            r1_point2 = max(points1, key=lambda x: x[1])

            r2_point1 = sorted(points2, key=lambda x: x[1])[-3]
            r2_point2 = max(points2, key=lambda x: x[1])

            a1 = (r1_point1[1] - r1_point2[1]) / (r1_point1[0] - r1_point2[0])
            a2 = (r2_point1[1] - r2_point2[1]) / (r2_point1[0] - r2_point2[0])
            b1 = r1_point1[1] - a1 * r1_point1[0]
            b2 = r1_point2[1] - a2 * r2_point1[0]
            x_meeting = abs((b1 - b2) / (a1 - a2))
            y_meeting = a1 * x_meeting + b1
            # y_meeting = self.main.display.camera_provider.get_resolution()[1] - y_meeting
            if y_meeting < r2_point2[1] and r1_point2[0] < x_meeting < r2_point2[0]:
                already_paired.extend([cnt, last_cnt])
                pairs.append((cnt, last_cnt))

        return pairs

    def draw_contours(self, filtered_contours, original):
        if not filtered_contours:
            return
        for cnt in filtered_contours:
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.drawContours(original, [box], 0, (0, 0, 255), 2)

        pairs = self.get_pairs(filtered_contours)

        for first, second in pairs:
            x, y, w, h = cv2.boundingRect(first)
            x2, y2, w2, h2 = cv2.boundingRect(second)
            cv2.rectangle(original, (x + w, y + h), (x2, y2), (0, 255, 0), 3)
