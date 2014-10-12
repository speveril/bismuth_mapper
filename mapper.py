import sys
import os
import struct
import math
import cStringIO
import json
from PIL import Image, ImageDraw
from MCMap import MCMap, AnvilRegion

def get_nibble(data, index):
    byte = data[index >> 1]
    #print "nibble(", index, byte, (index % 2), ")",
    if index % 2 == 0:
        return byte & 15
    else:
        return (byte & 240) >> 4

path = sys.argv[1] + "/data/"
output_path = sys.argv[2]

maps = []

file_list = os.listdir(path)

min_x = None
min_z = None
max_x = None
max_z = None

for filename in file_list:
    if filename.find("map_") == 0:
        map = MCMap(path + filename)

        scale = 2 ** map.scale;
        real_width = map.width * scale
        real_height = map.height * scale

        left = map.xCenter - (real_width / 2)
        top = map.zCenter - (real_height / 2)
        right = map.xCenter + (real_width / 2)
        bottom = map.zCenter + (real_height / 2)

        if min_x is None or left < min_x:
            min_x = left
        if min_z is None or top < min_z:
            min_z = top
        if max_x is None or right > max_x:
            max_x = right
        if max_z is None or bottom > max_z:
            max_z = bottom

        maps.append(map)

print "Loaded " + str(len(maps)) + " maps."

combined_width = max_x - min_x
combined_height = max_z - min_z
print "Combined map: %d x %d (%d,%d)-(%d,%d)" % (combined_width,combined_height,min_x,min_z,max_x,max_z)

combined_colors = []
for i in range(0, combined_width*combined_height):
    combined_colors.append(0)

# from http://www.minecraftwiki.net/wiki/Map_Item_Format
color_map = [
    '\x00\x00\x00\x00','\x00\x00\x00\x00','\x00\x00\x00\x00','\x00\x00\x00\x00',
    '\x59\x7d\x27\xff','\x6d\x99\x30\xff','\x1b\xb2\x38\xff','\x6d\x99\x30\xff',
    '\xae\xa4\x73\xff','\xd5\xc9\x8c\xff','\xf7\xe9\xa3\xff','\xd5\xc9\x8c\xff',
    '\x75\x75\x75\xff','\x90\x90\x90\xff','\xa7\xa7\xa7\xff','\x90\x90\x90\xff',
    '\xb4\x00\x00\xff','\xdc\x00\x00\xff','\xff\x00\x00\xff','\xdc\x00\x00\xff',
    '\x70\x70\xb4\xff','\x8a\x8a\xdc\xff','\xa0\xa0\xff\xff','\x8a\x8a\xdc\xff',
    '\x75\x75\x75\xff','\x90\x90\x90\xff','\xa7\xa7\xa7\xff','\x90\x90\x90\xff',
    '\x00\x57\x00\xff','\x00\x6a\x00\xff','\x00\x7c\x00\xff','\x00\x6a\x00\xff',
    '\xb4\xb4\xb4\xff','\xdc\xdc\xdc\xff','\xff\xff\xff\xff','\xdc\xdc\xdc\xff',
    '\x73\x76\x81\xff','\x8d\x90\x9e\xff','\xa4\xa8\xb8\xff','\x8d\x90\x9e\xff',
    '\x81\x4a\x21\xff','\x9d\x5b\x28\xff','\xb7\x6a\x2f\xff','\x9d\x5b\x28\xff',
    '\x4f\x4f\x4f\xff','\x60\x60\x60\xff','\x70\x70\x70\xff','\x60\x60\x60\xff',
    '\x2d\x2d\xb4\xff','\x37\x37\xdc\xff','\x40\x40\xff\xff','\x37\x37\xdc\xff',
    '\x49\x3a\x23\xff','\x59\x47\x2b\xff','\x68\x53\x32\xff','\x59\x47\x2b\xff',
    '\xff\x00\xff\xff','\xff\x00\xff\xff','\xff\x00\xff\xff','\xff\x00\xff\xff'
]

