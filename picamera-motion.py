#!/usr/bin/python
"""
 Lightweight Motion Detection using python picamera libraries.
 Requires a Raspberry Pi computer with a picamera module.
 This code is based on a raspberry pi forum post by user utpalc
 modified by Claude Pageau for this working example.

 This project can be used for further development
 and is located on GitHub at
 https://github.com/pageauc/picamera-motion

 For a full featured program see my GitHub pi-timolo project at
 https://github.com/pageauc/pi-timolo
"""

import os
import datetime
import time
import glob
import logging
import picamera
import picamera.array
import notifications.FTPUploader as FTPUploader
import notifications.MSTeamsNontifier as MSTeamsNontifier
if not os.path.exists('settings.py'):
    logging.error(
        """File Not Found - settings.py
             Cannot import program variables."
             To Repair Run menubox.sh UPGRADE menu pick.""")
    exit(1)
try:
    from settings import *
except ImportError:
    logging.error("Could Not Import settings.py")
    exit(1)

PROG_VER = "ver 2.8"
SCRIPT_PATH = os.path.abspath(__file__)
# get script file name without extension
PROG_NAME = SCRIPT_PATH[SCRIPT_PATH.rfind("/")+1:SCRIPT_PATH.rfind(".")]
SCRIPT_DIR = SCRIPT_PATH[0:SCRIPT_PATH.rfind("/")+1]  # get script directory
# conversion from stream coordinate to full image coordinate
X_MO_CONV = imageWidth/float(streamWidth)
Y_MO_CONV = imageHeight/float(streamHeight)

# ------------------------------------------------------------------------------


def check_image_dir(image_dir):
    """ if image_dir does not exist create the folder """
    if not os.path.isdir(image_dir):
        logging.debug("Creating Image Storage folder {}".format(image_dir))
        try:
            os.makedirs(image_dir)
        except OSError as err:
            logging.error(
                "Could Not Create Folder {} {}".format(image_dir, err))
            exit(1)

# ------------------------------------------------------------------------------


def get_file_name(image_dir, image_name_prefix, current_count):
    """
    Create a file name based on settings.py variables
    Note image numbering will not be saved but will be inferred from the
    last image name using get_last_counter() function.
    If the last image file name is not a number sequence file
    then numbering will start from imageNumStart variable and may overwrite
    previous number sequence images. This can happen if you switch between
    number sequence and datetime sequence in the same folder.
    or
    Set imageNumOn=False to save images in datetime format to
    ensure image name is unique and avoid overwriting previous image(s).

    """
    if imageNumOn:
        # you could also use os.path.join to construct image path file_path
        file_path = image_dir + "/"+image_name_prefix+str(current_count)+".jpg"
    else:
        right_now = datetime.datetime.now()
        file_path = ("{}/{}{:04d}{:02d}{:02d}-{:02d}{:02d}{:02d}.jpg".format(image_dir, image_name_prefix,
                                                                             right_now.year, right_now.month, right_now.day,
                                                                             right_now.hour, right_now.minute, right_now.second))
    return file_path

# ------------------------------------------------------------------------------


def get_last_counter():
    """
    glob imagePath for last saved jpg file. Try to extract image counter from
    file name and convert to integer.  If it fails restart number sequence.

    Note: If the last saved jpg file name is not in number sequence name
    format (example was in date time naming format) then previous number
    sequence images will be overwritten.

    Avoid switching back and forth between datetime and number sequences
    per imageNumOn variable in settings.py
    """
    counter = imageNumStart
    if imageNumOn:
        image_ext = ".jpg"
        search_str = imagePath + "/*" + image_ext
        file_prefix_len = len(imagePath + imageNamePrefix)+1
        try:
           # Scan image folder for most recent jpg file
           # and try to extract most recent number counter from file name
            newest = max(glob.iglob(search_str), key=os.path.getctime)
            count_str = newest[file_prefix_len:newest.find(image_ext)]
            logging.info(
                "Last Saved Image is {} Try to Convert {}".format(newest, count_str))
            counter = int(count_str)+1
            logging.info("Next Image Counter is {}".format(counter))
        except:
            logging.warn(
                "Restart Numbering at {} WARNING: Previous Files May be Over Written.".format(counter))
    return counter

# ------------------------------------------------------------------------------


def save_image(image_path):
    """
    Take a photo with the picamera. Note: You may need to increase
    sleep for low light conditions
    """
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
        camera.capture(image_path)
        camera.close()

# ------------------------------------------------------------------------------


def get_stream_array():
    """ Take a stream image and return the image data array"""
    with picamera.PiCamera() as camera:
        camera.resolution = (streamWidth, streamHeight)
        with picamera.array.PiRGBArray(camera) as stream:
            camera.vflip = imageVFlip
            camera.hflip = imageHFlip
            camera.exposure_mode = 'auto'
            camera.awb_mode = 'auto'
            camera.capture(stream, format='rgb')
            camera.close()
            return stream.array

# ------------------------------------------------------------------------------


def scan_motion():
    """ Loop until motion is detected """
    data1 = get_stream_array()
    while True:
        data2 = get_stream_array()
        diff_count = 0
        for y in range(0, streamHeight):
            for x in range(0, streamWidth):
                # get pixel differences. Conversion to int
                # is required to avoid unsigned short overflow.
                diff = abs(int(data1[y][x][1]) - int(data2[y][x][1]))
                if diff > threshold:
                    diff_count += 1
                    if diff_count > sensitivity:
                        # x,y is a very rough motion position
                        return x, y
        data1 = data2

# ------------------------------------------------------------------------------


def do_motion_detection():
    """
    Loop until motion found then take an image,
    and continue motion detection. ctrl-c to exit
    """
    ftp = FTPUploader.FTPUploader(notification_config["ftp"])
    teams = MSTeamsNontifier.MSTeamsNontifier(notification_config["teams"])

    current_count = get_last_counter()
    if not imageNumOn:
        logging.info("File Naming by Date Time Sequence")
    while True:
        x_pos, y_pos = scan_motion()
        file_name = save_image(imagePath, imageNamePrefix, current_count)

        save_image(file_name)
        image_fname = os.path.basename(file_name)

        ftp.upload(file_name, image_fname)
        teams.notify(
            "Detected motion", notification_config["teams"]["base_image"] + "/" + image_fname)

        if imageNumOn:
            current_count += 1

        # Convert xy movement location for full size image
        mo_x = x_pos * X_MO_CONV
        mo_y = y_pos * Y_MO_CONV
        logging.debug("Motion xy({},{}) Saved {} ({}x{})".format(
            mo_x, mo_y, file_name, imageWidth, imageHeight,))


# Start Main Program Logic
if __name__ == '__main__':
    logging.info("{} {}  written by Claude Pageau".format(PROG_NAME, PROG_VER))
    logging.info("---------------------------------------------")
    check_image_dir(imagePath)
    logging.info("Scan for Motion:  threshold={} (diff)  sensitivity={} (num px's)...".format(
        threshold, sensitivity))
    # if not verbose:
    #     print("%s WARN  : Messages turned off per settings.py verbose = %s"
    #           % (get_now(), verbose))
    try:
        do_motion_detection()
    except KeyboardInterrupt:
        logging.WARN("")
        logging.WARN("User Pressed ctrl-c")
        logging.WARN("Exiting {} {} ".format(PROG_NAME, PROG_VER))
