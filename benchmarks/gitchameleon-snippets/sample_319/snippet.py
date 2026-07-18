import numpy as np
from PIL import Image, ImageChops


def imaging(img1: Image, img2: Image) -> Image:


    def create(imIn1, imIn2, mode=None):
        if imIn1.shape != imIn2.shape:
            return None
        return np.empty_like(imIn1, dtype=np.uint8)

    def imaging_hardlight(imIn1, imIn2):
        imOut = create(imIn1, imIn2)
        if imOut is None:
            return None
        
        ysize, xsize, _ = imOut.shape
        for y in range(ysize):
            for x in range(xsize):
                for c in range(3):  # Loop over RGB channels
                    in1, in2 = int(imIn2[y, x, c]), int(imIn1[y, x, c])
                    if in1 < 128:
                        imOut[y, x, c] = np.clip((in1 * in2) // 127, 0, 255)
                    else:
                        imOut[y, x, c] = np.clip(255 - (((255 - in1) * (255 - in2)) // 127), 0, 255)
        
        return imOut

    return imaging_hardlight(np.array(img1), np.array(img2))

# --- test ---

def generate_random_image(width, height):
    random_data = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    return Image.fromarray(random_data)

np.random.seed(42)

width, height = 8, 8
img1 = generate_random_image(width, height)
img2 = generate_random_image(width, height)



def create(imIn1, imIn2, mode=None):
    if imIn1.shape != imIn2.shape:
        return None
    return np.empty_like(imIn1, dtype=np.uint8)

def imaging_hardlight(imIn1, imIn2):
    imOut = create(imIn1, imIn2)
    if imOut is None:
        return None
    
    ysize, xsize, _ = imOut.shape
    for y in range(ysize):
        for x in range(xsize):
            for c in range(3):  # Loop over RGB channels
                in1, in2 = int(imIn2[y, x, c]), int(imIn1[y, x, c])
                if in1 < 128:
                    imOut[y, x, c] = np.clip((in1 * in2) // 127, 0, 255)
                else:
                    imOut[y, x, c] = np.clip(255 - (((255 - in1) * (255 - in2)) // 127), 0, 255)
    
    return imOut

gt = np.array([
    [[176,   0, 241],
     [ 86, 216, 249],
     [ 90,  36, 152],
     [  1,   0, 250],
     [130, 159, 150],
     [ 96,  41, 252],
     [ 22,  75,  59],
     [ 11, 238, 151]],

    [[ 79, 234, 119],
     [156, 233,   1],
     [225, 252,  50],
     [207, 245,  79],
     [248, 150,  33],
     [106, 211,  22],
     [252,   3, 247],
     [ 24,  43, 192]],

    [[ 29,  17, 225],
     [ 66, 205, 131],
     [ 45, 167,  13],
     [173, 210,  74],
     [ 65, 253,  71],
     [ 76, 146,  75],
     [235,  19,  13],
     [157, 116,   0]],

    [[154,  20, 225],
     [248,  90,  42],
     [ 65, 246,  69],
     [ 87,  27, 240],
     [  5, 254,  44],
     [ 45, 227,   0],
     [239, 253, 248],
     [240, 227, 141]],

    [[ 14,  82, 248],
     [129, 110, 185],
     [ 11,   7,  15],
     [ 17,   0,  10],
     [130, 186,  10],
     [  0, 124, 207],
     [ 45, 124, 133],
     [222, 103, 122]],

    [[ 17, 222, 248],
     [ 40, 205,  48],
     [216, 194, 232],
     [246, 108,  18],
     [125, 163,  46],
     [178, 250, 231],
     [176, 132,  13],
     [ 12, 123, 171]],

    [[243, 247, 213],
     [  6,  23, 145],
     [176,   1, 174],
     [112, 207, 223],
     [137, 170,  19],
     [105, 113,  81],
     [ 80,  81,  98],
     [  3, 143,  36]],

    [[137,  26, 197],
     [107, 255,  51],
     [181, 136,   1],
     [151, 234,  46],
     [254,   0, 198],
     [211, 209,  80],
     [ 55, 100,   5],
     [239,  69,  24]]
])
sol = imaging(img1, img2)
assert np.allclose(np.array(gt), np.array(sol))
