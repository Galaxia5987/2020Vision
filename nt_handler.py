import atexit
import logging

from networktables import NetworkTables

import constants
from file import File


class NT:
    """
    This is a class for handling all networktables operations, mainly starting a server and sending to and receiving
    variables from it.

    WARNING: This class is incomplete and requires further tuning.

    Attributes
    ----------

    name : str
        - the name of the target with which the variables sent and received are associated
    prefix : str
        - added to variable names to ease finding and sending them
    team_number : int
        - the number of the team running the code, used for IP
    file : File
        - the file from which the target's variables will be read at the beginning of the run, and to which the target's
        variables will be saved at the end of the run
    table
        - the table to which the variables will be sent and from which the variables will be received
    """
    def __init__(self, name: str):
        """
        Create a networktables server, and create the vision table.

        :param name: The name of the target.
        """
        self.name = name
        self.prefix = '/vision/' + self.name + '_'
        self.team_number = 5987
        # The values file for the target, with a default value for when no such file exists
        self.file = File(self.name, '[NetworkTables Storage 3.0]\nstring "/vision/{}_name"={}',
                         'values', 'nt'.format(self.name, self.name))
        # Server IP returned by get_nt_server()
        server = self.get_nt_server()
        # Set update rate as defined in constants.py
        NetworkTables.setUpdateRate(constants.NT_RATE)
        logging.info('Initiating network tables connection with {}'.format(server))
        NetworkTables.initialize(server=server)
        NetworkTables.addConnectionListener(self.connection_listener, immediateNotify=True)
        # Create individual table instead of clogging SmartDashboard
        self.table = NetworkTables.getTable('vision')

    @staticmethod
    def get_nt_server():
        """
        IP for networktables server.
        :return: IP corresponding to team number.
        """
        # TODO: Make dynamic based on self.team_number
        return '10.59.87.2'

    @staticmethod
    def connection_listener(connected, info):
        """
        Callback for when network tables connect.
        :param connected: Connected bool.
        :param info: Connection info.
        """
        if connected:
            logging.info('Success: {}'.format(info))
        else:
            logging.error('Fail: {}'.format(info))

    def set_item(self, key, value):
        """
        Add a value to SmartDashboard.

        :param key: The name the value will be stored under and displayed.
        :param value: The information the key will hold.
        """
        # TODO: Add self.prefix
        self.table.putValue(key, value)

    def get_item(self, key, default_value):
        """
        Get a value from SmartDashboard.

        :param key: The name the value is stored under.
        :param default_value: The value returned if key holds none.
        :return: The value that the key holds, default_value if it holds none.
        """
        # TODO: Add self.prefix
        return self.table.getValue(key, default_value)

    def load_values(self):
        """
        Loads the target's values onto networktables, using its values file.
        Values files are found in the 'values' folder and have the .nt extension.
        """
        # TODO: Add self.prefix and extension
        NetworkTables.loadEntries(self.file.get_filename(), prefix='/vision/' + self.name + '_')

    def save_values(self):
        """
        Save the target's values from networktables, to its values file.
        Values files are found in the 'values' folder and have the .nt extension.
        """
        # TODO: Add self.prefix and extension
        NetworkTables.saveEntries(self.file.get_filename(), prefix='/vision/' + self.name + '_')


if __name__ == "__main__":
    help(NT)
