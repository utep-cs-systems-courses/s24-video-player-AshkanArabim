#!/usr/bin/env python3

import threading
import cv2
import numpy as np
import base64
import queue


class blockingQueue:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self._queue = queue.Queue(self.capacity)
        self._full = threading.Semaphore(0)
        self._empty = threading.Semaphore(self.capacity)
        self._queue_lock = threading.Lock()
    
    def put(self, item):
        self._empty.acquire()
        self._queue_lock.acquire()
        self._queue.put(item)
        self._queue_lock.release()
        self._full.release()
        
    def get(self):
        self._full.acquire()
        self._queue_lock.acquire()
        to_return = self._queue.get()
        self._queue_lock.release()
        self._empty.release()
        
        return to_return
    

def extract_frames(filename, output_buffer, maxFramesToLoad=9999):
    # Initialize frame count 
    count = 0

    # open video file
    vidcap = cv2.VideoCapture(filename)

    # read first image
    success,image = vidcap.read()
    
    print(f'Reading frame {count} {success}')
    while success and count < maxFramesToLoad:
        # get a jpg encoded frame
        success, jpgImage = cv2.imencode('.jpg', image)

        #encode the frame as base 64 to make debugging easier
        jpgAsText = base64.b64encode(jpgImage)

        # add the frame to the buffer
        output_buffer.put(image)

        success,image = vidcap.read()
        print(f'Reading frame {count} {success}')
        count += 1

    output_buffer.put("END")
    print('Frame extraction complete')


def convert_to_grayscale(input_buffer, output_buffer):
    
    count = 0
    input_frame = input_buffer.get()
    
    while not (isinstance(input_frame, str) and input_frame == "END"):
        print(f'Converting frame {count}')

        # convert the image to grayscale
        grayscaleFrame = cv2.cvtColor(input_frame, cv2.COLOR_BGR2GRAY)
        
        # write output file
        output_buffer.put(grayscaleFrame)

        count += 1

        # load the next frame
        input_frame = input_buffer.get()
    
    output_buffer.put("END")

        
def display_frames(input_buffer):
    # initialize frame count
    count = 0

    input_frame = input_buffer.get()
    while not (isinstance(input_frame, str) and input_frame == "END"):
        # get the next frame
        frame = input_buffer.get()

        print(f'Displaying frame {count}')        

        # display the image in a window called "video" and wait 42ms
        # before displaying the next frame
        cv2.imshow('Video', frame)
        if cv2.waitKey(42) and 0xFF == ord("q"):
            break

        count += 1

    print('Finished displaying all frames')
    # cleanup the windows
    cv2.destroyAllWindows()


# filename of clip to load
filename = 'clip.mp4'

# thread to extract the frames
extracted_queue = blockingQueue(10)
extract_frames_thread = threading.Thread(target=lambda: extract_frames(filename, extracted_queue, 72))

# thread to convert to grayscale
grayscale_queue = blockingQueue(10)
convert_to_grayscale_thread = threading.Thread(target=lambda: convert_to_grayscale(extracted_queue, grayscale_queue))

# thread to display the frames
display_frames_thread = threading.Thread(target=lambda: display_frames(grayscale_queue))
threading.Thread()

# start all threads
extract_frames_thread.start()
convert_to_grayscale_thread.start()
display_frames_thread.start()
