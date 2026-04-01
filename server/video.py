from typing import Optional, Tuple
import cv2
import queue
import threading

# This solution is taken from the following link:
# https://stackoverflow.com/questions/43665208/how-to-get-the-latest-frame-from-capture-device-camera-in-opencv
class BufferlessVideo:
    def __init__(self, endpoint: str):
        self.capture = cv2.VideoCapture(endpoint)
        self.queue = queue.Queue()
        self.t = threading.Thread(target=self.get_latest_frame)
        self.t.daemon = True
        self.t.start()
    def get_latest_frame(self):
        while True:
            ret, frame = self.capture.read()
            if not ret:
                break
            if not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    pass
            self.queue.put((ret, frame))
    def read(self):
        return self.queue.get()
    def is_opened(self):
        return self.capture.isOpened()
