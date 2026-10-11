from exif import Image
from datetime import datetime
import cv2
import math

# can't install picamzero, as it need to install Linux's python-prctl (process control library of Linux) 
# from picamzero import Camera
from time import sleep
from pathlib import Path

def get_time(image):
    with open(image, 'rb') as image_file:
        img = Image(image_file)
        time_str = img.get("datetime_original")
        time = datetime.strptime(time_str, '%Y:%m:%d %H:%M:%S')
    return time

def get_time_difference(image_1, image_2):
    time_1 = get_time(image_1)
    time_2 = get_time(image_2)
    time_difference = time_2 - time_1
    return time_difference.seconds

base_folder = Path(__file__).parent.resolve()
image_folder = base_folder/"sample5"

image_1 = f"{image_folder}/image1.jpg"
image_2 = f"{image_folder}/image2.jpg"

t = get_time_difference(image_1, image_2)
#get_time_difference(image_1, image_2)
print(t)

list = [3,4,6,8,10]
print(len(list))

for index in range(1, 10):
    print('index:', index)



