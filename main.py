import argparse
import logging
import sys
import time
from importlib import import_module

import cv2

import nt_handler
import utils
from cv_camera import CVCamera
from display import Display
from file_hsv import FileHSV
from pi_camera import PICamera
from realsense import RealSense
from trackbars import Trackbars
from web import Web
from logger import Logger

logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO, handlers=[
    logging.FileHandler('vision.log', mode='w'),
    logging.StreamHandler()
])


def get_args():
    """
    Add command line arguments. Listed are the names of the arguments, with '/' differentiating options of syntax, as
    well as the names under which they are stored in the returned variable and their default values.

    Uses: Added in 'Parameters' under 'Edit configurations' in the 'Run' window when running this file, with spaces
    separating each argument and each argument from its value.

    -no-web : bool
        whether the display frame will be streamed
        :name web
        :default True
    -networktables/-nt : bool
        whether the measurements will be sent to the networktables server
        :name networktables
        :default False
    -help_main/-hm : bool
        whether the help() for main will be shown upon launch
        :default False
    -local : bool
        whether the display frame will be shown on current screen
        :name local
        :default False
    -camera : str
        the camera provider used
        :name camera
        :options 'cv', 'pi', 'realsense'
        :default 'cv'
    -port/-p : int
        the port in which the camera is inserted
        :name port
        :default 0
    -target : str
        the name of the target being recognised
        :name target
        :default 'example_target'
    -robot : str
        the robot on which the processor is mounted
        :name robot
        :options 'genesis', 'driving_robot'
        :default 'genesis'
    :return: Parsed arguments, each variable stored as a variable with its key as its name.
    """
    parser = argparse.ArgumentParser()
    # Add web server argument
    parser.add_argument('-no-web', action='store_false', default=True,
                        dest='web',
                        help='Disable web server UI')
    # Add networktables argument
    parser.add_argument('-networktables', '-nt', action='store_true', default=False,
                        dest='networktables',
                        help='Initiate network tables')
    # Add help in main argument
    parser.add_argument('-help-main', '-hm', action='store_true', default=False,
                        dest='help_main',
                        help='Display the main\'s documentation')
    # Add local ui argument
    parser.add_argument('-local', action='store_true', default=False,
                        dest='local',
                        help='Launch local UI')
    # Add camera provider argument
    parser.add_argument('-camera', default='cv', help='Camera provider', type=str, choices=['cv', 'pi', 'realsense'])
    # Add camera port argument
    parser.add_argument('-port', default=0, dest='port', help='Camera port', type=int)
    # Add target argument
    parser.add_argument('-target', default='example_target', dest='target', help='Target file', type=str)
    # Add robot argument
    parser.add_argument('-robot', default='genesis', help='robot', type=str, choices=['genesis', 'driving_robot'])
    return parser.parse_args()


