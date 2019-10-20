from file import File
from abc import abstractmethod


class HSVHandler:
    """
    Attributes
    ----------
    file : file
        - the file from which initial HSV values will be read, and where new HSV values will be saved
        - written in dictionary format, with the keys indicating the type of variable (h, s, or v), each holding two
        variables (low, high)
        - corresponds to the target under name
        - if such a file does not exist, creates it, and writes an open HSV range into it (low values set to 0, high
        values set to 255)
    """
    def __init__(self, name: str):
        self.name = name
        self.file = File(self.name, {'H': (0, 255), 'S': (0, 255), 'V': (0, 255)}, 'hsv', 'json')

    @abstractmethod
    def save_hsv(self):
        pass

    @abstractmethod
    def reload(self):
        pass

    @abstractmethod
    def get_hsv(self):
        pass
