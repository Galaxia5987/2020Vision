import cv2

from hsv_handler import HSVHandler


class Trackbars(HSVHandler):
    """
    This class handles the trackbar window that allows us to change and set the HSV values.

    Attributes
    ----------
    name : str
        - the name of the target for which the trackbars are created, and hsv values will be saved.
    window
        - the window in which the trackbars will exist.
    callback : function
        :returns None
        - a dry callback function for the trackbars, since OpenCv requires one but it isn't needed.
    """

    def __init__(self, name: str):
        """
        Create the trackbars window, create an HSV file, and assign the HSV values corresponding to the target.

        See: create_trackbars(), File class in file.py, __init__ in main.py

        :param name: The name of the target. Will be used for creating, or calling, the right file.
        """
        super().__init__(name)
        self.window = cv2.namedWindow('HSV')  # Create window
        self.callback = lambda v: None  # Dry callback for trackbars since it's not needed
        self.create_trackbars()

    def save_hsv(self):
        """
        Save HSV values to self.file.

        See: get_hsv()
        """
        self.file.save_file(self.get_hsv())

    def reload(self):
        """
        Reload the trackbars from self.file.

        Uses: Call when selecting a new target, and self.file changes.
        """
        hsv = self.file.load_file()
        cv2.setTrackbarPos('lowH', 'HSV', hsv['H'][0])
        cv2.setTrackbarPos('highH', 'HSV', hsv['H'][1])

        cv2.setTrackbarPos('lowS', 'HSV', hsv['S'][0])
        cv2.setTrackbarPos('highS', 'HSV', hsv['S'][1])

        cv2.setTrackbarPos('lowV', 'HSV', hsv['V'][0])
        cv2.setTrackbarPos('highV', 'HSV', hsv['V'][1])

    def create_trackbars(self):
        """
        Create the trackbars intially with the value from the file.

        See: load_file() in file.py
        """
        hsv = self.file.load_file()
        # Create trackbars for color change
        cv2.createTrackbar('lowH', 'HSV', hsv['H'][0], 179, self.callback)
        cv2.createTrackbar('highH', 'HSV', hsv['H'][1], 179, self.callback)

        cv2.createTrackbar('lowS', 'HSV', hsv['S'][0], 255, self.callback)
        cv2.createTrackbar('highS', 'HSV', hsv['S'][1], 255, self.callback)

        cv2.createTrackbar('lowV', 'HSV', hsv['V'][0], 255, self.callback)
        cv2.createTrackbar('highV', 'HSV', hsv['V'][1], 255, self.callback)

    @staticmethod
    def get_hsv() -> dict:
        """
        Get HSV values from trackbars.

        Uses: Get HSV values for mask filtering, save HSV values to file.
        See: save_hsv_values(), loop() in main.py

        :return: HSV values, in dictionary format. The keys are the 3 variables, which hold two variable for low and
        high.
        """
        low_h = cv2.getTrackbarPos('lowH', 'HSV')
        high_h = cv2.getTrackbarPos('highH', 'HSV')
        low_s = cv2.getTrackbarPos('lowS', 'HSV')
        high_s = cv2.getTrackbarPos('highS', 'HSV')
        low_v = cv2.getTrackbarPos('lowV', 'HSV')
        high_v = cv2.getTrackbarPos('highV', 'HSV')
        return {'H': (low_h, high_h), 'S': (low_s, high_s), 'V': (low_v, high_v)}

    def change_hsv(self,values):
        new_HSV = {'H':[values[0],values[1]],'S':[values[3],values[4]],"V":[values[5],values[6]]}
        self.file.save_file(new_HSV)


if __name__ == "__main__":
    help(Trackbars)

