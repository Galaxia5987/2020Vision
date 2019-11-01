import logging
import math
import os
import socket
from typing import Union, List, Tuple

import cv2
import imutils
import numpy as np


def index0(x: iter):
    """
    An index function for sorting based on the first variable. Generally is passed as a parameter itself, and isn't
    called on its own.

    Uses: Sorting lists of coordinates or points.

    :param x: An iterable variable with a length of at least 1.
    :return: The first variable in x.
    """
    return x[0]


def index00(x: iter):
    """
    An index function for sorting based on the first variable in the first variable. Generally is passed as a parameter
    itself, and isn't called on its own.

    Uses: Sorting lists of coordinates or points.

    :param x: An iterable variable, whose first variable is also iterable, both iterables with a length of at least 1.
    :return: The first variable in the first variable of x.
    """
    return x[0][0]


def index1(x: iter):
    """
    An index function for sorting based on the second variable. Generally is passed as a parameter itself, and isn't
    called on its own.

    Uses: Sorting lists of coordinates or points.

    :param x: An iterable variable with a length of at least 2.
    :return: The second variable in x.
    """
    return x[1]


def index01(x: iter):
    """
    An index function for sorting based on the second variable in the first variable. Generally is passed as a parameter
    itself, and isn't called on its own.

    Uses: Sorting lists of coordinates or points.

    :param x: An iterable variable, whose first variable is also iterable, both iterables with a length of at least 2.
    :return: The second variable in the first variable of x.
    """
    return x[0][1]


def aspect_ratio(cnt: np.array) -> float:
    """
    :param cnt: A contour.
    :return: The aspect ratio of the contour, width over height.
    """
    _, _, w, h = cv2.boundingRect(cnt)  # Omitted: x, y as they are not useful for this calculation.
    return w / h


def rotated_aspect_ratio(cnt: np.array) -> float:
    """
    Based on a rotated rectangle instead of a straight one.

    :param cnt: A contour.
    :return: The aspect ratio of the contour, width over height.
    """
    return width(cnt)[0] / height(cnt)[0]


def reversed_rotated_aspect_ratio(cnt: np.array) -> float:
    """
    Based on a rotated rectangle instead of a straight one.

    :param cnt: A contour.
    :return: The aspect ratio of the contour, height over width.
    """
    return height(cnt)[0] / width(cnt)[0]


def height(cnt: np.array) -> Tuple[float, Tuple[int, int], Tuple[int, int]]:
    """
    Find the height of the box bounding the contour.

    Uses: Aspect ratios based on rotated rectangles instead of straight ones.
    See: rotated_aspect_ratio(cnt), reversed_rotated_aspect_ratio(cnt), index0(x), box(cnt)

    :param cnt: A contour.
    :return: The height, top left point, and bottom right point of the bounding rotated rectangle.
    # TODO: Check returned points
    """
    points = []
    for p in box(cnt):  # Receive rotated rectangle points from box(cnt).
        points.append(p)

    points.sort(key=index0)  # Sort based on index0(x).

    x1, y1 = points[0]
    x2, y2 = points[1]

    return math.hypot(abs(x1 - x2), abs(y1 - y2)), (x1, y1), (x2, y2)


def width(cnt) -> Tuple[float, Tuple[int, int], Tuple[int, int]]:
    """
    Find the width of the box bounding the contour.

    Uses: Aspect ratios based on rotated rectangles instead of straight ones.
    See: rotated_aspect_ratio(cnt), reversed_rotated_aspect_ratio(cnt), index1(x), box(cnt)

    :param cnt: A contour.
    :return: The width, top left point, and bottom right point of the bounding rotated rectangle.
    # TODO: Check returned points
    """
    points = []
    for p in box(cnt):  # Receive rotated rectangle points from box(cnt).
        points.append(p)

    points.sort(key=index1)  # Sort based on index1(x).

    x1, y1 = points[0]
    x2, y2 = points[1]

    return math.hypot(abs(x1 - x2), abs(y1 - y2)), (x1, y1), (x2, y2)


def box(cnt: np.array) -> np.array:
    """
    Return a list of the points of the minimum area rectangle bounding the contour.

    :param cnt: A contour.
    :return: List of 4 points in an [x y] format
    """
    rect = cv2.minAreaRect(cnt)
    box = cv2.boxPoints(rect)
    return np.int0(box)


def circle_area(radius: Union[float, int]) -> float:
    """
    :param radius: A circle's radius.
    :return: The circle's area.
    """
    return radius ** 2 * math.pi


