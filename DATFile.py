import sys
import os
import gzip
from TagReader import TagReader

class DATFile:
    def __init__(self, path, no_read=False):
        self.path = path
        if not no_read:
            self.read()

    def read(self):
        self.file = gzip.open(self.path)
        self.tagReader = TagReader(self.file)

        self.root = self.tagReader.readTag()
        self.file.close()
