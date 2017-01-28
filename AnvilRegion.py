import sys
import struct
import os
import io
import gzip
import zlib
from TagReader import TagReader

class AnvilRegion:
    def __init__(self, path, no_read=False):
        self.path = path
        self.file = open(path, "rb")
        self.chunks = []

        if not no_read:
            self.read()

    def read(self):
        #print("Loading anvil region " + self.path)
        chunk_info = []

        for i in range(0, 1024):
            chunk_int = struct.unpack(">I", self.file.read(4))[0]
            chunk_loc = chunk_int >> 8
            chunk_sec = chunk_int & 255
            chunk_info.append((chunk_loc, chunk_sec))

        for i in range(0, 1024):
            chunk_time = struct.unpack(">I", self.file.read(4))
            chunk_info[i] = (chunk_info[i][0], chunk_info[i][1], chunk_time)

        for ch in chunk_info:
            if ch[1] == 0:
                continue
            self.file.seek(ch[0] * 4096)
            raw_chunk_size = struct.unpack(">I", self.file.read(4))[0]
            raw_chunk_type = struct.unpack("b", self.file.read(1))[0]
            raw_chunk_data = self.file.read(raw_chunk_size - 1)

            #print("-- CHUNK -- (type:" + str(raw_chunk_type) + "," + str(ch) + ") --")
            if raw_chunk_type > 0:
                chunk_data = zlib.decompress(raw_chunk_data)
            else:
                chunk_data = raw_chunk_data

            data_buffer = io.BytesIO(chunk_data)
            tagReader = TagReader(data_buffer)
            root = tagReader.readTag()
            self.chunks.append((ch, root))