def circle_ratio(cnt) -> float:
    """
    :param cnt: A contour.
    :return: Hull area / minimum enclosing circle area.
    """
    _, radius = cv2.minEnclosingCircle(cnt)
    hull = cv2.convexHull(cnt)
    hull_area = cv2.contourArea(hull)
    return hull_area / float(circle_area(radius))


def center(cnt) -> Tuple[int, int]:
    """
    Find the center point of the contour.
    :param cnt: A contour.
    :return: The center of the minimum enclosing circle.
    """
    (x, y), radius = cv2.minEnclosingCircle(cnt)
    return int(x), int(y)


def hsv_mask(frame: np.array, hsv: np.array) -> np.array:
    """
    Generate HSV mask.
    :param frame: Original frame, BGR format.
    :param hsv: Dictionary of HSV values, formatted as in file_hsv.FileHSV.
    :return: Binary mask in HSV range, where pixels within range hold 1's, and those outside hold 0's.
    """
    hsv_colors = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_hsv = np.array([hsv['H'][0], hsv['S'][0], hsv['V'][0]])
    higher_hsv = np.array([hsv['H'][1], hsv['S'][1], hsv['V'][1]])
    mask = cv2.inRange(hsv_colors, lower_hsv, higher_hsv)
    return mask


def morphology(mask: np.array, kernel: np.array) -> np.array:
    """
    Most commonly used morphology method.
    1. Open the mask - erode to remove noise, then dilate the object remaining.
    2. Close the mask - dilate the object to close holes, then erode the rough edges.
    :param mask: Mask to morph.
    :param kernel: The kernel to use for all morphology operations.
    :return: Mask after morphology.
    """
    mask = opening_morphology(mask, kernel, kernel)
    mask = closing_morphology(mask, kernel, kernel)
    return mask


def opening_morphology(mask: np.array, kernel_e: np.array, kernel_d: np.array, itr=1) -> np.array:
    """
    Run opening morphology on given mask.
    1. Erode to remove noise.
    2. Dilate the object remaining.
    :param mask: Mask to open.
    :param kernel_e: Kernel for eroding.
    :param kernel_d: Kernel for dilating
    :param itr: Number of iterations.
    :return: Mask after opening.
    """
    mask = cv2.erode(mask, kernel_e, iterations=itr)
    mask = cv2.dilate(mask, kernel_d, iterations=itr)
    return mask


def closing_morphology(mask: np.array, kernel_d: np.array, kernel_e: np.array, itr=1) -> np.array:
    """
    Runs closing morphology on given mask.
    1. Dilate the object to close holes.
    2. Erode the rough edges.
    :param mask: Mask to close.
    :param kernel_d: Kernel for dilating.
    :param kernel_e: Kernel for eroding.
    :param itr: Number of iterations.
    :return: Mask after closing.
    """
    mask = dilate(mask, kernel_d, itr)
    mask = erode(mask, kernel_e, itr)
    return mask


def dilate(mask: np.array, kernel: np.array, itr=1) -> np.array:
    """
    :param mask: Binary array.
    :param kernel: Binary array, usually rather small. Examples can be found in target base.
    :param itr: Number of iterations.
    :return: Dilated mask.
    """
    return cv2.dilate(mask, kernel, iterations=itr)


def erode(mask: np.array, kernel: np.array, itr=1) -> np.array:
    """
    Run erosion on given mask.
    :param mask: Binary array.
    :param kernel: Binary array, usually rather small.
    :param itr: Number of iterations.
    :return: Eroded mask.
    """
    return cv2.erode(mask, kernel, iterations=itr)


def bitwise_and(frame: np.array, mask: np.array) -> np.array:
    """
    Uses: Better display of masks, edge detection.

    :param frame: A frame.
    :param mask: A mask.
    :return: The part of the frame cut out by the mask. The 0's in the mask draw 0's over the frame.
    """
    frame = frame.copy()
    return cv2.bitwise_and(frame, frame, mask=mask)


def bitwise_not(frame: np.array, mask: np.array) -> np.array:
    """
    Uses: Edge detection.

    :param frame: A frame.
    :param mask: A mask.
    :return: The mask, with the frame removed from it. The frame's 1's draw 0's over the mask's 1's. The 0's don't
    affect each other.
    """
    frame = frame.copy()
    return cv2.bitwise_not(frame, frame, mask=mask)


