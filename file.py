import json
import os
from typing import Callable


class File:
    """
    Handles reading and writing files.

    Uses: Reading and writing HSV files. Can be used for saving networktables data between runs.
    See: __init__, save_hsv_values(), reload_trackbars(), create_trackbars() in Trackbars in trackbars.py; __init__,
    load_values(), save_values in NT in nt_handler.py

    Attributes
    ----------

    name : str
        - the name of the target with which the file is associated
    default
        - the default data to write to the file if it doesn't exist
    folder : str
        - the directory in which the file is located
    extension : str
        - the extension of the file
    """

    def __init__(self, name: str, default, folder: str, extension: str):
        """
        Instantiate a file.
        :param name: The name of the target to associate the file with.
        :param default: Default value to write to the file if it doesn't exist.
        :param folder: Folder to write the file to/call the file from.
        :param extension: The extension of the file to call/write.
        """
        self.name = name
        self.default = default
        self.folder = folder
        self.extension = extension

    def get_filename(self) -> str:
        """
        Format filename.
        :return: The filename in a folder/name.extension format.
        """
        return '{}/{}.{}'.format(self.folder, self.name, self.extension)

    def save_file(self, data):
        """
        Save file to address given by get_filename().
        :param data: The data to save to the file.
        """
        with open(self.get_filename(), 'w') as f:
            json.dump(data, f)

    def load_file(self):
        """
        Load file from address given by get_filename().
        :return: The data from the file, raw.
        """
        if not os.path.isfile(self.get_filename()):
            if isinstance(self.default, Callable):
                self.save_file(self.default(self.name))
            else:
                self.save_file(self.default)
        with open(self.get_filename(), 'r') as f:
            return json.load(f)


if __name__ == "__main__":
    help(File)
