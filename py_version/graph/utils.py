import xml.etree.ElementTree as ET
import Levenshtein
import random
from PIL import Image
import numpy as np

class Utils:
    
    @staticmethod
    def find_clickableNodes(node:ET.Element, clickableNodes:list[ET.Element]):
        if node == None:
            return
        
        if node.attrib['clickable'] == 'true':
            clickableNodes.append(node)
        
        for child in node:
            if child != None:
                Utils.find_clickableNodes(child,clickableNodes)
    
    @staticmethod
    def calculate_string_similarity(str1, str2):
        str1 = str1.replace(' id=', '').replace('"', '')
        str2 = str2.replace(' id="', '').replace('"', '')
        distance = Levenshtein.distance(str1, str2)
        return 1 - distance / max(len(str1), len(str2))
    
    @staticmethod
    def calculate_desc_similarity(str1, str2):
        distance = Levenshtein.distance(str1, str2)
        return 1 - distance / max(len(str1), len(str2))
    
    @staticmethod
    def generate_id():
        return random.randint(100,999)
    
    @staticmethod
    def calculate_phash(image_path):
        image = Image.open(image_path)
    
        # 1. Resize the image to 8x8 pixels
        image = image.resize((8, 8), Image.ANTIALIAS)
    
        # 2. Convert the image to grayscale
        image = image.convert("L")

        # 3. Get the pixel values
        pixels = np.array(image).flatten()
        image.close()

        # 4. Compute the DCT (Discrete Cosine Transform)
        dct = np.fft.dct(pixels)

        # 5. Calculate the average of the DCT coefficients
        avg = np.mean(dct)

        # 6. Generate the hash based on average
        return ''.join(['1' if pixel > avg else '0' for pixel in dct])

    @staticmethod
    def hamming_distance(hash1, hash2):
        if len(hash1) != len(hash2):
            raise ValueError("Hash lengths do not match!")
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

    @staticmethod
    def calculate_phash_similarity(path1, path2):
        phash1 = Utils.calculate_phash(path1)
        phash2 = Utils.calculate_phash(path2)
        return 1 - Utils.hamming_distance(phash1, phash2) / 64
 