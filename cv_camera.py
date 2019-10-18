import logging
from threading import Thread

import cv2

import constants


class CVCamera(Thread):
    """
    Handler for cameras accessed through OpenCV functions. Receives frames in a thread, and allows changing and reading
    a few camera configurations. Extends the threading.Thread class.

    Attributes
    ----------

    camera
        - the camera inserted into the port passed in __init__
    exit : bool
        - a flag indicating the run's shut down
    frame
        - the current frame read from self.camera
    """
    def __init__(self, port, exposure=0, contrast=7):
        """
        Initialize camera, set contrast and exposure, and initialize frame thread.
        :param port: The port in which the camera is inserted on the processor. Usually 0.
        :param exposure: The exposure to set the camera to. Default is 0.
        :param contrast: The contrast to set the camera to. Default is 7.
        """
        # Start video capture on desired port
        self.camera = cv2.VideoCapture(port)
        self.camera.set(constants.CAMERA_CONTRAST, contrast)  # TODO: Make self.set_contrast
        self.set_exposure(exposure)
        self.exit = False
        self.frame = None
        logging.info(
            'Contrast: {} Exposure: {} FPS: {}'.format(contrast, exposure, self.camera.get(constants.CAMERA_FPS))
        )
        super().__init__(daemon=True)  # Initialize thread

    def run(self):
        """
        Implementation of "abstract" Thread run method, stores frames in a class variable. Breaks if exit flag is
        raised.
        """
        while True:
            if self.exit:
                break
            self.frame = self.camera.read()[1]

    def release(self):
        """
        Release the camera and loop. Raise exit flag.
        """
        self.exit = True
        self.camera.release()

    def set_exposure(self, exposure: int):
        """
        Set the camera exposure.
        :param exposure: Camera exposure value.
        """
        # TODO: Print new exposure
        self.camera.set(constants.CAMERA_EXPOSURE, exposure)

    def get_resolution(self):
        """
        :return: The resolution of the camera's frame. Derived from constants.
        """
        # TODO: Make dynamic
        return int(self.camera.get(constants.CAMERA_WIDTH)), int(self.camera.get(constants.CAMERA_HEIGHT))


if __name__ == "__main__":
    help(CVCamera)