class Main:
    """
    The main class for target recognition, which makes use of all other files in this directory. When recognising a
    target, only this file needs to be run.

    Attributes
    ----------
    results
        the arguments returned from the run configuration parameters
        See: get_args()
    name : str
        - the name of the target, as received from self.results
        - if the target doesn't exist, shuts down the code
        See: is_target(name) in utils.py
    display : Display
        - the display that will be used for the current run
        - created according to camera_provider in __init__
    hsv_handler : Trackbars or FileHSV
        - hsv handler, based on what is requested in self.results
        - if the run is to be displayed locally, the handler will show trackbars for tuning HSV
        - if the run is not to be displayed locally, the handler will just use the corresponding HSV file to self.name
    web : Web
        - streaming handler, if streaming is requested in self.results
    nt : nt_handler.NT
        - networktables handler, if networktbales are requested in self.results
    stop : bool
        - a variable checked at the end of each loop, notifies if a shut down is requested
        See: loop()
    """
    def __init__(self):
        """
        Create all initial handlers based on parameters from get_args.

        camera_provider : CVCamera or PICamera or RealSense
            - the type of camera to be used by self.display
        """
        self.results = get_args()
        self.name = self.results.target
        # Check if requested target exists
        if not utils.is_target(self.name):
            return

        # Set the camera provider
        if self.results.camera == 'pi':
            camera_provider = PICamera()
            logging.info('Using PI Camera provider')
        elif self.results.camera == 'realsense':
            logging.info('Using RealSense camera provider')
            camera_provider = RealSense()
        elif self.results.camera == 'cv':
            camera_provider = CVCamera(self.results.port)
        else:
            logging.error('Invalid camera provider, this shouldn\'t happen')
            sys.exit(1)

        # Create the display
        self.display = Display(provider=camera_provider)
        if self.results.local:
            self.hsv_handler = Trackbars(self.name)
        else:
            self.hsv_handler = FileHSV(self.name)

        # Create the web server
        if self.results.web:
            self.web = Web(self)
            self.web.start_thread()

        # Create the networktables server
        if self.results.networktables:
            self.nt = nt_handler.NT(self.name)

        self.logger = Logger(self)

        self.stop = False

    def change_name(self, name):
        """
        Changes the name of the target.

        Uses: Generally placed in the web handler, where it receives a string from the site. Is called before a new
        loop.
        See: update() in web.py

        :param name: The name of the new target. If it does not exist, the run is shut down.
        """
        if not utils.is_target(name):
            return
        logging.info('Changing target to {}'.format(name))
        self.name = name
        # Update the HSV variables to match the new target
        self.hsv_handler.name = name
        self.hsv_handler.reload()
        # Stop the current loop
        self.stop = True

    def loop(self):
        """
        Recognises the target repeatedly. Utilises all handlers initialised in __init__.

        :return: If the target doesn't exist, the run is shut down.
        """
        printed = False
        # Check if requested target exists
        if not utils.is_target(self.name, False):
            return
        logging.info('Starting loop with target {}'.format(self.name))
        self.stop = False
        # Load the target class from the 'targets' directory
        target = import_module('targets.{}'.format(self.name)).Target(self)
        time.sleep(1)
        # Change camera exposure based on the target
        self.display.change_exposure(target.exposure)
        # Timer for FPS counter
        self.timer = time.time()
        avg = 0
        last_frame = self.display.get_frame()
        while True:
            # Get initial frame
            frame = self.display.get_frame()
            # If the frame could not be read, flag it as unreadable to avoid errors
            if frame is None:
                if not printed:
                    logging.warning('Couldn\'t read from camera')
                    printed = True
                continue
            else:
                self.logger.record_latency()
                printed = False
            # Copy the initial frame for analysis and display, respectively
            original = frame.copy()
            contour_image = frame.copy()
            same_frame = original == last_frame
            if same_frame == False:
                last_frame = original
            # Show FPS
            avg = utils.calculate_fps(contour_image, time.time(), self.timer, avg)
            self.timer = time.time()
            # Create a mask
            mask = target.create_mask(frame, self.hsv_handler.get_hsv())
            # Get all contours
            contours, hierarchy = target.find_contours(mask)
            self.is_potential_target = bool(contours)
            # Filter contours
            filtered_contours = target.filter_contours(contours, hierarchy)
            self.is_target = bool(filtered_contours)
            # Draw contours
            target.draw_contours(filtered_contours, contour_image)
            self.logger.record_contours()
            # Find distance, angle, and other measurements if stated
            angle, distance, field_angle, additional_data = target.measurements(contour_image, filtered_contours)
            if self.results.web:
                # Stream frame
                self.web.frame = contour_image
            # Display frame
            self.display.process_frame(contour_image, 'image', self.results.local)
            # Display mask
            self.display.process_frame(utils.bitwise_and(original, mask), 'mask', self.results.local)
            # Send measurements to networktables, if requested, and if measurements were returned
            if self.results.networktables:
                if distance is not None:
                    self.nt.set_item('distance', distance)
                if angle is not None:
                    self.nt.set_item('angle', angle)
                if field_angle is not None:
                    self.nt.set_item('field_angle', field_angle)
            # TODO: Send additional data
            if self.stop:
                # If stop signal was sent, call loop again to start with new name
                logging.warning('Restarting...')
                self.loop()
                break
            # Stop the code if q is pressed
            k = cv2.waitKey(1) & 0xFF  # Large wait time to remove freezing
            if k in (27, 113):
                logging.warning('Q pressed, stopping...')
                # Release the camera and close all windows
                self.display.release()
                break


if __name__ == '__main__':
    main = Main()
    if main.results.help_main:
        help(main)
    main.loop()
