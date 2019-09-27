import argparse
import logging
import sys
import time
from importlib import import_module

import cv2
import tensorflow as tf

import nt_handler
import utils
from cv_camera import CVCamera
from display import Display
from pi_camera import PICamera
from realsense import RealSense
from web import Web

logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO, handlers=[
    logging.FileHandler('vision.log', mode='w'),
    logging.StreamHandler()
])


def get_args():
    """
    Add command line arguments.
    :return: Parsed arguments
    """
    parser = argparse.ArgumentParser()
    # Add web server argument
    parser.add_argument('-no-web', action='store_false', default=True,
                        dest='web',
                        help='Disable web server UI')
    parser.add_argument('-networktables', '-nt', action='store_true', default=False,
                        dest='networktables',
                        help='Initiate network tables')
    # Add local ui argument
    parser.add_argument('-local', action='store_true', default=False,
                        dest='local',
                        help='Launch local UI')
    # Add camera provider argument
    parser.add_argument('-camera', default='cv', help='Camera provider', type=str, choices=['cv', 'pi', 'realsense'])
    # Add camera port argument
    parser.add_argument('-port', default=0, dest='port', help='Camera port', type=int)
    # Add target argument
    parser.add_argument('-target', default='hatch', dest='target', help='Target file', type=str)
    # Add robot argument
    parser.add_argument('-robot', default='genesis', help='robot', type=str, choices=['genesis', 'driving_robot'])
    return parser.parse_args()


class Main:
    def __init__(self):
        self.results = get_args()
        self.name = self.results.target
        # Check if requested target exists
        if not utils.is_target(self.name, neural=True):
            return
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
        self.display = Display(provider=camera_provider)
        if self.results.web:
            self.web = Web(self)
            self.web.start_thread()  # Run web server
        if self.results.networktables:
            self.nt = nt_handler.NT(self.name)
        self.stop = False
        self.session = None

    def change_name(self, name):
        """
        Changes the name and starts a new loop.
        :param name:
        """
        if not utils.is_target(name, neural=True):
            return
        logging.info('Changing target to {}'.format(name))
        self.name = name
        self.stop = True

    def loop(self):
        printed = False
        # Check if requested target exists
        if not utils.is_target(self.name, False, True):
            return
        logging.info('Starting loop with target {}'.format(self.name))
        self.stop = False
        # We dynamically load classes in order to provide a modular base
        target = import_module('neural_targets.{}'.format(self.name)).Target(self)
        self.display.change_exposure(target.exposure)
        # Timer for FPS counter
        timer = time.time()
        avg = 0
        while True:
            frame = self.display.get_frame()
            if frame is None:
                if not printed:
                    logging.warning('Couldn\'t read from camera')
                    printed = True
                continue
            else:
                printed = False
            # Get bounding boxes
            boxes = target.boxes(frame)
            # Draw on frame
            target.draw(frame, boxes)
            angle, distance, bounding_box = target.measurements(frame, boxes)
            # Show FPS
            avg = utils.calculate_fps(frame, time.time(), timer, avg)
            timer = time.time()
            # Web
            self.web.frame = frame
            # Display
            self.display.process_frame(frame, 'image', self.results.local)
            if self.results.networktables:
                if distance:
                    self.nt.set_item('distance', distance)
                if angle:
                    self.nt.set_item('angle', angle)
            if self.stop:
                # If stop signal was sent we call loop again to start with new name
                logging.warning('Restarting...')
                self.loop()
                break
            k = cv2.waitKey(1) & 0xFF  # large wait time to remove freezing
            if k in (27, 113):
                logging.warning('Q pressed, stopping...')
                self.display.release()
                self.session.close()
                break


if __name__ == '__main__':
    Main().loop()
