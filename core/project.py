import json
import os
from config import DEFAULT_BUS, DEFAULT_CHANNEL

PROJECT_FILE = "project.json"


class Project:
    def __init__(self):
        self.name = "Untitled Project"
        self.dbc_path = ""
        self.bus_interface = DEFAULT_BUS
        self.channel = DEFAULT_CHANNEL
        self.bitrate = 500000

    def save(self, path: str = PROJECT_FILE):
        with open(path, "w") as f:
            json.dump(self.__dict__, f, indent=2)

    def load(self, path: str = PROJECT_FILE):
        if not os.path.exists(path):
            return
        with open(path) as f:
            data = json.load(f)
        self.__dict__.update(data)

    def to_dict(self):
        return self.__dict__.copy()


project = Project()
