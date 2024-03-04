import asyncio
from collections import deque
import json
from time import sleep
import os

import stomp

from .schemas import DIAMOND_FILEPATH_KEY, DIAMOND_STATUS_KEY, STOMP_TOPIC_NAME
from ..ingest import get_tiled_config, process_file
import logging

TILED_INGEST_TILED_CONFIG_PATH = os.getenv("TILED_INGEST_TILED_CONFIG_PATH")
STOMP_SERVER = os.getenv("STOMP_SERVER")

STOMP_LOG_LEVEL = os.getenv("STOMP_LOG_LEVEL", "INFO")
logging.getLogger("stomp").setLevel(logging.getLevelName(STOMP_LOG_LEVEL))
logging.getLogger("asyncio").setLevel(logging.INFO)


class ScanListener(stomp.ConnectionListener):
    def __init__(self):
        self.messages = deque()

    def on_error(self, message):
        print("received an error %s" % message)

    def on_message(self, message):
        # this might be a difference in version of stomp from what
        # diamond is using. In their example, messsage and headers are
        # separate parameters. But in the version I'm using, the message
        # is an object that contains body and headers
        ob = json.loads(message.body)
        # if (ob["status"] == "STARTED"):
        if ob[DIAMOND_STATUS_KEY] == "COMPLETE":
            self.messages.append(ob[DIAMOND_FILEPATH_KEY])


def start_consumer():
    tiled_config = get_tiled_config(TILED_INGEST_TILED_CONFIG_PATH)
    conn = stomp.Connection([(STOMP_SERVER, 61613)])
    scan_listener = ScanListener()
    conn.set_listener("", scan_listener)
    conn.connect()
    conn.subscribe(destination=STOMP_TOPIC_NAME, id=1, ack="auto")
    while True:
        if scan_listener.messages:
            new_file_path = scan_listener.messages.popleft()
            try:
                asyncio.run(process_file(new_file_path, tiled_config))
            except Exception as e:
                print("Failed to process file " + new_file_path)
                print(str(e))

        sleep(1)


if __name__ == "__main__":
    start_consumer()
