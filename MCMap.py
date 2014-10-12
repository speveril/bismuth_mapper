import sys
import os
import gzip
from TagReader import TagReader

class MCMap:
    def __init__(self, path, no_read=False):
        self.path = path
        if not no_read:
            self.read()

    def read(self):
        self.file = gzip.open(self.path)
        self.tagReader = TagReader(self.file)

        self.root = self.tagReader.readTag()
        self.file.close()

        if self.root['data']:
            for tag_id in self.root['data'].value:
                tag = self.root['data'][tag_id]
                if tag.name == 'scale':
                    self.scale = tag.value
                elif tag.name == 'dimension':
                    self.dimension = tag.value
                elif tag.name == 'height':
                    self.height = tag.value
                elif tag.name == 'width':
                    self.width = tag.value
                elif tag.name == 'xCenter':
                    self.xCenter = tag.value
                elif tag.name == 'zCenter':
                    self.zCenter = tag.value
                elif tag.name == 'colors':
                    self.colors = tag.value
