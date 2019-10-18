from camera_handler import CameraHandler


class PICamera(CameraHandler):
    """
    Handler for cameras accessed through PiCamera functions. Receives frames in a thread, and allows changing and reading
    a few camera configurations. Extends the threading.Thread class.

    Attributes
    ----------

    camera : PICamera
    rawCapture : PiRGBArray
        - i'm gonna be real with you chief, i have no idea what this is. probably a recorder
    """
    def __init__(self, exposure=0, contrast=7, framerate=32, resolution=(320, 240)):
        """
        Initialize camera, set resolution, framerate, contrast, and exposure, and initialize frame thread.
        :param exposure: The exposure to set the camera to. Default is 0.
        :param contrast: The contrast to set the camera to. Default is 7.
        :param framerate: The framerate at which the camera is set to record. Default is 32.
        :param resolution: The resolution at which the camera is set to record. Default is 320 by 240 pixels.
        """
        super().__init__(exposure, contrast)
        # Set additional camera parameters not set in super().__init__
        self.set_fps(framerate)
        self.set_resolution(resolution)
        # Create what I can only assume to be an RPI video recorder
        from picamera.array import PiRGBArray
        self.rawCapture = PiRGBArray(self.camera, size=resolution)

    def create_camera(self):
        """
        Import PiCamera inside class to avoid errors, as PiCamera can only be imported on RPI.
        """
        from picamera import PiCamera
        # Initiate camera
        self.camera = PiCamera()

    def run(self):
        """
        Implementation of Thread.run(), stores frames in a class variable. Breaks if exit flag is raised.
        Uses a different method than the default OpenCV one.
        """
        # PiCamera iterator
        for frame in self.camera.capture_continuous(self.rawCapture, format='bgr', use_video_port=True):
            if self.exit:
                break
            self.frame = frame.array
            self.rawCapture.truncate(0)

    def set_exposure(self, exposure: int):
        """
        Set the camera exposure.
        :param exposure: Camera exposure value.
        """
        self.camera.exposure_compensation = exposure
        self.log('New exposure: {}'.format(self.get_exposure()))


if __name__ == "__main__":
    help(PICamera)
