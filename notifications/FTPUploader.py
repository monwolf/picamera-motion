from pathlib import Path
import requests
import os
#import pysftp
from ftplib import FTP

class FTPUploader:
    """ Send Teams Notification """

    def __init__(self, config) -> None:
        self._config = config

    def upload(self, image_path, image_fname):

        srv = FTP(host=self._config["host"], user=self._config["username"],
        passwd=self._config["password"])
        srv.cwd(self._config["path"]) #chdir to public
        with open(image_path, 'rb') as file:
            srv.storbinary('STOR {}'.format(image_fname), file) 
