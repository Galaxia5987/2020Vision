# Focal length dictionary
FOCAL_LENGTHS = {
    'cv': 638.6086956521739,
    'realsense': 606.3,
    'pi': 608.4
}

# Target sizes dictionary
TARGET_SIZES = {'2012': {'width': 0.609, 'height': 0.457, 'closing_circle_radius': 0.381},
                '2015': {'width': 0.425, 'height': 0.177},
                '2016': {'width': 0.508, 'height': 0.304},
                '2018': {'width': 0.508, 'height': 0.203},
                '2019': {'single_width': 0.0508, 'single_height': 0.1397, 'inner_distance_between_tapes': 0.2032,
                         'outer_distance_between_tapes': 0.3015}}

# The distance between the middle of the target and the carpet
HEIGHT_FROM_CARPET = {'2019': {'reflectors': {'hatch': 0.73, 'cargo': 0.9255}},
                      'camera': {'driving_robot': 0.14, 'genesis': 0.92}}

CAMERA_DISTANCE_FROM_CENTER = 0.015  # In meters (genesis)

REALSENSE_SN = '825312070193'

# Game pieces sizes dictionary
GAME_PIECE_SIZES = {'fuel': {'diameter': 0.127},
                    'gear': {'diameter': 0.3},
                    'power_cube': {'width': 0.3302, 'length': 0.3302, 'height': 0.2794},
                    'tennis_ball': {'diameter': 0.134},
                    'cargo': {'diameter': 0.3302}}

CAMERA_CONTRAST = 11
CAMERA_EXPOSURE = 15
CAMERA_FPS = 5
CAMERA_WIDTH = 3
CAMERA_HEIGHT = 4

REALSENSE_TIMEOUT_MS = 2000

NT_RATE = 0.01
