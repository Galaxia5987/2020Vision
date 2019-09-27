from abc import ABC, abstractmethod
from typing import Tuple, Optional

import cv2
import tensorflow as tf

import utils


class NeuralTargetBase(ABC):
    """An abstract class representing a base neural target."""

    def __init__(self, main):
        self.exposure = 250
        self.main = main
        self.graph = utils.load_tf_graph(self.main.name, tf)
        self.num_detections = self.graph.get_tensor_by_name('num_detections:0')
        self.detection_scores = self.graph.get_tensor_by_name('detection_scores:0')
        self.detection_boxes = self.graph.get_tensor_by_name('detection_boxes:0')
        self.detection_classes = self.graph.get_tensor_by_name('detection_classes:0')

        # Avoid memory errors
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True

        self.main.session = tf.Session(graph=self.graph, config=config)

    def boxes(self, image):
        """
        :param image: Image to run network on
        :return:
        """
        inp = cv2.resize(image, (300, 300))
        inp = cv2.cvtColor(inp, cv2.COLOR_BGR2RGB)
        # Run the model
        out = self.main.session.run([self.num_detections,
                                     self.detection_scores,
                                     self.detection_boxes,
                                     self.detection_classes
                                     ],
                                    feed_dict={'image_tensor:0': inp.reshape(1, inp.shape[0], inp.shape[1], 3)})
        boxes = []
        num_detections = int(out[0][0])
        for i in range(num_detections):
            class_id = int(out[3][0][i])
            score = float(out[1][0][i])
            bounding_box = [float(v) for v in out[2][0][i]]
            if score > 0.7:
                boxes.append({"class": class_id, "score": score, "box": bounding_box})
        return boxes

    @abstractmethod
    def measurements(self, image, boxes) -> Tuple[Optional[float], Optional[float], Optional[list]]:
        """
        Return the angle and distance from a single target.
        :param image: Frame to measure from
        :param boxes: Bounding boxes of detected objects
        """
        return None, None, None

    @staticmethod
    def draw(image, boxes):
        """
        Visualize detection by drawing on the frame.
        :param image: Frame to draw on
        :param boxes: Bounding boxes of detected objects
        """
        for box in boxes:
            bounding_box = box['box']
            x1, x2, y1, y2 = utils.bounding_box_coords(bounding_box, image)
            cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (125, 255, 51), thickness=2)
