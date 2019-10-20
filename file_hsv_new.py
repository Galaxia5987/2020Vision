from hsv_handler import HSVHandler


class FileHSV(HSVHandler):
    """
    HSV value handler that loads values from/writes values to a file. Implements a lot of methods from File in file.py.

    Uses: A simple HSV loader for use in matches, as an alternative to trackbars.

    Attributes
    ----------

    hsv_values : dict
        - initial HSV values loaded from the file associated with the target
    """

    def __init__(self, name: str):
        """
        Instantiate an HSV value handler.

        Uses: Replaces Trackbars when local display is not requested.
        See: __init__ in main.py

        :param name: Target name.
        """
        super().__init__(name)
        self.hsv_values = self.file.load_file()

    def save_hsv(self):
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
