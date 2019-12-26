import logging
import time
from threading import Thread


class PICamera(Thread):
    """
    Handler for cameras accessed through PiCamera functions. Receives frames in a thread, and allows changing and reading
    a few camera configurations. Extends the threading.Thread class.

    Attributes
    ----------

    camera : PICamera
        - the camera used for receiving frames
    rawCapture : PiRGBArray
        - i'm gonna be real with you chief, i have no idea what this is.
    exit : bool
        - a flag indicating the run's shut down
    frame
        - the current frame read from self.camera
    """
    def __init__(self, exposure=0, contrast=7, framerate=32, resolution=(320, 240)):
        """
        Initialize camera, set resolution, framerate, contrast, and exposure, and initialize frame thread.
        :param exposure: The exposure to set the camera to. Default is 0.
        :param contrast: The contrast to set the camera to. Default is 7.
        :param framerate: The framerate at which the camera is set to record. Default is 32.
        :param resolution: The resolution at which the camera is set to record. Default is 320 by 240 pixels.
        """
        # Hacky fix picamera only being able to be installed on a raspberry pi
        from picamera import PiCamera
        from picamera.array import PiRGBArray
        # Initiate camera
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.camera.exposure_compensation = exposure
        self.camera.contrast = contrast
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.exit = False
        self.frame = None
        logging.info('Contrast: {} Exposure: {} FPS: {}'.format(contrast, exposure, framerate))
        time.sleep(0.1)  # Sleep to let the camera warm up
        super().__init__(daemon=True)  # Initialize thread

    def run(self):
        """
        Implementation of "abstract" Thread run method, stores frames in a class variable. Breaks if exit flag is
        raised.
        """
        # picamera iterator
        for frame in self.camera.capture_continuous(self.rawCapture, format='bgr', use_video_port=True):
            if self.exit:
                break
            self.frame = frame.array
            self.rawCapture.truncate(0)

    def release(self):
        """
        Release the camera and loop. Raise exit flag.
        """
        self.exit = True

    def set_exposure(self, exposure: int):
        """
        Set the camera exposure.
        :param exposure: Camera exposure value.
        """
        # TODO: Print new exposure
        self.camera.exposure_compensation = exposure

    def get_resolution(self):
        """
        :return: The resolution of the camera's frame.
        """
        return self.camera.resolution


if __name__ == "__main__":
    help(PICamera)
