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
    colors = json.load(open('colors.json'))
    colors['dark'] = []
    colors['bright'] = []

    for c in colors['actual']:
        if len(c) < 1: # skip placeholders
            colors['bright'].append([])
            colors['dark'].append([])
            continue

        d = (int(c[0] * 0.75), int(c[1] * 0.75), int(c[2] * 0.75))
        colors['dark'].append(d)
        b = (min(255,int(c[0] * 1.2)), min(255,int(c[1] * 1.2)), min(255, int(c[2] * 1.2)))
        colors['bright'].append(b)

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
        out("Loaded markers.json\n")
    else:
        markers = {}
        out("Creating markers.json\n")

    if os.path.exists(output_path + '/tile/tiles.json'):
        tiles = json.load(open(output_path + '/tile/tiles.json'))
        out("Loaded tiles.json\n")
    else:
        tiles = {}
        out("Creating tiles.json\n")

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
