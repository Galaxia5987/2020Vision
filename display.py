import logging
import os

import cv2


class Display:
    """
    Handles receiving frames from the camera provider and displaying frames. Can record frames as videos for debugging
    purposes.

    Attributes
    ----------
    codec
        - fourcc code to pass to the video writer when recording
    is_recording : bool
        - recording flag
    out
        - defined as a video writer if recording is requested
    camera_provider : cv_camera.CVCamera or pi_camera.PICamera or realsense.RealSense
        - the camera provider from which frames are received.
    """
    def __init__(self, provider):
        """
        Receive a camera provider and initialize it.

        :param provider: The camera provider from which frames are received.
        """
        self.codec = cv2.VideoWriter_fourcc(*'XVID')
        self.is_recording = False
        self.out = None
        self.camera_provider = provider
        self.camera_provider.start()

    def get_frame(self):
        """
        Return the most current frame from the camera provider.
        :return: Latest frame.
        """
        return self.camera_provider.frame

    def change_exposure(self, new_exposure: int):
        """
        Change the exposure through the camera provider.
        :param new_exposure: New exposure to set.
        """
        self.camera_provider.set_exposure(new_exposure)

    def release(self):
        """
        Release the camera, save the recording, and destroy all windows.
        """
        # TODO: Replace the following two lines with the "stop_recording" function
        if self.out:
            self.out.release()
        self.camera_provider.release()
        cv2.destroyAllWindows()

    def start_recording(self, title):
        """
        Begin recording.
        :param title: The title under which the recording file is saved.
        """
        logging.info('Starting recording with title {}'.format(title))
        if not os.path.isdir('recordings'):
            os.makedirs('recordings')
        self.is_recording = True
        self.out = cv2.VideoWriter('recordings/{}.avi'.format(title), self.codec, 30.0, self.camera_provider.get_resolution())

    def stop_recording(self):
        """
        Stop recording, save the recording into the file, and release the video writer.
        """
        if self.out:
            logging.info('Releasing video recorder')
            self.out.release()

    def process_frame(self, frame, title: str, show: bool):
        """
        Show and or record frame.
        :param frame: OpenCV frame.
        :param title: Title of window where frame will be displayed.
        :param show: Show or don't show on local display.
        """
        # Show frame
        if show:
            cv2.imshow(title, frame)
        # Record frame
        if self.is_recording and title == 'image' and self.out:
            self.out.write(frame)


if __name__ == "__main__":
    help(Display)
