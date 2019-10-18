import logging
import time
from abc import abstractmethod
from threading import Thread
from typing import Tuple


class CameraHandler(Thread):

    def __init__(self, exposure=0, contrast=7):
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
        threading, otherwise should just be called as super().
        :return: None
        """
        super().start()

    @abstractmethod
    def create_camera(self):
        self.camera = None

    @abstractmethod
    def set_exposure(self,  exposure: int):
        self.camera.exposure = exposure

    @abstractmethod
    def set_contrast(self, contrast: int):
        self.camera.contrast = contrast

    @abstractmethod
    def set_resolution(self, resolution: Tuple[int, int]):
        self.camera.resolution = resolution

    @abstractmethod
    def set_fps(self, framerate):
        self.camera.framerate = framerate

    @abstractmethod
    def get_exposure(self):
        return self.camera.exposure

    @abstractmethod
    def get_contrast(self):
        return self.camera.contrast

    @abstractmethod
    def get_resolution(self):
        return self.camera.resolution

    @abstractmethod
    def get_fps(self):
        pass

    @abstractmethod
    def run(self):
        """
        Implementation of "abstract" Thread run method, stores frames in a class variable. Breaks if exit flag is
        raised.
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
        logging.info(data)
