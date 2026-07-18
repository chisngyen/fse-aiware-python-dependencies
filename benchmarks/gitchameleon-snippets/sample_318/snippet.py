import numpy as np
from PIL import Image, ImageChops

def imaging(img1: Image, img2: Image) -> Image:


    def create(imIn1, imIn2, mode=None):
        if imIn1.shape != imIn2.shape:
            return None
        return np.empty_like(imIn1, dtype=np.uint8)

    def imaging_softlight(imIn1, imIn2):
        if imIn1.shape != imIn2.shape:
            return None
        
        imOut = create(imIn1, imIn2)
        ysize, xsize, _ = imOut.shape
        for y in range(ysize):
            for x in range(xsize):
                for c in range(3):  # Loop over RGB channels
                    in1, in2 = int(imIn1[y, x, c]), int(imIn2[y, x, c])
                    imOut[y, x, c] = int((((255 - in1) * (in1 * in2)) // 65536) +  (in1 * (255 - ((255 - in1) * (255 - in2) // 255))) // 255)
        return imOut
    return imaging_softlight(np.array(img1), np.array(img2))

# --- test ---

def generate_random_image(width, height):
    random_data = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    return Image.fromarray(random_data)

def create(imIn1, imIn2, mode=None):
    if imIn1.shape != imIn2.shape:
        return None
    return np.empty_like(imIn1, dtype=np.uint8)

np.random.seed(42)
width, height = 8, 8
img1 = generate_random_image(width, height)
img2 = generate_random_image(width, height)


gt = np.array([
    [[131, 189, 237],
     [ 88, 204, 105],
     [222, 168, 112],
     [  0,  38, 249],
     [ 19, 153, 241],
     [ 54,  68, 251],
     [ 51, 156,  62],
     [177, 203, 188]],

    [[159, 214,  77],
     [154,  36,   8],
     [220, 210,  71],
     [212, 244,  44],
     [180,  35,  33],
     [109, 209,  32],
     [251,   8, 240],
     [234, 106,  40]],

    [[ 41,  89, 223],
     [ 15, 203,  99],
     [101, 139,  38],
     [180, 203, 200],
     [ 87, 251,  87],
     [ 79, 117, 140],
     [233,  99,  50],
     [229, 132,   5]],

    [[152,  29, 109],
     [227, 109, 115],
     [124, 217, 115],
     [  7,  37,   8],
     [ 14, 254,  73],
     [ 15,   0,   0],
     [123, 252, 140],
     [239, 223, 171]],

    [[217, 238,  47],
     [198, 138, 252],
     [ 26, 226,  17],
     [190,  32,  19],
     [128,  14,  18],
     [  0, 173,  34],
     [ 97,  59, 172],
     [189,   0, 254]],

    [[ 16, 193, 247],
     [ 40, 187,  53],
     [ 33, 179, 225],
     [238, 212,  35],
     [ 71, 102, 105],
     [168,  38, 162],
     [115, 132, 250],
     [ 13, 191,   0]],

    [[241, 246, 183],
     [ 50,  45, 121],
     [226,   0,  71],
     [254, 176, 116],
     [205, 166,  42],
     [119,  69,  87],
     [131, 126, 254],
     [ 23, 110,  62]],

    [[157, 196, 191],
     [ 43, 255,  56],
     [238,  15, 188],
     [252, 226,  54],
     [236,   0, 107],
     [248, 209, 210],
     [169,  94,   5],
     [237, 116,  32]]
])
sol = imaging(img1, img2)
assert np.allclose(np.array(gt), np.array(sol))
