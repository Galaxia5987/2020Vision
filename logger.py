import time
from file import File


class Logger:
    def __init__(self, main):
        self.main = main
        name = time.strftime('%d-%m-%Y %H-%M-%S')
        data = []
        data.append(str(self.main.results) + '\n')
        data.append('Time;Latency;Sees potential targets?;Sees target?\n')
        folder = 'logs'
        extension = 'csv'
        self.file = File(name, None, folder, extension)
        with open(self.file.get_filename(), 'a') as log:
            log.writelines(data)

    def record_latency(self):
        data = []
        current_time = '{}'.format(time.strftime('%H-%M-%S'))
        data.append(current_time)
        data.append(';')
        latency = '{:.3f}'.format(time.time() - self.main.timer)
        data.append(latency)
        data.append(';')

        with open(self.file.get_filename(), 'a') as log:
            log.writelines(data)

    def record_contours(self):
        data = []
        potential_target = '{}'.format(self.main.is_potential_target)
        data.append(potential_target)
        data.append(';')
        target = '{}'.format(self.main.is_target)
        data.append(target)
        data.append('\n')

        with open(self.file.get_filename(), 'a') as log:
            log.writelines(data)
