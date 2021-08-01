import requests
import logging
import json

class MSTeamsNontifier:
    """ Send Teams Notification """
    def __init__(self, config) -> None:
        self._config = config

    # @staticmethod
    # def _encode64(image_path):
    #     """ This function reads a file and encode to a base64 string/byte """
    #     with open(image_path, "rb") as image_file:
    #         encoded_string = base64.b64encode(image_file.read())
    #     return encoded_string

    def notify(self, text, image_url):
        """ This function will send a webhook notification to a teams channel """
        schema = {
            "@type": "MessageCard",
            "text": text,
            "sections": [
                {
                    "images": [
                        {
                            #"image": "data:image/jpeg;base64,{}".format(MSTeamsNontifier._encode64(image_path).decode("utf-8"))"
                            "image": image_url
                        }
                    ]
                }
            ]
        }
        logging.error(json.dumps(schema))
        res = requests.post(self._config["teams_webhook_url"], json=schema)
        
        if res.content != b'1':
            logging.error("Status Code: {}, Response {}".format(
                        res.status_code, res.content))
            raise "The notification went wrong" 

