import logging
import time
from abc import abstractmethod
from threading import Thread
from typing import Tuple


class CameraHandler(Thread):
    """
    An "upper" class for handling cameras. Includes all methods called from cameras in other classes as abstracts.
    Defaults to the simplest method, sometimes OpenCV and sometimes PICamera. Details on which is which is found in the
    methods themselves.

    Attributes
    ----------
    camera : cv_camera_new.CVCamera or pi_camera_new.PICamera or realsense_new.RealSense or None
        - initially assigned as None, and later created in its own way in each individual camera handler
    exit : bool
        - a flag indicating the run's shut down
    frame
        - the current frame read from self.camera
    """
    def __init__(self, exposure=0, contrast=7):
        """
        Create the camera and set exposure and contrast using handler's own methods. Additional parameters may be set in
        implementations. If the camera does not run on a thread, this entire function can be overwritten, except the
        creation and assignment of the exit flag.
        :param exposure: The exposure to set the camera to. Default is 0.
        :param contrast: The contrast to set the camera to. Default is 7.
        """
        self.camera = None
        self.create_camera()
        self.set_exposure(exposure)
        self.set_contrast(contrast)
        self.exit = False
        self.frame = None
        self.log('Contrast: {} Exposure: {} FPS: {}'.format(self.get_contrast(), self.get_exposure(), self.get_fps()))
        time.sleep(0.1)  # Sleep to let the camera warm up
        super().__init__(daemon=True)  # Initialize thread

    @abstractmethod
    def start(self) -> None:
        """
        Implementation of Thread.start(). May be overwritten into an empty function if the camera does not use
        threading, otherwise should not be implemented.
        :return: None
        """
        super().start()

    @abstractmethod
    def create_camera(self):
        """
        Create the camera to be used for the handler. Must be over-written in any implementation.
        """
        self.camera = None

    @abstractmethod
    def set_exposure(self,  exposure: int):
        """
        PICamera default.
        :param exposure: The exposure to set the camera to.
        """
        self.camera.exposure = exposure

    @abstractmethod
    def set_contrast(self, contrast: int):
        """
        PICamera default.
        :param contrast: The contrast to set the camera to.
        """
        self.camera.contrast = contrast

    @abstractmethod
    def set_resolution(self, resolution: Tuple[int, int]):
        """
        PICamera default.
        :param resolution: The resolution to set the camera to, length x width.
        """
        self.camera.resolution = resolution

    @abstractmethod
    def set_fps(self, framerate):
        """
        PICamera default.
        :param framerate: The framerate to set the camera to.
        """
        self.camera.framerate = framerate

    @abstractmethod
    def get_exposure(self):
        """
        PICamera default.
        :return: The camera's actual exposure.
        """
        return self.camera.exposure

    @abstractmethod
    def get_contrast(self):
        """
        PICamera default.
        :return: The camera's actual contrast.
        """
        return self.camera.contrast

    @abstractmethod
    def get_resolution(self):
        """
        PICamera default.
        :return: The camera's actual resolution.
        """
        return self.camera.resolution

    @abstractmethod
    def get_fps(self):
        """
        PICamera default.
        :return: The camera's actual framerate.
        """
        return self.camera.framerate

    @abstractmethod
    def run(self):
        """
        OpenCV default.
        Implementation of Thread.run(), stores frames in the class variable by reading from camera. Breaks if exit flag
        is raised.
        Must be over-written if camera doesn't use threading, or uses a different algorithm.
        """
        while True:
            if self.exit:
                break
            self.frame = self.camera.read()[1]

    @abstractmethod
    def release(self):
        """
        Raise exit flag to signal the thread to stop.
        """
        self.exit = True

    @staticmethod
    def log(data):
        """
        Display data on console and write to vision.log.
        :param data: Information.
        """
        logging.info(data)
