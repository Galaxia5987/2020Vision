import logging
import time

import numpy as np

import constants


class RealSense:
    def __init__(self, serial_number: str = None, rotated_vertical: bool = False, rotated_horizontal: bool = False,
                 name: str = 'RealSense'):
        """
        :param serial_number: Serial number of camera, used in multiple camera setups
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
        frames = self.pipeline.wait_for_frames()
        frames = self.align.process(frames)  # Align depth frame to size of depth frame
        depth_frame = frames.get_depth_frame()
        self.depth_frame = depth_frame.as_depth_frame()
        color_frame = frames.get_color_frame()
        color_image = np.asanyarray(color_frame.get_data())
        self.color_frame = color_image
        return color_image

    def start(self):
        """Implementation of Thread run method, stores frames in a class variable."""
        pass

    def release(self):
        """Release the camera and loop."""
        self.exit = True
        self.pipeline.stop()

    def get_resolution(self):
        return 424, 240

    def set_exposure(self, exposure: int):
        """
        Set the exposure to a desired value.
        :param exposure:

        """
        s = self.prof.get_device().query_sensors()[1]
        s.set_option(self.rs_options.enable_auto_exposure, 0)
        s.set_option(self.rs_options.enable_auto_white_balance, 0)
        s.set_option(self.rs_options.exposure, exposure)
        logging.info('Current exposure: {}'.format(s.get_option(self.rs_options.exposure)))

    def get_distance(self, x, y):
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
