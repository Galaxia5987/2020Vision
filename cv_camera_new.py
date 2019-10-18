from camera_handler import CameraHandler

import cv2

import constants


class CVCamera(CameraHandler):
    """
    Handler for cameras accessed through OpenCV functions. Receives frames in a thread, and allows changing and reading
    a few camera configurations. Extends the camera_handler.CameraHandler class, which extends the threading.Thread
    class.

    Attributes
    ----------

    port : int
    camera : cv2.VideoCapture
    """
    def __init__(self, port: int, exposure=0, contrast=7):
        """
        Initialize camera, set contrast and exposure, and initialize frame thread.
        :param port: The port in which the camera is inserted on the processor. Usually 0.
        :param exposure: The exposure to set the camera to. Default is 0.
        :param contrast: The contrast to set the camera to. Default is 7.
        """
        self.port = port
        super().__init__(exposure, contrast)

    def create_camera(self):
        """
        Start the camera on the desired port.
        """
        self.camera = cv2.VideoCapture(self.port)

    def release(self):
        """
        Release the camera and allow it to be used again. Raise exit flag to signal the thread to stop.
        """
        super()
        self.camera.release()

    def set_exposure(self, exposure: int):
        """
        Set the camera exposure. May not always set exact value, prints the actual value after setting.
        :param exposure: Exposure value to set.
        """
        self.camera.set(constants.CAMERA_EXPOSURE, exposure)
        self.log(self.get_exposure())

    def set_contrast(self, contrast: int):
        """
        Set the camera contrast. May not always set exact value, prints the actual value after setting.
        :param contrast: Contrast value to set.
        """
        self.camera.set(constants.CAMERA_CONTRAST, contrast)
        self.log(self.get_contrast())

    def get_exposure(self):
        return self.camera.get(constants.CAMERA_EXPOSURE)

    def get_contrast(self):
        return self.camera.get(constants.CAMERA_CONTRAST)

    def get_fps(self):
        return self.camera.get(constants.CAMERA_FPS)

    def get_resolution(self):
        """
        :return: The resolution of the camera's frame. Derived from constants.
        """
        # TODO: Make dynamic
        return int(self.camera.get(constants.CAMERA_WIDTH)), int(self.camera.get(constants.CAMERA_HEIGHT))


if __name__ == "__main__":
    help(CVCamera)
