import logging
import time

import numpy as np

import constants


class RealSense:
    """
    Handler for Intel RealSense cameras. Uses functions accessed from pyrealsense2.
    RealSense cameras have a user interface installed when plugging in a camera, and it is the preferred method for
    debugging most methods found in this class.

    Attributes
    ----------

    name : str
        - the name of the camera in use
        - default: 'RealSense'
    serial_number : str
        - the serial number of camera, used in multiple camera setups
    pipeline : pyrealsense2.pipeline
        - the pipeline through which frames will be recieved frames from the camera
    align : pyrealsense2.align
        - used for resizing the depth frame
    prof : pyrealsense2.pipeline.start
        - used for accessing camera settings such as exposure

    """
    def __init__(self, serial_number: str = None, rotated_vertical: bool = False, rotated_horizontal: bool = False,
                 name: str = 'RealSense'):
        """
        Import the RealSense library and start the pipeline for the camera. Configure various preferences, such as
        rotation of the camera and frame.

        :param serial_number: Must be filled with the camera's actual serial number, has no default.
        """
        import pyrealsense2 as rs
        config = rs.config()
        self.name = name
        if serial_number:
            config.enable_device(serial_number)

        self.serial_number = serial_number

        config.enable_stream(rs.stream.depth, 480, 270, rs.format.z16, 60)
        config.enable_stream(rs.stream.color, 424, 240, rs.format.bgr8, 60)
        self.pipeline = rs.pipeline()
        self.align = rs.align(rs.stream.color)

        start = time.perf_counter()
        self.prof = self.pipeline.start(config)
        logging.info('[{}] Took {:.3f} seconds to start pipeline'.format(self.name, time.perf_counter() - start))

        self.rs_options = rs.option
        self.exit = False
        self.depth_frame = None
        self.rotated_vertical = rotated_vertical
        self.rotated_horizontal = rotated_horizontal

        self.color_frame = None

    @property
    def frame(self):
        """
        The frame of the camera, treated as a variable, retrieved through an algorithm.
        Receives both the coloured frame and the depth frame from the pipeline and stores them in class variables.
        :return: The coloured frame.
        """
        frames = self.pipeline.wait_for_frames()
        frames = self.align.process(frames)  # Align depth frame to size of depth frame
        depth_frame = frames.get_depth_frame()
        self.depth_frame = depth_frame.as_depth_frame()
        color_frame = frames.get_color_frame()
        color_image = np.asanyarray(color_frame.get_data())
        self.color_frame = color_image
        return color_image

    def start(self):
        """
        Dry implementation of Thread run method, to match those in other cameras.
        """
        pass

    def release(self):
        """
        Release the camera and stop the loop.
        """
        self.exit = True
        self.pipeline.stop()

    @staticmethod
    def get_resolution():
        return 424, 240

    def set_exposure(self, exposure: int):
        """
        Set the exposure to a desired value. May not set the camera to the exact value, so the actual exposure of the
        camera is logged.
        :param exposure: Exposure to set the camera to.
        """
        s = self.prof.get_device().query_sensors()[1]
        s.set_option(self.rs_options.enable_auto_exposure, 0)
        s.set_option(self.rs_options.enable_auto_white_balance, 0)
        s.set_option(self.rs_options.exposure, exposure)
        logging.info('Current exposure: {}'.format(s.get_option(self.rs_options.exposure)))

    def get_distance(self, x, y):
        """
        Matches a coloured pixel to its distance recorded in the depth frame.
        :param x: X coordinate of the pixel.
        :param y: Y coordinate of the pixel.
        :return: The real life distance of the object the pixel.
        """
        if self.rotated_horizontal:
            return self.depth_frame.get_distance(self.get_resolution()[0] - x, self.get_resolution()[1] - y)
        elif self.rotated_vertical:
            if self.serial_number == constants.REALSENSE_CAMERAS[0]['hatch']:
                # (y, 480 - x)
                return self.depth_frame.get_distance(y, self.get_resolution()[1] - x)
            elif self.serial_number == constants.REALSENSE_CAMERAS[0]['cargo']:
                # (y, 480 - x)
                return self.depth_frame.get_distance(y, self.get_resolution()[1] - x)
        return self.depth_frame.get_distance(x, y)


if __name__ == "__main__":
    help(RealSense)
