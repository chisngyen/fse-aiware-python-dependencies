import numpy as np
from PIL import Image, ImageChops


def imaging(img1: Image, img2: Image) -> Image:

    return ImageChops.overlay(img1, img2)

# --- test ---

import numpy as np
from PIL import Image, ImageChops

def generate_random_image(width, height):
 random_data = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
 return Image.fromarray(random_data)

np.random.seed(42)
width, height = 8, 8
img1 = generate_random_image(width, height)
img2 = generate_random_image(width, height)

gt = np.array([
    [[151, 185, 241],
     [ 86, 216, 120],
     [221, 161, 126],
     [  1,   0, 250],
     [ 20, 159, 242],
     [ 57,  41, 252],
     [ 22, 146,  59],
     [172, 238, 186]],

    [[149, 234,  83],
     [156,  38,   1],
     [225, 252,  50],
     [213, 245,  46],
     [236,  37,  33],
     [106, 211,  22],
     [252,   3, 247],
     [235,  77,  43]],

    [[ 29,  48, 225],
     [ 17, 205, 108],
     [ 69, 160,  13],
     [180, 210, 199],
     [ 65, 253,  71],
     [ 76, 129, 125],
     [235,  64,  13],
     [229, 123,   0]],

    [[154,  20, 125],
     [248,  91,  90],
     [104, 246,  92],
     [  7,  27,   9],
     [  5, 254,  44],
     [ 15,   1,   0],
     [145, 253, 170],
     [240, 227, 168]],

    [[217, 239,  51],
     [197, 127, 253],
     [ 11, 226,  15],
     [186,   0,  10],
     [130,  15,  10],
     [  0, 169,  36],
     [ 62,  63, 168],
     [222,   1, 254]],

    [[ 17, 222, 248],
     [ 40, 205,  48],
     [ 35, 194, 232],
     [246, 211,  18],
     [ 76, 114,  76],
     [178,  41, 205],
     [132, 133, 250],
     [ 12, 188,   1]],

    [[243, 247, 213],
     [  6,  23, 134],
     [226,   1,  77],
     [254, 207, 135],
     [205, 170,  19],
     [108,  74,  81],
     [115, 108, 254],
     [  3, 122,  36]],

    [[153, 193, 197],
     [ 46, 255,  51],
     [239,  16, 183],
     [253, 234,  46],
     [254,   0, 121],
     [249, 209, 209],
     [162,  97,   5],
     [239,  93,  24]]
])

sol = imaging(img1, img2)
assert np.allclose(np.array(gt), np.array(sol))
