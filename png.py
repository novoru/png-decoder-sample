"""
   PNG decoder sample
   :copyright: (c) 2014 by Noboru HORITA.

"""

import math
import struct
import zlib

from PIL import Image

# Filter Types
NONE    = 0
SUB     = 1
UP      = 2 
AVERAGE = 3
PAETH   = 4

class PNG:

    def __init__(self, fileName):
        self.f = open(fileName)
    
        self.fs = self.f.read(8)
    
        self.chunks = {}
    
        while True:
            chunk = {}
            chunk["length"] = struct.unpack(">i", self.f.read(4))[0]
            chunk["name"]   = self.f.read(4)
            chunk["data"]   = self.f.read(chunk["length"])

            if chunk["name"] == "IHDR":
                temp = struct.unpack(">IIBBBBB", chunk["data"])
                chunk["width"]       = temp[0]
                chunk["height"]      = temp[1]
                chunk["bitdepth"]    = temp[2]
                chunk["colortype"]   = temp[3]
                chunk["compression"] = temp[4]
                chunk["filter"]      = temp[5]
                chunk["interlace"]   = temp[6]
            
            chunk["crc"]    = self.f.read(4)

            self.chunks[chunk["name"]] = chunk
        
            if chunk["name"] == "IEND":
                break

        self.nSample       = 0
        
        # Gray scale
        if self.chunks["IHDR"]["colortype"] == 0:
            self.nSample = 1
        # RGB color
        elif self.chunks["IHDR"]["colortype"] == 2:
            self.nSample = 3
        # Palette index
        # TODO
        elif self.chunks["IHDR"]["colortype"] == 3:
            pass
        # Gray scale sample + alpha channel
        elif self.chunks["IHDR"]["colortype"] == 4:
            self.nSample = 2
        # RGB color + alpha channel
        elif self.chunks["IHDR"]["colortype"] == 6:
            self.nSample = 4

        self.bytePerSample = self.chunks["IHDR"]["bitdepth"] / 8

            
    def decompress(self):
        _deflateDecomp = zlib.decompress(self.chunks["IDAT"]["data"])
        fc = '>' + 'B'*len(_deflateDecomp)
        deflateDecomp  = list(struct.unpack(fc, _deflateDecomp))

        bpp = self.nSample * self.bytePerSample
        filterTypes = []

        for i in range(self.chunks["IHDR"]["height"]):
            filterTypes.insert(0, deflateDecomp.pop((self.chunks["IHDR"]["height"]-1-i)*(1+(self.chunks["IHDR"]["width"]*self.nSample))))

        raw = []

        for i, filterType in enumerate(filterTypes):
            if filterType == NONE:
                for j in range(i*self.chunks["IHDR"]["width"]*self.nSample, (i+1)*self.chunks["IHDR"]["width"]*self.nSample):
                    raw.append(deflateDecomp[j])
            elif filterType == SUB:
                for j in range(i*self.chunks["IHDR"]["width"]*self.nSample, (i+1)*self.chunks["IHDR"]["width"]*self.nSample):
                    left = 0
                    if (j - i*self.chunks["IHDR"]["width"]*self.nSample - bpp) < 0:
                        pass
                    else:
                        left = raw[j-bpp]
                    raw.append((deflateDecomp[j]+left)%256)

            elif filterType == UP:
                for j in range(i*self.chunks["IHDR"]["width"]*self.nSample, (i+1)*self.chunks["IHDR"]["width"]*self.nSample):
                    above = 0 
                    if i == 0:
                        pass
                    else:
                        above = raw[j-self.chunks["IHDR"]["width"]*self.nSample]
                    raw.append((deflateDecomp[j]+above)%256)

            elif filterType == AVERAGE:
                for j in range(i*self.chunks["IHDR"]["width"]*self.nSample, (i+1)*self.chunks["IHDR"]["width"]*self.nSample):
                    left = 0
                    if (j - i*self.chunks["IHDR"]["width"]*self.nSample - bpp) < 0:
                        pass
                    else:
                        left = raw[j-bpp]

                    above = 0
                    if i == 0:
                        pass
                    else:
                        above = raw[j-self.chunks["IHDR"]["width"]*self.nSample]
                    raw.append(int((deflateDecomp[j]+math.floor((left+above)/2))%256))

            elif filterType == PAETH:
                for j in range(i*self.chunks["IHDR"]["width"]*self.nSample, (i+1)*self.chunks["IHDR"]["width"]*self.nSample):
                    left = 0
                    if (j - i*self.chunks["IHDR"]["width"]*self.nSample - bpp) < 0:
                        pass
                    else:
                        left = raw[j-bpp]

                    above = 0
                    if i == 0:
                        pass
                    else:
                        above = raw[j-self.chunks["IHDR"]["width"]*self.nSample]

                    upperLeft = 0
                    if ((j - i*self.chunks["IHDR"]["width"]*self.nSample - bpp) < 0) | (i == 0):
                        pass
                    else:
                        upperLeft = raw[j-self.chunks["IHDR"]["width"]*self.nSample-bpp]
                        
                    raw.append((deflateDecomp[j]+self.paethPredictor(left, above, upperLeft))%256)
                        
        return raw


    def paethPredictor(self, a, b, c):
        p = a + b - c
        pa = abs(p - a)
        pb = abs(p - b)
        pc = abs(p - c)
        if (pa <= pb) & (pa <= pc):
            return a
        elif (pb <= pc):
            return b
        else:
            return c


    def __del__(self):
        self.f.close()


if __name__ == "__main__":
    fileName = "lena" + ".png"
    png = PNG(fileName)
    pixels = png.decompress()
    colorType = ""

    if png.chunks["IHDR"]["colortype"] == 0:
        colorType = "L"
    elif png.chunks["IHDR"]["colortype"] == 2:
        colorType = "RGB"
    # TODO
    elif png.chunks["IHDR"]["colortype"] == 3:
        pass
    # TODO
    elif png.chunks["IHDR"]["colortype"] == 4:
        pass
    elif png.chunks["IHDR"]["colortype"] == 6:
        colorType = "RGBA"

    img = Image.new(colorType, (png.chunks["IHDR"]["width"], png.chunks["IHDR"]["height"]))

    for row in range(png.chunks["IHDR"]["height"]):
        for column in range(png.chunks["IHDR"]["width"]):
            colors = []
            for i in range(len(colorType)):
                colors.append(pixels[row*png.chunks["IHDR"]["width"]*png.nSample + column*png.nSample + i])
            if colorType == "L":
                color = colors[0]
            else:
                color = tuple(colors)
            img.putpixel((column, row), color)
    img.show()
