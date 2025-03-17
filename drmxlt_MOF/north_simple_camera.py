import cv2
from datetime import datetime
import numpy as np
import threading
from time import sleep


class SimpleCamera:

    def __init__(self, source_num=0):
        self.source_num = source_num
        self.last_frame = None
        self.cam = cv2.VideoCapture(source_num)
        self.streaming = False
        threading.Thread(target=self._frame_grabber, daemon=True).start()

    def _frame_grabber(self):
        while True:
            ret, self.last_frame = self.cam.read()
            if self.streaming:
                cv2.imshow(f'Camera {self.source_num} stream', self.last_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.streaming = False

    def capture(self):
        return SimplePhoto(self.last_frame)

    def stream(self):
        self.streaming = True
        #threading.Thread(target=self._stream_worker).start()

    def stop_stream(self):
        self.streaming = False

    def _stream_worker(self):
        while True:
            cv2.imshow(f'Camera {self.source_num} stream', self.last_frame)



class SimplePhoto:

    def __init__(self, img):
        self.img = img
        self.name = f'SAMPLE_{datetime.now().strftime("%Y%m%d-%H%M%S")}'

    def show(self):
        threading.Thread(target=self._show_img_worker, daemon=True).start()

    def _show_img_worker(self):
        cv2.imshow(self.name, self.img)
        cv2.waitKey(0)

    def save(self):
        cv2.imwrite(f'{self.name}.png', self.img)
        
    def get_size(self):
        return self.img.shape
