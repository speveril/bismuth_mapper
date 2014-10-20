from PIL import Image, ImageDraw
from AnvilRegion import AnvilRegion
from output import out

class TileGenerator:
    def __init__(self, mask_data, colors, minx, minz, maxx, maxz):
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

                worldX = data['xPos'].value * 16
                worldZ = data['zPos'].value * 16

                if 'Sections' in data.value and 'HeightMap' in data.value:
                    sections = [None] * 16
                    for s in data['Sections'].value:
                        sections[s['Y'].value] = s

                    for x in range(16):
                        for z in range(16):
                            mapX = worldX + x - self.world_offset[0]
                            mapY = worldZ + z - self.world_offset[1]
                            tileX = (worldX % 512) + x
                            tileZ = (worldZ % 512) + z

                            if mapX >= 0 and mapX < self.combined_width and mapY >= 0 and mapY < self.combined_height and self.mask_data[mapX + (mapY * self.combined_width)] != 0:
                                h = data['HeightMap'].value[x + z * 16] + 1
                                cl = 0
                                water_depth = 0
                                while (cl == 0 or water_depth > 0) and h >= 0:
                                    h = h - 1
                                    sect = int(h/16)
                                    if sections[sect]:
                                        blockIndex = x + z * 16 + (h % 16) * 256

                                        bl = sections[sect]['Blocks'].value[blockIndex]

                                        if sections[sect]['Add'] != None:
                                            addValue = self.get_nibble(sections[sect]['Add'].value, blockIndex)
                                            bl = bl + (addValue << 8)

                                        if bl == 8 or bl == 9: # water handling
                                            water_depth += 1
                                        else:
                                            if water_depth > 0:
                                                if water_depth < 12 or (water_depth < 24 and (mapX + mapY) % 2):
                                                    cl = self.colors['water'][0]
                                                else:
                                                    cl = self.colors['water'][1]
                                                water_depth = 0
                                            elif bl == 35 or bl == 159 or bl == 172: # coloured blocks
                                                dataValue = self.get_nibble(sections[sect]['Data'].value, blockIndex)
                                                cl = self.colors['tints'][dataValue]
                                            else:
                                                cl = self.colors['block'][bl]

                                        if not bl:
                                            light = 0.50 + (self.get_nibble(sections[sect]['BlockLight'].value, blockIndex) * 0.034)

                                        if bl in [31,32,37,38,39,40,78]:
                                            h = h - 1
                                        heights[tileX * 512 + tileZ] = h

                                    if h == 0 and cl == 0:
                                        out("!!" + str(x) + "," + str(z) + "!!")

                                color = self.colors['actual'][cl]

                                if tileZ > 0 and heights[tileX * 512 + (tileZ - 1)] and heights[tileX * 512 + (tileZ - 1)] > h:
                                    color = self.colors['dark'][cl]
                                elif tileZ > 0 and heights[tileX * 512 + (tileZ - 1)] and heights[tileX * 512 + (tileZ - 1)] < h:
                                    color = self.colors['bright'][cl]

                                tile_im.putpixel((tileX, tileZ), (int(color[0] * light), int(color[1] * light), int(color[2] * light)))

                if 'TileEntities' in data.value and len(data['TileEntities'].value) > 0:
                    for e in data['TileEntities'].value:
                        if e['id'].value == 'Sign':
                            x = e["x"].value - self.world_offset[0]
                            z = e["z"].value - self.world_offset[1]

                            # strip the " characters off the beginning and end of the string
                            text1 = e["Text1"].value[1:-1]
                            text2 = e["Text2"].value[1:-1]
                            text3 = e["Text3"].value[1:-1]
                            text4 = e["Text4"].value[1:-1]

                            if x > 0 and x < self.combined_width - 1 and z > 0 and z < self.combined_height - 1:
                                if text1 == 'X' or text1 == "x" or text1 == "(X)" or text1 == "(x)":
                                    label = text2
                                    if text3 != "":
                                        label = label + " " + text3
                                    if text4 != "" and text4 != text1:
                                        label = label + " " + text4
                                    markers.append({"x": e["x"].value, "z": e["z"].value, "type": "x", "label": label })
                                elif text1 == '^^':
                                    label = text2
                                    if text3 != "":
                                        label = label + " " + text3
                                    if text4 != "" and text4 != text1:
                                        label = label + " " + text4
                                    markers.append({"x": e["x"].value, "z": e["z"].value, "type": "portal", "label": label })
                                elif text1 == '(R)':
                                    label = text2
                                    if text3 != "":
                                        label = label + " " + text3
                                    if text4 != "" and text4 != text1:
                                        label = label + " " + text4
                                    markers.append({"x": e["x"].value, "z": e["z"].value, "type": "ruins", "label": label })
                                elif text1 == '(M)':
                                    label = text2
                                    if text3 != "":
                                        label = label + " " + text3
                                    if text4 != "" and text4 != text1:
                                        label = label + " " + text4
                                    markers.append({"x": e["x"].value, "z": e["z"].value, "type": "mine", "label": label })
                                elif text1 == '(K)':
                                    label = text2
                                    if text3 != "":
                                        label = label + " " + text3
                                    if text4 != "" and text4 != text1:
                                        label = label + " " + text4
                                    markers.append({"x": e["x"].value, "z": e["z"].value, "type": "keep", "label": label })
                                elif text1 == '(T)':
                                    label = text2
                                    if text3 != "":
                                        label = label + " " + text3
                                    if text4 != "" and text4 != text1:
                                        label = label + " " + text4
                                    markers.append({"x": e["x"].value, "z": e["z"].value, "type": "tower", "label": label })
                                elif text1 == '(F)':
                                    label = text2
                                    if text3 != "":
                                        label = label + " " + text3
                                    if text4 != "" and text4 != text1:
                                        label = label + " " + text4
                                    markers.append({"x": e["x"].value, "z": e["z"].value, "type": "farm", "label": label })
                                elif text1 == "[*]":
                                    label = text2
                                    if text3 != "":
                                        label = label + " " + text3
                                    if text4 != "" and text4 != text1:
                                        label = label + " " + text4
                                    markers.append({"x": e["x"].value, "z": e["z"].value, "type": "square", "label": label })
                                elif text1 == "(*)":
                                    label = text2
                                    if text3 != "":
                                        label = label + " " + text3
                                    if text4 != "" and text4 != text1:
                                        label = label + " " + text4
                                    markers.append({"x": e["x"].value, "z": e["z"].value, "type": "circle", "label": label })
                                elif text1 == "((*))":
                                    label = text2
                                    if text3 != "":
                                        label = label + " " + text3
                                    if text4 != "" and text4 != text1:
                                        label = label + " " + text4
                                    markers.append({"x": e["x"].value, "z": e["z"].value, "type": "big_circle", "label": label })
                                else:
                                    pass
        return (tile_im, markers)
