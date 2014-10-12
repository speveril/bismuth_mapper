import sys
import os
import struct
import math
import cStringIO
import gzip
import zlib

# -----------------------------------------------------------------------------------------------------------------

Tag_Type = {
    "TAG_End":0,
    "TAG_Byte":1,
    "TAG_Short":2,
    "TAG_Int":3,
    "TAG_Long":4,
    "TAG_Float":5,
    "TAG_Double":6,
    "TAG_Byte_Array":7,
    "TAG_String":8,
    "TAG_List":9,
    "TAG_Compound":10,
    "TAG_Int_Array":11
}

Tag_Type_Name = [
    "TAG_End", "TAG_Byte", "TAG_Short", "TAG_Int",
    "TAG_Long", "TAG_Float", "TAG_Double", "TAG_Byte_Array",
    "TAG_String", "TAG_List", "TAG_Compound", "TAG_Int_Array"
]

# -----------------------------------------------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------------------------------------------

class AnvilRegion:
    def __init__(self, path, no_read=False):
        self.path = path
        self.file = open(path, "rb")
        self.chunks = []

        if not no_read:
            self.read()

    def read(self):
        #print "Loading anvil region " + self.path
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

            #print "-- CHUNK -- (type:" + str(raw_chunk_type) + "," + str(ch) + ") --"
            if raw_chunk_type > 0:
                chunk_data = zlib.decompress(raw_chunk_data)
            else:
                chunk_data = raw_chunk_data

            data_buffer = cStringIO.StringIO(chunk_data)
            tagReader = TagReader(data_buffer)
            root = tagReader.readTag()
            self.chunks.append((ch, root))

# -----------------------------------------------------------------------------------------------------------------

class Tag:
    def __init__(self, name="", type=0, value=0):
        self.name = name
        self.type = type
        self.value = value

    def __getitem__(self, key):
        if self.type == Tag_Type['TAG_Compound'] or self.type == Tag_Type['TAG_List'] or self.type == Tag_Type['TAG_Byte_Array'] or self.type == Tag_Type['TAG_Int_Array']:
            if key in self.value:
                return self.value[key]
        return None

    def is_type(self, type_key):
        if type(type_key) == type([]):
            for k in type_key:
                if self.type == Tag_Type[k]:
                    return True
            return False
        else:
            return self.type == Tag_Type[type_key]

    def pretty_print(self, indent=0):
        if self.type == 0:
            return

        elif self.is_type(['TAG_Byte','TAG_Short','TAG_Int','TAG_Long','TAG_Float','TAG_Double','TAG_String']):
            print (" " * indent) + "[" + Tag_Type_Name[self.type] + "] " + str(self.name) + ": " + str(self.value)

        elif self.is_type(['TAG_List','TAG_Byte_Array','TAG_Int_Array']):
            print (" " * indent) + "[" + Tag_Type_Name[self.type] + "] " + str(self.name) + ": " + str(self.value)

        elif self.is_type('TAG_Compound'):
            print (" " * indent) + "[" + Tag_Type_Name[self.type] + "] " + str(self.name) + ": "
            for t in self.value:
                self[t].pretty_print(indent=indent + 2)

        else:
            print (" " * indent) + "[" + Tag_Type_Name[self.type] + "] " + str(self.name)

# -----------------------------------------------------------------------------------------------------------------

class TagReader:
    def __init__(self, openedFile):
        self.file = openedFile

    def readTag(self, force_type=None, no_name=False):
        tag = None

        type = force_type
        if not type:
            type = self.readByte()

        name = None
        value = None

        if type != Tag_Type['TAG_End'] and not no_name:
            name = self.readString()

        if type == Tag_Type['TAG_Compound']:
            value = {}
            while True:
                subtag = self.readTag()
                if subtag.is_type('TAG_End'):
                    break
                value[subtag.name] = subtag

        elif type == Tag_Type['TAG_Byte_Array']:
            value = []
            count = self.readInt()
            value = struct.unpack(">" + str(count) + "b",self.file.read(count*1))

        elif type == Tag_Type['TAG_Int_Array']:
            count = self.readInt()
            value = struct.unpack(">" + str(count) + "i",self.file.read(count*4))

        elif type == Tag_Type['TAG_Byte']:
            value = self.readByte()

        elif type == Tag_Type['TAG_Short']:
            value = self.readShort()

        elif type == Tag_Type['TAG_Int']:
            value = self.readInt()

        elif type == Tag_Type['TAG_Long']:
            value = self.readLong()

        elif type == Tag_Type['TAG_Float']:
            value = self.readFloat()

        elif type == Tag_Type['TAG_Double']:
            value = self.readDouble()

        elif type == Tag_Type['TAG_String']:
            value = self.readString()

        elif type == Tag_Type['TAG_List']:
            inner_type = self.readByte()
            count = self.readInt()
            value = []
            for i in range(0, count):
                value.append(self.readTag(force_type=inner_type, no_name=True))

        elif type == Tag_Type['TAG_End']:
            pass

        else:
            print "BAD TAG TYPE: " + str(type)
            exit

        return Tag(name=name, type=type, value=value)

    def readByte(self):
        return struct.unpack('B',self.file.read(1))[0]

    def readShort(self):
        return struct.unpack('>h',self.file.read(2))[0]

    def readInt(self):
        return struct.unpack('>i',self.file.read(4))[0]

    def readLong(self):
        return struct.unpack('>q',self.file.read(8))[0]

    def readFloat(self):
        return struct.unpack('>f',self.file.read(4))[0]

    def readDouble(self):
        return struct.unpack('>d',self.file.read(8))[0]

    def readString(self):
        length = struct.unpack('>h',self.file.read(2))[0]
        return self.file.read(length)

# -----------------------------------------------------------------------------------------------------------------
