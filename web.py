import logging
import time
from threading import Thread

import cv2
import imutils
from flask import Flask, render_template, Response, request

import utils


class Web:
    """
    This class handles the web server used for streaming & control.

    Attributes
    ----------

    main: main.Main
        - the main in which the target recognition loop is being run
    app : Flask
        - the application that will run the streaming service
    frame
        - the frame that is being streamed
    resize: bool, optional
        - whether the frame should be resized
        - used to improve performance
    """

    def __init__(self, main, resize: bool = False):
        """

        :param main: The Main in which the target recognition loop is being run.
        :param resize: Whether the frame should be resized, False by default.
        """
        self.main = main
        self.app = Flask('Web')
        self.frame = None
        self.resize = resize

        # Index html file
        @self.app.route('/')
        def index():  # Returns the HTML template
            if self.main.results.networktables:
                filename = self.main.nt.get_item('match data', 'Enter file name')
            else:
                filename = time.strftime("%d-%m-%Y-%H-%M-%S")
            return render_template('index.html', initial_filename=filename)

        # Video feed endpoint
        @self.app.route('/stream.mjpg')
        def video_feed():  # Initiate the feed
            return Response(self.stream_frame(),
                            mimetype='multipart/x-mixed-replace; boundary=frame')

        @self.app.route('/save', methods=['POST'])
        def save():
            """
            Post route that saves HSV values.
            See: save_hsv_values() in FileHSV in file_hsv.py; save_hsv_values() in Trackbars in trackbars.py
            """
            self.main.hsv_handler.save_hsv_values()
            return '', 204

        @self.app.route('/update', methods=['POST'])
        def update():
            """
            Post route to change target. Receive the name of the target from a string, and change the target in the
            main.
            See: change_name(name) in Main in main.py
            """
            target = request.data.decode('utf-8')
            self.main.change_name(target)
            return '', 204

        @self.app.route('/record', methods=['POST'])
        def record():
            """
            Start recording. Receive the name of the file to record to from a string, and send an instruction to the
            display handler to begin recording.
            See: start_recording(title) in Display in display.py
            """
            filename = request.data.decode('utf-8')
            if filename:
                self.main.display.start_recording(filename)
            else:
                logging.warning('File name not present')
            return '', 204

        @self.app.route('/stopRecording', methods=['POST'])
        def stop_recording():
            """
            Stop recording. Send a message to the display handler to save the file.
            See: stop_recording() in Display in display.py
            """
            self.main.display.stop_recording()
            return '', 204

    def stream_frame(self):
        """
        A generator that encodes and streams the last frame to the stream endpoint.
        :return: JPEG encoded frame.
        """
        while True:
            frame = self.frame
            if self.resize:
                frame = imutils.resize(frame, 320)
            if frame is None:
                continue
            jpg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 20])[1].tostring()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')

    def serve(self):
        """
        Start the web server, print out ip and port for ease of use, run flask and bind to all IPs
        """
        logging.info('Web server: http://{}:5802'.format(utils.get_ip()))
        self.app.run('0.0.0.0', 5802, threaded=True)

    def start_thread(self):
        """
        Run web server in a thread - daemon so it lets the program exit.
        """
        Thread(target=self.serve, daemon=True).start()


if __name__ == "__main__":
    help(Web)