actual_colors = [
    (255,255,255), #transparent
    (127,178,56), #grass green
    (247,233,163), #sand,gravel
    (167,167,167), #sponge,bed,cobweb,(wool)
    (255,  0,  0), #lava,tnt
    (160,160,255), #ice
    (167,167,167), #blocks of metal
    (  0,124,  0), #plants
    (240,240,240), #snow
    (164,168,184), #clay
    (183,106, 47), #dirt
    (112,112,112), #stone,etc
    ( 64, 64,255), #water
    (104, 83, 50), #wood stuff
    (255,  0,255), #other???

    (221,221,221), # white wool
    (219,125, 62), # orange
    (179, 80,188), # purple
    (107,138,201), # blue
    (177,166, 39), # yellow
    ( 65,174, 56), # green
    (208,132,153), # pink
    ( 64, 64, 64), # dark grey
    (154,161,161), # grey
    ( 46,110,137), # teal
    (126, 61,181), # dark purple
    ( 46, 56,141), # dark blue
    ( 79, 50, 31), # brown
    ( 53, 70, 27), # dark green
    (150, 52, 48), # red
    ( 25, 22, 22), # black

    ( 32, 32,196), # deep water
]

dark_colors = []
bright_colors = []

for c in actual_colors:
    d = (int(c[0] * 0.75), int(c[1] * 0.75), int(c[2] * 0.75))
    dark_colors.append(d)
    b = (min(255,int(c[0] * 1.2)), min(255,int(c[1] * 1.2)), min(255, int(c[2] * 1.2)))
    bright_colors.append(b)

# based on table at http://www.minecraftwiki.net/wiki/Block_ids
block_colors = [
     0,11, 1,10,11,13, 7,11,12,12, 4, 4, 2, 2,11,11, # 0-15
    11,13, 7, 3, 0,11,12,11,11,13, 3, 0, 0,11, 3, 7, # 16-31
     7,11,11, 3,11, 7, 7, 7, 7, 6, 6,11,11,11, 4,13, # 32-47
    11,11, 0, 0, 0,13,13, 0,11, 6,13, 7,10,11,11,13, # 48-63
    13, 0, 0,11,13, 0,11, 6,13,11,11, 0, 0, 0, 8, 5, # 64-79
     8, 7, 9, 7,13,13, 7,11, 2, 0, 0, 7, 0, 0, 0,13, # 80-95
    13, 9,11,13,13, 6, 0, 7, 7, 7, 7,13,11,11, 1,11, # 96-111
    11,11,11, 7,11, 6, 6, 0, 0,11, 7, 0, 0,13,13, 7, # 112-127
    11,11,13, 0, 0, 6,13,13,13,13, 0,11, 7, 7, 7,13, # 128-143
     0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, # 144-159
     0, 7,13, 0, 0, 0, 0, 0, 0, 0, 0, 1,10, 0, 0, 0, # 160-175
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 176-191
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 192-207
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 208-223
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 224-239
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 240-255
]

wool_colors = [
    15,16,17,18, 19,20,21,22, 23,24,25,26, 27,28,29,30
]
water_colors = [ 12, 31 ]

for map in maps:
    scale = 2 ** map.scale
    x = map.xCenter - (map.width * scale / 2) - min_x
    z = map.zCenter - (map.height * scale / 2) - min_z

    for cz in range(0, map.height):
        for cx in range(0, map.width):
            c = map.colors[cx + cz * map.width] #color_map[map.colors[cx + cz * map.width]]
            if c > 3:
                for row in range(0,scale):
                    for col in range(0,scale):
                        combined_colors[(x + col + cx * scale) + (z + row + cz * scale) * combined_width] = map.colors[cx + cz * map.width]
                        # TODO write True into a region look up for "are there pixels here"

pixels = ""
line = ""
for i in range(0, len(combined_colors)):
    if (combined_colors[i] < 4):
        line = line + "\x00\x00\x00\x00"
    else:
        line = line + "\xff\xff\xff\xff"
    #line = line + color_map[combined_colors[i]]
    if len(line) >= combined_width * 4:
        pixels = pixels + line
        line = ""
im = Image.frombuffer("RGBA", (combined_width,combined_height), pixels, "raw", "RGBA", 0, 1)
#im.save(output_path + "/stitched.png")


path = sys.argv[1] + "/region/"
file_list = os.listdir(path)

print str(len(file_list)) + " regions to check."

full_trans = Image.new('L', im.size, color=0)

over_icons = Image.new("RGBA", im.size)
over_icons.putalpha(full_trans)
over_labels = Image.new("RGBA", im.size)
over_labels.putalpha(full_trans)

draw_icons = ImageDraw.ImageDraw(over_icons)
draw_labels = ImageDraw.ImageDraw(over_labels)

