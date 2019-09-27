import itertools
import math

import numpy as np

import constants
import utils
from neural_targets.neural_target_base import NeuralTargetBase


class Target(NeuralTargetBase):
    """Class representing a Hatch Panel vision target."""

    def measurements(self, frame, boxes):
        if not boxes:
            return None, None, None
        bounding_box = boxes[0]['box']
        x1, y1, x2, y2 = utils.bounding_box_coords(bounding_box, frame)
        center = (x1 + x2) / 2
        angle = utils.angle(constants.FOCAL_LENGTHS['realsense'], center, frame)
        horizontal_distance = None
        if self.main.results.camera == 'realsense':
            distances = []
            for x, y in itertools.product(range(int(x1), int(x2), 5), range(int(y1), int(y2), 5)):
                distances.append(self.main.display.camera_provider.get_distance(x, y))
            distance = np.median(distances)

            try:
                horizontal_distance = math.sqrt((distance ** 2) - (constants.HEIGHT_FROM_CARPET['camera']['genesis']))
            except ValueError:
                pass

        return angle, horizontal_distance, bounding_box
