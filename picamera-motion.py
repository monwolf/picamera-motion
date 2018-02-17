#!/usr/bin/python
"""
 Lightweight Motion Detection using python picamera libraries
 based on code from raspberry pi forum by user utpalc
 modified by Claude Pageau for this working example
 ------------------------------------------------------------
 original code on github https://github.com/pageauc/picamera-motion
 This is sample code that can be used for further development
"""

import os
import picamera
import picamera.array
import datetime
import time
try:
    from settings import *
except ImportError:
    print("ERROR : Could Not import settings.py")
    exit(1)

PROG_VER = "ver 2.1"
PROG_PATH = os.path.abspath(__file__)
BASE_DIR = PROG_PATH[0:PROG_PATH.rfind("/")+1]
BASE_FILE_NAME = PROG_PATH[PROG_PATH.rfind("/")+1:PROG_PATH.rfind(".")]
PROG_NAME = BASE_FILE_NAME
print("%s %s  written by Claude Pageau" % (PROG_NAME, PROG_VER))
print("---------------------------------------------")
if not verbose:
    print("INFO  : Logging has been disabled per verbose=%s" % verbose)

#------------------------------------------------------------------------------
def get_now():
    """ Get datetime and return formatted string"""
    right_now = datetime.datetime.now()
    now = ("%04d%02d%02d-%02d:%02d:%02d"
           % (right_now.year, right_now.month, right_now.day,
              right_now.hour, right_now.minute, right_now.second))
    return now

#------------------------------------------------------------------------------
def check_image_path(image_path):
    """ if image_path does not exist create the folder """
    if not os.path.isdir(image_path):
        if verbose:
            print("INFO  : Creating Image Storage folder %s" % (image_path))
        try:
            os.makedirs(image_path)
        except OSError as err:
            print("ERROR : Could Not Create Folder %s %s" % (image_path, err))
            exit(1)

#------------------------------------------------------------------------------
def get_file_name(image_path, image_name_prefix, current_count):
    """ Create a file name based on settings.py variables """
    if imageNumOn:
        # could use os.path.join to construct file image path
        file_name = image_path + "/" + image_name_prefix + str(current_count) + ".jpg"
    else:
        right_now = datetime.datetime.now()
        file_name = ("%s/%s%04d%02d%02d-%02d%02d%02d.jpg"
                     % (image_path, image_name_prefix,
                        right_now.year, right_now.month, right_now.day,
                        right_now.hour, right_now.minute, right_now.second))
    return file_name

#------------------------------------------------------------------------------
def take_day_image(filename):
    """ Take a picamera image """
    with picamera.PiCamera() as camera:
        camera.resolution = (imageWidth, imageHeight)
        # camera.rotation = cameraRotate
        # Note use imageVFlip and imageHFlip settings.py variables
        if imagePreview:
            camera.start_preview()
        camera.vflip = imageVFlip
        camera.hflip = imageHFlip
        camera.exposure_mode = 'auto'
        camera.awb_mode = 'auto'
        time.sleep(1)
        camera.capture(filename)
    if verbose:
        print("%s INFO  : takeDayImage (%ix%i) - Saved %s"
              % (get_now(), imageWidth, imageHeight, filename))
    return filename

#------------------------------------------------------------------------------
def get_stream_array():
    """ Take a stream image and return the image data array"""
    with picamera.PiCamera() as camera:
        camera.resolution = (streamWidth, streamHeight)
        with picamera.array.PiRGBArray(camera) as stream:
            camera.exposure_mode = 'auto'
            camera.awb_mode = 'auto'
            camera.capture(stream, format='rgb')
            return stream.array

#------------------------------------------------------------------------------
def scan_motion():
    """ Loop until motion is detected """
    data1 = get_stream_array()
    while True:
        data2 = get_stream_array()
        diff_count = 0
        for h in range(0, streamHeight):
            for w in range(0, streamWidth):
                # get the diff of the pixel. Conversion to int
                # is required to avoid unsigned short overflow.
                diff = abs(int(data1[h][w][1]) - int(data2[h][w][1]))
                if  diff > threshold:
                    diff_count += 1
                    if diff_count > sensitivity:
                        return w, h
        data1 = data2

#------------------------------------------------------------------------------
def motion_detection():
    current_count = imageNumStart
    while True:
        x, y = scan_motion()
        if verbose:
            print("%s INFO  : Motion Found At xy(%i,%i) in stream wh(%i,%i)"
                  % (get_now(), x, y, streamWidth, streamHeight))
        filename = get_file_name(imagePath, imageNamePrefix, current_count)
        if imageNumOn:
            current_count += 1
        take_day_image(filename)

# Start Main Program Logic
if __name__ == '__main__':
    check_image_path(imagePath)
    if verbose:
        print("%s INFO  : Scan for Motion "
              "threshold=%i (diff)  sensitivity=%i (num px's)..."
              % (get_now(), threshold, sensitivity))
    try:
        motion_detection()
    except KeyboardInterrupt:
        print("")
        print("INFO  : User Pressed ctrl-c")
        print("        Exiting %s %s " % (PROG_NAME, PROG_VER))