worldOffset = (min_x, min_z)

# todo: check if file exists and create it if not
jsondata = open(output_path + '/markers.json')
markers = json.load(jsondata)

## todo: start using a hints.json which stores whatever; specifically I can start
##             storing the southern edge of height maps so I can calculate the shading
##             on the next tile to the south
hints = []

# assumes at most 10000 regions square; that's an area of roughly 5120 km to a side so
# it's probably okay for most worlds
file_list.sort(key=lambda x: int(x.split(".")[1]) + float(x.split(".")[2]) / 10000)

for f in file_list:
    sys.stdout.write("Loading " + f + "...")
    sys.stdout.flush()

    f_parts = f.split(".")
    tx = f_parts[1]
    ty = f_parts[2]
    output_f = output_path + "/tile." + tx + "." + ty + ".png"

    if int(tx) * 512 > max_x or int(ty) * 512 > max_z or (int(tx) + 1) * 512 < min_x or (int(ty) + 1) * 512 < min_z:
        sys.stdout.write(" Region is entirely outside of mapped area. Skipping.\n")
        sys.stdout.flush()
        continue

    if (os.path.exists(output_f) and os.path.getmtime(output_f) > os.path.getmtime(path + f)):
        sys.stdout.write(" Tile exists and is newer than the region file. Skipping.\n")
        sys.stdout.flush()
        continue

    markers[f] = []
    region = AnvilRegion(path + f)

    sys.stdout.write(" " + str(len(region.chunks)) + " chunks loaded.");
    sys.stdout.flush()

    tile_im = Image.new("RGBA", (512,512), color=(0,0,0,0))

    counter = 0
    heights = [None] * (16 * 16 * 32 * 32)

    for ch in region.chunks:
        counter = counter + 1
        if (counter - 1) % 64 == 0:
            sys.stdout.write(".")
            sys.stdout.flush()

        if ch[1] and isinstance(ch[1].value, dict) and ch[1].value and 'Level' in ch[1].value:
            data = ch[1]['Level']

            worldX = data['xPos'].value * 16
            worldZ = data['zPos'].value * 16

            if 'Sections' in data.value and 'HeightMap' in data.value:
                sections = []

                for s in range(16):
                    sections.append(None)
                for s in data['Sections'].value:
                    sections[s['Y'].value] = s
                for x in range(16):
                    for z in range(16):
                        mapX = worldX + x - worldOffset[0]
                        mapY = worldZ + z - worldOffset[1]
                        tileX = (worldX % 512) + x
                        tileZ = (worldZ % 512) + z

                        if mapX >= 0 and mapX < combined_width and mapY >= 0 and mapY < combined_height and combined_colors[mapX + (mapY * combined_width)] != 0:
                            h = 256 # TODO replace with heightmap look up?
                            cl = 0
                            water_depth = 0
                            while (cl == 0 or water_depth > 0) and h >= 0:
                                h = h - 1
                                sect = int(h/16)
                                if sections[sect]:
                                    blockIndex = x + z * 16 + (h % 16) * 256

                                    bl = sections[sect]['Blocks'].value[blockIndex]

                                    if sections[sect]['Add'] != None:
                                        addValue = get_nibble(sections[sect]['Add'].value, blockIndex)
                                        bl = bl + (addValue << 8)

                                    if bl == 8 or bl == 9: # water handling
                                        water_depth += 1
                                    else:
                                        if water_depth > 0:
                                            if water_depth < 12 or (water_depth < 24 and (mapX + mapY) % 2):
                                                cl = water_colors[0]
                                            else:
                                                cl = water_colors[1]
                                            water_depth = 0
                                        elif bl == 35 or bl == 159 or bl == 172: # coloured blocks
                                            dataValue = get_nibble(sections[sect]['Data'].value, blockIndex)
                                            cl = wool_colors[dataValue]
                                        else:
                                            cl = block_colors[bl]

                                    if not bl:
                                        light = 0.50 + (get_nibble(sections[sect]['BlockLight'].value, blockIndex) * 0.034)

                                    if bl in [31,32,37,38,39,40,78]:
                                        h = h - 1
                                    heights[tileX * 512 + tileZ] = h

                                if h == 0 and cl == 0:
                                    sys.stdout.write("!!" + str(x) + "," + str(z) + "!!")

                            color = actual_colors[cl]

                            if tileZ > 0 and heights[tileX * 512 + (tileZ - 1)] and heights[tileX * 512 + (tileZ - 1)] > h:
                                color = dark_colors[cl]
                            elif tileZ > 0 and heights[tileX * 512 + (tileZ - 1)] and heights[tileX * 512 + (tileZ - 1)] < h:
                                color = bright_colors[cl]

                            tile_im.putpixel((tileX, tileZ), (int(color[0] * light), int(color[1] * light), int(color[2] * light)))

            if 'TileEntities' in data.value and len(data['TileEntities'].value) > 0:
                for e in data['TileEntities'].value:
                    if e['id'].value == 'Sign':
                        x = e["x"].value - min_x
                        z = e["z"].value - min_z

                        # strip the " characters off the beginning and end of the string
                        text1 = e["Text1"].value[1:-1]
                        text2 = e["Text2"].value[1:-1]
                        text3 = e["Text3"].value[1:-1]
                        text4 = e["Text4"].value[1:-1]

                        if x > 0 and x < combined_width - 1 and z > 0 and z < combined_height - 1:
                            if text1 == 'X' or text1 == "x" or text1 == "(X)" or text1 == "(x)":
                                label = text2
                                if text3 != "":
                                    label = label + " " + text3
                                if text4 != "" and text4 != text1:
                                    label = label + " " + text4
                                markers[f].append({"x": e["x"].value, "z": e["z"].value, "type": "x", "label": label })
                            elif text1 == '^^':
                                label = text2
                                if text3 != "":
                                    label = label + " " + text3
                                if text4 != "" and text4 != text1:
                                    label = label + " " + text4
                                markers[f].append({"x": e["x"].value, "z": e["z"].value, "type": "portal", "label": label })
                            elif text1 == '(R)':
                                label = text2
                                if text3 != "":
                                    label = label + " " + text3
                                if text4 != "" and text4 != text1:
                                    label = label + " " + text4
                                markers[f].append({"x": e["x"].value, "z": e["z"].value, "type": "ruins", "label": label })
                            elif text1 == '(M)':
                                label = text2
                                if text3 != "":
                                    label = label + " " + text3
                                if text4 != "" and text4 != text1:
                                    label = label + " " + text4
                                markers[f].append({"x": e["x"].value, "z": e["z"].value, "type": "mine", "label": label })
                            elif text1 == '(K)':
                                label = text2
                                if text3 != "":
                                    label = label + " " + text3
                                if text4 != "" and text4 != text1:
                                    label = label + " " + text4
                                markers[f].append({"x": e["x"].value, "z": e["z"].value, "type": "keep", "label": label })
                            elif text1 == '(T)':
                                label = text2
                                if text3 != "":
                                    label = label + " " + text3
                                if text4 != "" and text4 != text1:
                                    label = label + " " + text4
                                markers[f].append({"x": e["x"].value, "z": e["z"].value, "type": "tower", "label": label })
                            elif text1 == '(F)':
                                label = text2
                                if text3 != "":
                                    label = label + " " + text3
                                if text4 != "" and text4 != text1:
                                    label = label + " " + text4
                                markers[f].append({"x": e["x"].value, "z": e["z"].value, "type": "farm", "label": label })
                            elif text1 == "[*]":
                                label = text2
                                if text3 != "":
                                    label = label + " " + text3
                                if text4 != "" and text4 != text1:
                                    label = label + " " + text4
                                markers[f].append({"x": e["x"].value, "z": e["z"].value, "type": "square", "label": label })
                            elif text1 == "(*)":
                                label = text2
                                if text3 != "":
                                    label = label + " " + text3
                                if text4 != "" and text4 != text1:
                                    label = label + " " + text4
                                markers[f].append({"x": e["x"].value, "z": e["z"].value, "type": "circle", "label": label })
                            elif text1 == "((*))":
                                label = text2
                                if text3 != "":
                                    label = label + " " + text3
                                if text4 != "" and text4 != text1:
                                    label = label + " " + text4
                                markers[f].append({"x": e["x"].value, "z": e["z"].value, "type": "big_circle", "label": label })
                            else:
                                pass

    tile_im.save(output_f)

    sys.stdout.write("\n")

#over_icons.save(output_path + "/icons.png")
#over_labels.save(output_path + "/labels.png")
f = open(output_path + "/markers.json", "w")
json.dump(markers, f)
sys.stdout.write("Wrote markers.json\n")
