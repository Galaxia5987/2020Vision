from file import File


class FileHSV:
    """
    HSV value handler that loads values from/writes values to a file. Implements a lot of methods from File in file.py.

    Uses: A simple HSV loader for use in matches, as an alternative to trackbars.

    Attributes
    ----------

    file : File
        - the file to which HSV values are written/from which HSV values are read, associated with the name of the
        target passed in __init__
        - if file doesn't exist, writes an open-range HSV dictionary where the keys are the three variables (H, S, and
        V), each key holds two values (low and high), and all low values are set to 0 and all high values are set to 255
    hsv_values : dict
        - initial HSV values loaded from the file associated with the target
    """

    def __init__(self, name):
        """
        Instantiate an HSV value handler.

        Uses: Replaces Trackbars when local display is not requested.
        See: __init__ in main.py

        :param name: Target name.
        """
        self.file = File(name, {'H': (0, 255), 'S': (0, 255), 'V': (0, 255)}, 'hsv', 'json')
        self.hsv_values = self.file.load_file()

    def save_hsv_values(self):
        """
        Dry method to match the one in Trackbars.
        """
        pass

    def reload(self):
        """
        Reload the values from self.file.
        """
        self.hsv_values = self.file.load_file()

    def get_hsv(self) -> dict:
        """
        Get current HSV.

        This method is here to allow diversity, and the use of FileHSV and Trackbars interchangeably.
        :return: Cached HSV values that were loaded from self.file.
        """
        return self.hsv_values


if __name__ == "__main__":
    help(FileHSV)
