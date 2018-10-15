from PIL import Image, ImageDraw
from AnvilRegion import AnvilRegion
from output import out
import json
import math
import sys

class TileGenerator:
    def __init__(self, config, mask_data, colors, minx, minz, maxx, maxz):
        self.config = config
        self.mask_data = mask_data
        self.world_offset = (minx, minz)
        self.combined_width = maxx - minx
        self.combined_height = maxz - minz
        self.colors = colors

    def get_nibble(self, data, index):
        byte = data[index >> 1]
        #out "nibble(", index, byte, (index % 2), ")",
        if index % 2 == 0:
            return byte & 15
        else:
            return (byte & 240) >> 4
    
    def get_longarray_bits(self, array, bitindex, numbits, debug=False):
        arrayindex = int(bitindex / 64)
        bit = bitindex % 64

        # LongArray uses signed longs, and Python's bitwise operators don't work well with negative numbers,
        # so convert them to unsigned by adding 2^64 (sigh)
        lowlong = array[arrayindex]
        if lowlong < 0:
            lowlong = lowlong + 2**64

        highlong = 0
        if (arrayindex < len(array) - 1):
            highlong = array[arrayindex + 1]
            if highlong < 0:
                highlong = highlong + 2**64
        
        if debug:
            out("\n >> width: %d, index: %d, %d %d" % (numbits, bitindex % 64, array[arrayindex + 1] if arrayindex < len(array) - 1 else 0, array[arrayindex]))
            out("\n  >> %s %s" % ('{:064b}'.format(array[arrayindex + 1] if arrayindex < len(array) - 1 else 0), '{:064b}'.format(array[arrayindex])))
            out("\n  >> %s %s" % ('{:064b}'.format(highlong), '{:064b}'.format(lowlong)))

        mask = '1' * numbits
        n = (lowlong >> bit) & int(mask, 2)
        if bit + numbits > 64:
            mask = '1' * (bit + numbits - 64)
            n += (highlong & int(mask, 2)) << (numbits - len(mask))
        
        if debug:
            out("\n  >> %s > %d" % (('{:0%db}' % numbits).format(n), n))
        return n
    
    def isAir(self, blockname):
        return blockname in ['minecraft:air','minecraft:cave_air','minecraft:void_air','minecraft:ladder']
    
    def isWater(self, blockname):
        return blockname in ['minecraft:water','minecraft:flowing_water']
    
    def isFlat(self, blockname):
        blockname = blockname.replace('minecraft:', '')
        flatblocks = [
            'oak_sapling','spruce_sapling','birch_sapling','jungle_sapling','acacia_sapling','dark_oak_sapling','grass',
            'sunflower','lilac','rose_bush','peony','tall_grass','large_fern','dandelion','poppy','blue_orchid','allium',
            'azure_bluet','red_tulip','orange_tulip','white_tulip','pink_tulip','oxeye_daisy','fern','dead_bush',
            'brown_mushroom','red_mushroom','snow','white_carpet','orange_carpet','magenta_carpet','light_blue_carpet',
            'yellow_carpet','lime_carpet','pink_carpet','gray_carpet','light_gray_carpet','cyan_carpet','wheat','carrots',
            'potatoes','nether_wart','beetroots'
        ]
        return blockname in flatblocks

    
    def makeTile(self, region):
        tile_im = Image.new("RGBA", (512,512), color=(0,0,0,0))
        markers = []

        counter = 0
        heights = [None] * (16 * 16 * 32 * 32)

        for ch in region.chunks:
            counter = counter + 1
            if counter % 64 == 0:
                out(".")

            if ch[1] and isinstance(ch[1].value, dict) and ch[1].value and 'Level' in ch[1].value:
                data = ch[1]['Level']
                if self.config['fog'] and data['Status'].value in ['empty','base','carved','liquid_carved']:
                    continue

                worldX = data['xPos'].value * 16
                worldZ = data['zPos'].value * 16

                if 'Sections' in data.value:
                    sections = [None] * 16
                    for s in data.value['Sections'].value:
                        sections[s['Y'].value] = s

                    for x in range(16):
                        for z in range(16):
                            mapX = worldX + x - self.world_offset[0]
                            mapY = worldZ + z - self.world_offset[1]
                            tileX = (worldX % 512) + x
                            tileZ = (worldZ % 512) + z

                            if mapX >= 0 and mapX < self.combined_width and mapY >= 0 and mapY < self.combined_height and (self.mask_data == None or self.mask_data[mapX + (mapY * self.combined_width)] != 0):
                                h = 256

                                # TODO should be able to make it run faster using Heightmaps but... this doesn't seem to work
                                # if 'WORLD_SURFACE' in data['Heightmaps'].value:
                                #     h = data['Heightmaps']['WORLD_SURFACE'][x + z * 16] or 256
                                # if h == 256 and 'WORLD_SURFACE_WG' in data['Heightmaps'].value:
                                #     h = data['Heightmaps']['WORLD_SURFACE_WG'][x + z * 16] or 256 # _WG is the World Generation value of the heightmap
                                # h = min(256, h + 2)
                                
                                cl = None
                                water_depth = 0
                                light = 0.5

                                while (cl == None or water_depth > 0) and h >= 0:
                                    h = h - 1
                                    sect = int(h / 16)
                                    if sections[sect]:
                                        pal = sections[sect]['Palette'].value

                                        indexbitsize = max(4, math.ceil(math.log(max(len(pal), 1), 2)))
                                        bitindex = (x + z * 16 + (h % 16) * 256) * indexbitsize
                                        blockIndex = self.get_longarray_bits(sections[sect]['BlockStates'].value, bitindex, indexbitsize)
                                        if blockIndex >= len(pal):
                                            out(" >> (%d, %d, %d), bad block index; %s" % (x, z, h, bin(len(pal))))
                                            self.get_longarray_bits(sections[sect]['BlockStates'].value, bitindex, indexbitsize, True)
                                            out("\n!! block index (%s) out of range (%s) -- %s(bit %s, %s size) !!\n" % (blockIndex, len(pal), bitindex, (bitindex % 64), indexbitsize))
                                            cl = self.colors['name_block']['__UNKNOWN__']
                                            light = 1
                                            break

                                        bl = pal[blockIndex]['Name'].value

                                        if self.isAir(bl):
                                            light = 0.50 + (self.get_nibble(sections[sect]['BlockLight'].value, (x + z * 16 + (h % 16) * 256)) * 0.034)
                                            continue
                                        elif self.isWater(bl):
                                            water_depth += 1
                                        else:
                                            if water_depth > 0:
                                                if water_depth < 12 or (water_depth < 24 and (mapX + mapY) % 2):
                                                    cl = self.colors['water'][0]
                                                else:
                                                    cl = self.colors['water'][1]
                                                water_depth = 0
                                            else:
                                                if bl.replace('minecraft:','') in self.colors['name_block']:
                                                    cl = self.colors['name_block'][bl.replace('minecraft:','')]
                                                else:
                                                    out("!! unrecognized block type %s\n" % (bl))
                                                    cl = self.colors['name_block']['__UNKNOWN__']
                                                    light = 1

                                        # plants, snow layer, and carpet should count as a block lower
                                        if self.isFlat(bl):
                                            h = h - 1
                                        heights[tileX * 512 + tileZ] = h

                                    if h < 0:
                                        # out("!!" + str(x) + "," + str(z) + "!!")
                                        pass
                                
                                if cl == None:
                                    continue

                                if tileZ > 0 and heights[tileX * 512 + (tileZ - 1)] and heights[tileX * 512 + (tileZ - 1)] > h:
                                    color = self.colors['palette_dark'][cl]
                                elif tileZ > 0 and heights[tileX * 512 + (tileZ - 1)] and heights[tileX * 512 + (tileZ - 1)] < h:
                                    color = self.colors['palette_bright'][cl]
                                else:
                                    color = self.colors['palette'][cl]

                                if self.config['fog'] and data['Status'].value != 'postprocessed':
                                    if data['Status'].value in ['decorated', 'lighted', 'mobs_spawned', 'finalized', 'fullchunk']:
                                        if (mapX + mapY) % 2:
                                            continue
                                tile_im.putpixel((tileX, tileZ), (int(color[0] * light), int(color[1] * light), int(color[2] * light)))

                if 'TileEntities' in data.value and len(data['TileEntities'].value) > 0:
                    for e in data['TileEntities'].value:

                        if e['id'].value == 'minecraft:sign':
                            x = e["x"].value - self.world_offset[0]
                            z = e["z"].value - self.world_offset[1]

                            # strip the " characters off the beginning and end of the string
                            text1 = json.loads(e["Text1"].value)['text']
                            text2 = json.loads(e["Text2"].value)['text']
                            text3 = json.loads(e["Text3"].value)['text']
                            text4 = json.loads(e["Text4"].value)['text']

                            if x > 0 and x < self.combined_width - 1 and z > 0 and z < self.combined_height - 1:
                                label = text2
                                if text3 != "":
                                    label = label + " " + text3
                                if text4 != "" and text4 != text1:
                                    label = label + " " + text4

                                markertype = None

                                if text1 == 'X' or text1 == "x" or text1 == "(X)" or text1 == "(x)":
                                    markertype = 'x'
                                elif text1 == '^^':
                                    markertype = "portal"
                                elif text1 == '(R)':
                                    markertype = "ruins"
                                elif text1 == '(M)':
                                    markertype = "mine"
                                elif text1 == '(K)':
                                    markertype = "keep"
                                elif text1 == '(T)':
                                    markertype = "tower"
                                elif text1 == '(F)':
                                    markertype = "farm"
                                elif text1 == "[*]":
                                    markertype = "square"
                                elif text1 == "(*)":
                                    markertype = "circle"
                                elif text1 == "((*))":
                                    markertype = 'big_circle'
                                else:
                                    pass

                                if markertype != None:
                                    markers.append({"x": e["x"].value, "z": e["z"].value, "type": markertype, "label": label })

        return (tile_im, markers)