def bitwise_xor(frame: np.array, mask: np.array) -> np.array:
    """
    :param frame: A frame.
    :param mask: A mask.
    :return: The parts unique to each array. If both have anything other than 0's in any location, they will become 0's.
    The rest stays the same.
    """
    frame = frame.copy()
    return cv2.bitwise_xor(frame, frame, mask=mask)


def binary_thresh(frame: np.array, thresh: int) -> np.array:
    """
    Uses: Masks - HSV and edge detection.

    :param frame: A frame.
    :param thresh: The lower limit of he binary threshold.
    :return: A black and white rendition of frame. Each pixel that has a value (V in HSV) higher than thresh becomes
    white, and the rest become black.
    """
    return cv2.threshold(frame, thresh, 255, cv2.THRESH_BINARY)[1]


def canny_edge_detection(frame: np.array, sigma=33) -> np.array:
    """
    Automatic edge detection from the imutils library.
    :param frame: A frame.
    :param sigma: A magic number. Shouldn't be changed without testing.
    :return: A black and white image of the edges in the frame.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return imutils.auto_canny(gray, sigma=sigma)


def calculate_fps(frame: np.array, current_time: float, last_time: float, avg: float) -> float:
    """
    Calculates current FPS and write on frame.
    :param frame: A frame.
    :param current_time: The current time measured.
    :param last_time: The previous time measured.
    :param avg: Accumulated average.
    :return: Average FPS.
    """
    avg = (avg + (current_time - last_time)) / 2
    cv2.putText(frame, '{} FPS'.format(int(1 / avg)), (0, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    return avg


def solidity(cnt) -> float:
    """
    Uses: Filtering out contours with lots of sharp edges or holes.

    :param cnt: A contour.
    :return: Contour area / convex hull area.
    """
    hull = cv2.convexHull(cnt)
    area = cv2.contourArea(cnt)
    hull_area = cv2.contourArea(hull)
    return float(area) / hull_area


def get_children(contour: np.array, contours: list, hierarchy: iter) -> iter:
    """
    :param contour: A contour.
    :param contours: All external contours.
    :param hierarchy: External contour hierarchy.
    :return: All contours enclosed inside the original contour.
    """
    hierarchy = hierarchy[0]
    index = numpy_index(contour, contours)
    return [child for child, h in zip(contours, hierarchy) if h[3] == index]


def get_ip() -> str:
    """
    :return: Local IP that can be used to access the web UI.
    """
    return socket.gethostbyname(socket.gethostname())


def is_target(name: str, message: bool = True, neural: bool = False) -> bool:
    """
    Checks if a target exists or not if not, print a message.
    :param neural: If the target is neural or not.
    :param message: Boolean if a message should be printed.
    :param name: Name of target.
    :return: Whether target exists.
    """
    folder = 'targets' if not neural else 'neural_targets'
    if not os.path.isfile('{}/{}.py'.format(folder, name)):
        if message:
            logging.error('Target doesn\'t exist')
        return False
    return True


def distance(focal: float, object_width: float, object_width_pixels: float) -> float:
    """
    Uses camera's focal length. 2 distance units over 1 distance unit gives 1 distance unit.
    :param focal: Camera focal length.
    :param object_width: Real object width in meters.
    :param object_width_pixels: Object width in pixels.
    :return: Distance from object in meters.
    """
    return (focal * object_width) / object_width_pixels


def pixel_width(focal: float, object_width: float, distance: float) -> float:
    """
    Calculate pixel width according to known distance. 2 distance units over 1 distance unit gives 1 distance unit.
    :param focal: Camera focal length.
    :param object_width: Real object width in meters.
    :param distance: Known distance from target in meters.
    :return: Object width in pixels.
    """
    return focal * object_width / distance


def array8(arr: iter) -> np.array:
    """
    :param arr An array.
    :return: A uin8 NumPy array from the original array.
    """
    return np.array(arr, dtype=np.uint8)


def approx_hull(cnt: np.array) -> np.array:
    """
    :param cnt: A contour.
    :return: The contour with less points. Magnitude defined by inner variable epsilon.
    """
    hull = cv2.convexHull(cnt)
    epsilon = 0.015 * cv2.arcLength(hull, True)
    return cv2.approxPolyDP(hull, epsilon, True)


def points(cnt: np.array) -> list:
    """
    Approximates a contour to a polygon.
    :param cnt: A contour.
    :return: A list of the the approximated points - the polygons points - in an [x, y] format
    """
    hullpoints = list(cv2.convexHull(approx_hull(cnt), returnPoints=True))
    hullpoints.sort(key=index00)

    points = []

    for p in hullpoints:
        new_p = (p[0][0], p[0][1])
        points.append(new_p)

    return points


def is_circle(cnt: np.array, minimum: Union[float, int]) -> bool:
    """
    :param cnt: A contour.
    :param minimum: Lower ratio threshold.
    :return: Whether the ratio provided from circle_ratio is above the minimum and below 1.
    """
    ratio = circle_ratio(cnt)
    return minimum <= ratio <= 1


def approx_poly(cnt: np.array, ratio: float = 0.07) -> int:
    """
    Another polygon approximation for contours. Does not use convex hulls, unlike approx_hull.
    :param cnt: A contour.
    :param ratio: A magic number that determines the magnitude of approximation. Default is 0.07.
    :return: The amount of points in the approximated polygon.
    """
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, ratio * peri, True)
    return len(approx)


def is_triangle(cnt, ratio=0.07) -> bool:
    """
    Returns if contour resembles a triangle.
    :param cnt: A contour.
    :param ratio: Approximation magnitude. Default is 0.07.
    :return: Whether the approximated polygon has 3 points.
    """
    return approx_poly(cnt, ratio) == 3


def numpy_index(element, arrays: list):
    """
    TODO: what
    :param element: An element.
    :param arrays: The array in which to search for the element.
    :return: Index of the element - a numpy array - in a list.
    """
    return [np.array_equal(element, x) for x in arrays].index(True)


def angle(focal: float, xtarget: int, frame: np.array) -> Union[float, int]:
    """
    Uses: Find angle from target relative to camera axis.

    :param focal: Focal length of desired camera.
    :param xtarget: X coordinate of target's center pixel - usually center of minimum enclosing circle.
    :param frame: The frame in which the target was recognised.
    :return: Angle in degrees.
    """
    xframe = frame.shape[1] / 2
    return math.atan2((xtarget - xframe), focal) * (180 / math.pi)


def np_array_in_list(np_array: np.array, list_arrays: List[np.array]) -> bool:
    """
    :param np_array: A numpy array.
    :param list_arrays: List of NumPy arrays.
    :return: Whether a NumPy array is in a list of NumPy arrays.
    """
    return next((True for elem in list_arrays if np.array_equal(elem, np_array)), False)


def get_center(cnt: np.array) -> (float, float):
    """
    See: cv2.moments()

    :param cnt: A contour.
    :return: X and Y coordinate of the center pixel.
    """
    # Get center of the contour
    moment = cv2.moments(cnt)
    try:
        x = int(moment['m10'] / moment['m00'])
        y = int(moment['m01'] / moment['m00'])
        return x, y
    except ZeroDivisionError:
        return None, None


def load_tf_graph(name: str, tf: __import__):
    """
    Load TensorFlow graph.
    :param name: Name of the graph.
    :param tf: TensorFlow module, imported outside of this function call.
    :return: TensorFlow graph.
    """
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile('models/{}.pb'.format(name), 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')
    return detection_graph


def put_number(number: Union[float, int], x: int, y: int, image: np.array):
    """
    :param number: Number to display.
    :param x: X coordinate to put number.
    :param y: Y coordinate to put number.
    :param image: Image to put number on.
    """
    if number is not None:
        cv2.putText(image, str(int(number)), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1, cv2.LINE_AA)


def bounding_box_coords(bounding_box: iter, frame: np.array) -> (int, int, int, int):
    """
    :param bounding_box: A straight bounding box.
    :param frame: Frame in which the bounding box was found.
    :return: Left X coordinate, right X coordinate, top Y coordinate, bottom Y coordinate.
    """
    cols = frame.shape[1]
    rows = frame.shape[0]
    x1 = bounding_box[1] * cols
    x2 = bounding_box[3] * cols
    y1 = bounding_box[0] * rows
    y2 = bounding_box[2] * rows
    return x1, x2, y1, y2


if __name__ == "__main__":
    functions = dir()
    print('List of functions in utils:')  # Print all functions in file.
    print('\tType\t\tName')
    print('---------------------------')
    for func in functions:
        if func[0] == func[0].lower() and func[0] is not '_':
            to_print = f'{func}'
            try:
                __import__(func)
                to_print = '|   import\t\t' + to_print
                print(to_print)
            except:
                to_print = '|   function\t' + to_print
                print(to_print)
    while True:
        try:
            inquiry = input('What would you like help with? ')
            help(eval(inquiry))
        except:
            continue
