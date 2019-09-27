import argparse
import logging
import math
import sys
import time
from importlib import import_module

import cv2
import imutils

import constants
import nt_handler
import utils
from cv_camera import CVCamera
from display import Display
from file_hsv import FileHSV
from pi_camera import PICamera
from realsense import RealSense
from trackbars import Trackbars
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
    parser.add_argument('-camera', default='realsense', help='Camera provider', type=str,
                        choices=['cv', 'pi', 'realsense'])
    # Add camera port argument
    parser.add_argument('-port', default=0, dest='port', help='Camera port', type=int)
    # Add robot argument
    parser.add_argument('-robot', default='genesis', help='robot', type=str, choices=['genesis', 'driving_robot'])
    return parser.parse_args()


class Main:
    def __init__(self):
        self.name = 'hatch'  # Neural target
        self.results = get_args()
        self.realsense = RealSense(constants.REALSENSE_SN)
        self.camera_provider = self.realsense
        time.sleep(1)  # Let realsense run a bit before setting exposure
        self.realsense.set_exposure(10)
        if self.results.camera == 'pi':
            camera_provider = PICamera()
            logging.info('Using PI Camera provider')
        elif self.results.camera == 'realsense':
            logging.info('Using RealSense camera provider')
            camera_provider = self.realsense
        elif self.results.camera == 'cv':
            camera_provider = CVCamera(self.results.port)
        else:
            logging.error('Invalid camera provider, this shouldn\'t happen')
            sys.exit(1)

        self.display = Display(provider=camera_provider)
        if self.results.local:
            # self.tape_hsv_handler = Trackbars('2019_tape')
            self.cargo_hsv_handler = Trackbars('cargo_simple')
            self.tape_hsv_handler = FileHSV('2019_tape')
        else:
            self.tape_hsv_handler = FileHSV('2019_tape')
            self.cargo_hsv_handler = FileHSV('cargo_simple')
        if self.results.web:
            self.web = Web(self)
            self.web.start_thread()  # Run web server
        if self.results.networktables:
            self.nt = nt_handler.NT('2019')
        self.stop = False

    def loop(self):
        printed = False
        logging.info('Starting loop')
        self.stop = False
        # Load targets
        logging.info('Loading targets......')
        tape = import_module('targets.2019_tape').Target(self)
        cargo_simple = import_module('targets.cargo_simple').Target(self)
        # hatch = import_module('neural_targets.hatch').Target(self)
        logging.info('Loading targets complete')

        # Timer for FPS counter
        timer = time.time()
        avg = 0
        while True:
            frame = self.realsense.frame

            if frame is None:
                if not printed:
                    logging.warning('Couldn\'t read from camera')
                    printed = True
                continue
            else:
                printed = False

            # Separate frames for display purposes
            original = frame.copy()
            contour_image = frame.copy()

            # ---- Classic detection

            mask = tape.create_mask(frame, self.tape_hsv_handler.get_hsv())
            contours, hierarchy = tape.find_contours(mask)
            filtered_contours = tape.filter_contours(contours, hierarchy)
            # Draw contours
            tape.draw_contours(filtered_contours, contour_image)
            rocket = self.results.networktables and self.nt.get_item('target_type', 'rocket') == 'rocket'
            rocket_hatch = rocket and self.nt.get_item('game_piece', 'hatch') == 'hatch'
            rocket_cargo = rocket and self.nt.get_item('game_piece', 'hatch') == 'cargo'

            # Find distance and angle
            tape_angle, tape_distance, tape_field_angle, data = tape.measurements(contour_image, filtered_contours,
                                                                                  rocket_hatch, rocket_cargo, False)
            pair = data[0] if data else None

            hatch_angle = None
            hatch_distance = None

            # Cargo ship
            neural = self.results.networktables and self.nt.get_item('target_type', 'rocket') in ['cargoship',
                                                                                                  'floor_hatch']
            if neural:
                # ---- Neural detection

                boxes = hatch.boxes(original)

                # Draw on frame
                hatch.draw(contour_image, boxes)

                target_type = self.nt.get_item('target_type', 'rocket')

                pairs = data[1] if data else None

                if target_type == 'cargoship':

                    hatch_pairs, non_hatch_pairs = self.match_hatches(pairs, boxes, frame, contour_image)

                    if self.nt.get_item('game_piece', 'hatch') == 'hatch':
                        chosen_pair = tape.get_closest_pair(non_hatch_pairs)
                    else:

                        non_cargo_pairs = self.match_cargos(cargo_simple, pairs, frame, boxes)

                        chosen_pair = tape.get_closest_pair(non_cargo_pairs)

                    tape_angle, tape_distance, tape_field_angle = tape.calculate(chosen_pair, original)
                    if chosen_pair:
                        # Draw chosen pair on screen
                        x, y, w, h = cv2.boundingRect(chosen_pair[0])
                        x2, y2, w2, h2 = cv2.boundingRect(chosen_pair[1])
                        cv2.rectangle(contour_image, (x + w, y + h), (x2, y2), (123, 92, 249), 3)

                else:
                    hatch_angle, hatch_distance, bounding_box = hatch.measurements(frame, boxes)
            else:
                if pair:
                    tape_angle, tape_distance, tape_field_angle = tape.calculate(pair, original)

            cargo_angle = None
            cargo_distance = None

            if self.results.networktables and self.nt.get_item('target_type', 'sandstorm') == 'floor_cargo':
                cargo_angle, cargo_distance, field_angle, additional_data = self.simple_cargo_detection(cargo_simple,
                                                                                                        frame,
                                                                                                        contour_image)

            # Show FPS
            avg = utils.calculate_fps(contour_image, time.time(), timer, avg)
            timer = time.time()
            self.web.frame = contour_image
            # Display
            self.display.process_frame(contour_image, 'Image', self.results.local)
            self.display.process_frame(utils.bitwise_and(original, mask), 'Reflector mask', self.results.local)

            # Compensation for cameras not being in the center
            if tape_distance and tape_angle is not None:
                tape_distance, tape_angle = self.compensate_center(tape_distance, tape_angle)

            # Set values in network tables
            if self.results.networktables:
                # Tape
                self.nt.set_item('tape_seen', tape_angle is not None)
                if tape_angle is not None:
                    self.nt.set_item('tape_angle', tape_angle)
                    if tape_distance:
                        self.nt.set_item('tape_distance', tape_distance)
                    if tape_field_angle is not None:
                        self.nt.set_item('tape_field_angle', tape_field_angle)
                # Hatch
                self.nt.set_item('hatch_seen', bool(hatch_distance))
                if hatch_distance:
                    self.nt.set_item('hatch_angle', hatch_angle)
                    self.nt.set_item('hatch_distance', hatch_distance)
                # Cargo
                self.nt.set_item('cargo_seen', bool(cargo_distance))
                if cargo_distance:
                    self.nt.set_item('cargo_angle', cargo_angle)
                    self.nt.set_item('cargo_distance', cargo_distance)
            if self.stop:
                # If stop signal was sent we call loop again to start with new name
                logging.warning('Restarting...')
                self.loop()
                break
            k = cv2.waitKey(1) & 0xFF  # large wait time to remove freezing
            if k in (27, 113):
                logging.warning('Q pressed, stopping...')
                self.display.release()
                break

    def compensate_center(self, distance, center_angle):
        """
        Compensate for cameras being offset on the genesis profile.
        :param distance: Original distance
        :param center_angle: Center angle before compensation
        :return: Distance and angle after compensation
        """
        try:
            angle_adjustment = 1
            if self.display.camera_provider.name == 'hatch':
                angle_adjustment = -1

            compensated_distance = math.sqrt(
                distance ** 2 + constants.CAMERA_DISTANCE_FROM_CENTER ** 2 + 2 * distance * angle_adjustment * constants.CAMERA_DISTANCE_FROM_CENTER * math.sin(
                    math.radians(center_angle)))

            compensated_angle = math.asin(
                (distance * math.sin(
                    math.radians(center_angle)) + constants.CAMERA_DISTANCE_FROM_CENTER * angle_adjustment) / (
                    compensated_distance))

            return compensated_distance, math.degrees(compensated_angle)
        except ValueError:
            logging.warning('ValueError during compensation')
            return distance, center_angle

    def simple_cargo_detection(self, cargo_simple, frame, contour_image):
        """
        Runs simple cargo detection.
        :param cargo_simple: Cargo simple target
        :param frame: Frame to run detection on
        :param contour_image: Contour image to draw on
        :return: Measurements from detection
        """
        cargo_mask = cargo_simple.create_mask(frame, self.cargo_hsv_handler.get_hsv())
        contours, hierarchy = cargo_simple.find_contours(cargo_mask)
        filtered_contours = cargo_simple.filter_contours(contours, hierarchy)
        # Draw contours
        cargo_simple.draw_contours(filtered_contours, contour_image)
        return cargo_simple.measurements(contour_image,
                                         filtered_contours)

    @staticmethod
    def match_hatches(pairs, boxes, frame, contour_image):
        """
        Match hatches to hatch pairs and non hatch pairs.
        :param pairs: Reflection tape pairs
        :param boxes: Boundign boxes
        :param frame: Original frame
        :param contour_image: Frame to draw on
        """
        hatch_pairs = []
        non_hatch_pairs = []
        if pairs:
            for pair in pairs:
                if pair:
                    has_hatch = False
                    for box in boxes:
                        bounding_box = box['box']
                        hatch_x1, hatch_x2, hatch_y1, hatch_y2 = utils.bounding_box_coords(bounding_box,
                                                                                           frame)
                        middle_hatch_x = (hatch_x1 + hatch_x2) / 2
                        middle_hatch_y = (hatch_y1 - hatch_y2) / 2

                        reflector_x1, reflector_y1, reflector_w1, reflector_h1 = cv2.boundingRect(pair[0])
                        reflector_x2, reflector_y2, reflector_w2, reflector_h2 = cv2.boundingRect(pair[1])
                        reflector_x2 = reflector_x2 + reflector_w2
                        bay_highest_y = max(reflector_y1, reflector_y2)
                        bay_lowest_y = min(reflector_y1 - (3 * reflector_h1),
                                           reflector_y2 - (3 * reflector_h2))

                        if reflector_x2 < middle_hatch_x < reflector_x1 and bay_lowest_y < middle_hatch_y < bay_highest_y:
                            cv2.rectangle(contour_image,
                                          (int(reflector_x2 - reflector_w1), int(reflector_y2)),
                                          (int(hatch_x2), int(hatch_y2)),
                                          (10, 50, 200), 3)
                            has_hatch = True
                    if has_hatch:
                        hatch_pairs.append(pair)
                    else:
                        non_hatch_pairs.append(pair)
        return hatch_pairs, non_hatch_pairs

    def match_cargos(self, cargo_simple, pairs, frame, boxes):
        """
        Matches cargo and non cargo pairs.
        :param cargo_simple: Cargo simple target
        :param frame: Frame
        :param boxes: Hatch bounding boxes
        :return: Non cargo pairs
        """
        non_cargo_pairs = []
        simple_mask = cargo_simple.create_mask(frame, self.cargo_hsv_handler.get_hsv())
        cargo_contours, hierarchy = cargo_simple.find_contours(simple_mask)
        for box in boxes:
            bounding_box = box['box']

            hatch_x1, hatch_x2, hatch_y1, hatch_y2 = utils.bounding_box_coords(bounding_box, frame)

            found = False
            for cargo in cargo_contours:
                if cv2.contourArea(cargo) > 25:
                    cargo_x, cargo_y, cargo_w, cargo_h = cv2.boundingRect(cargo)
                    middle_cargo_x = (cargo_x + (cargo_w / 2))
                    middle_cargo_y = (cargo_y + (cargo_h / 2))
                    if hatch_x1 < middle_cargo_x < hatch_x2 and hatch_y1 < middle_cargo_y < hatch_y2:
                        found = True
            if not found:
                # Find matching pair
                if pairs:
                    for pair in pairs:
                        if not pair:
                            continue
                        middle_hatch_x = (hatch_x1 + hatch_x2) / 2
                        middle_hatch_y = (hatch_y1 - hatch_y2) / 2
                        reflector_x1, reflector_y1, reflector_w1, reflector_h1 = cv2.boundingRect(
                            pair[0])
                        reflector_x2, reflector_y2, reflector_w2, reflector_h2 = cv2.boundingRect(
                            pair[1])
                        reflector_x2 = reflector_x2 + reflector_w2
                        bay_highest_y = max(reflector_y1, reflector_y2)
                        bay_lowest_y = min(reflector_y1 - (3 * reflector_h1),
                                           reflector_y2 - (3 * reflector_h2))

                        if reflector_x2 < middle_hatch_x < reflector_x1 and \
                                bay_lowest_y < middle_hatch_y < bay_highest_y:
                            non_cargo_pairs.append(pair)
                            break
        return non_cargo_pairs


if __name__ == '__main__':
    Main().loop()
