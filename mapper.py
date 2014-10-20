import sys
import os
import json
from PIL import Image, ImageDraw
from MCMap import MCMap
from AnvilRegion import AnvilRegion
from TileGenerator import TileGenerator
from output import out

def get_maps(path):
    min_x = None
    min_z = None
    max_x = None
    max_z = None

    map_files = os.listdir(path)
    maps = []
    for filename in map_files:
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
    out("Loaded " + str(len(maps)) + " maps.\n")
    return (min_x, min_z, max_x, max_z, maps)

def make_colors():
    colors = {}

    colors['actual'] = [
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

    colors['dark'] = []
    colors['bright'] = []

    for c in colors['actual']:
        d = (int(c[0] * 0.75), int(c[1] * 0.75), int(c[2] * 0.75))
        colors['dark'].append(d)
        b = (min(255,int(c[0] * 1.2)), min(255,int(c[1] * 1.2)), min(255, int(c[2] * 1.2)))
        colors['bright'].append(b)

    # based on table at http://www.minecraftwiki.net/wiki/Block_ids
    colors['block'] = [
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

    colors['tints'] = [
        15,16,17,18, 19,20,21,22, 23,24,25,26, 27,28,29,30
    ]
    colors['water'] = [ 12, 31 ]
    return colors

def build(world_path, output_path):
    (min_x, min_z, max_x, max_z, maps) = get_maps(world_path + "/data/")
    if len(maps) < 1:
        out("No maps to build from.\n")
        return

    combined_width = max_x - min_x
    combined_height = max_z - min_z
    out("Combined map: %d x %d (%d,%d)-(%d,%d)\n" % (combined_width,combined_height,min_x,min_z,max_x,max_z))

    map_data = [0] * (combined_width * combined_height)
    regions_with_data = []

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
                            block_x = x + cx * scale + col
                            block_z = z + cz * scale + row
                            map_data[block_x + block_z * combined_width] = 1
                            # TODO write True into a region look up for "are there pixels here"

        out(".")
    out("\n")

    path = world_path + "/region/"
    region_files = os.listdir(path)
    out(str(len(region_files)) + " regions to check.\n")

    if os.path.exists(output_path + '/tile/markers.json'):
        markers = json.load(open(output_path + '/tile/markers.json'))
        out("Loaded markers.json")
    else:
        markers = {}
        out("Creating markers.json")

    if os.path.exists(output_path + '/tile/tiles.json'):
        tiles = json.load(open(output_path + '/tile/tiles.json'))
        out("Loaded tiles.json")
    else:
        tiles = {}
        out("Creating tiles.json")

    # TODO start using a hints.json which stores whatever; specifically I can start
    # storing the southern edge of height maps so I can calculate the shading
    # on the next tile to the south
    hints = []

    # assumes at most 10000 regions square; that's an area of roughly 5120 km to a side so
    # it's probably okay for most worlds
    # TODO this sorting actually doesn't really work; it reverses negative y
    region_files.sort(key=lambda x: int(x.split(".")[1]) + float(x.split(".")[2]) / 10000)
    out("Region files sorted.\n")

    tile_generator = TileGenerator(map_data, make_colors(), min_x, min_z, max_x, max_z)

    for f in region_files:
        out("  " + f + ": ")

        f_parts = f.split(".")
        tx = f_parts[1]
        ty = f_parts[2]
        output_f = output_path + "/tile/tile." + tx + "." + ty + ".png"
        tiles[f] = { 'src':"tile/tile." + tx + "." + ty + ".png", 'x':int(tx)*512, 'y':int(ty)*512 }

        if int(tx) * 512 > max_x or int(ty) * 512 > max_z or (int(tx) + 1) * 512 < min_x or (int(ty) + 1) * 512 < min_z:
            out(" Region is entirely outside of mapped area. Skipping.\n")
            continue

        if (os.path.exists(output_f) and os.path.getmtime(output_f) > os.path.getmtime(path + f)):
            out(" Tile exists and is newer than the region file. Skipping.\n")
            continue

        region = AnvilRegion(path + f)

        out(" " + str(len(region.chunks)) + " chunks loaded");

        (tile_im, m) = tile_generator.makeTile(region)

        markers[f] = m
        tile_im.save(output_f)

        out("\n")

    f = open(output_path + "/tile/markers.json", "w")
    json.dump(markers, f)
    out("Wrote markers.json\n")

    f = open(output_path + "/tile/tiles.json", "w")
    json.dump(tiles, f)
    out("Wrote tiles.json\n")

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
