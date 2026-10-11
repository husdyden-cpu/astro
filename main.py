from exif import Image
from datetime import datetime
import cv2
import math
from picamzero import Camera
from time import sleep
from pathlib import Path
from logzero import logger

# get the original datetime from the image exif data
def get_time(image):
    with open(image, 'rb') as image_file:
        img = Image(image_file)
        time_str = img.get("datetime_original")
        time = datetime.strptime(time_str, '%Y:%m:%d %H:%M:%S')
    return time

# get the time difference in seconds between two images
def get_time_difference(image_1, image_2):
    time_1 = get_time(image_1)
    time_2 = get_time(image_2)
    time_difference = time_2 - time_1
    return time_difference.seconds

# convert images to OpenCV format
def convert_to_cv(image_1, image_2):
    image_1_cv = cv2.imread(image_1, 0)
    image_2_cv = cv2.imread(image_2, 0)
    return image_1_cv, image_2_cv

# calculate ORB(Oriented FAST and Rotated BRIEF) features and descriptors
def calculate_features(image_1, image_2, feature_number):
    orb = cv2.ORB_create(nfeatures = feature_number)
    keypoints_1, descriptors_1 = orb.detectAndCompute(image_1_cv, None)
    keypoints_2, descriptors_2 = orb.detectAndCompute(image_2_cv, None)
    return keypoints_1, keypoints_2, descriptors_1, descriptors_2

# calculate matches between two sets of descriptors using Brute-Force Matcher
def calculate_matches(descriptors_1, descriptors_2):
    brute_force = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = brute_force.match(descriptors_1, descriptors_2)
    matches = sorted(matches, key=lambda x: x.distance)
    return matches

# display the matches between two images
def display_matches(image_1_cv, keypoints_1, image_2_cv, keypoints_2, matches):
    match_img = cv2.drawMatches(image_1_cv, keypoints_1, image_2_cv, keypoints_2, matches[:100], None)
    
    resize = cv2.resize(match_img, (1600,600), interpolation = cv2.INTER_AREA)
    cv2.imshow('matches', resize)
    cv2.waitKey(0)
    cv2.destroyWindow('matches')

# find the coordinates of the matching keypoints in both images
def find_matching_coordinates(keypoints_1, keypoints_2, matches):
    coordinates_1 = []
    coordinates_2 = []
    for match in matches:
        image_1_idx = match.queryIdx
        image_2_idx = match.trainIdx
        (x1,y1) = keypoints_1[image_1_idx].pt
        (x2,y2) = keypoints_2[image_2_idx].pt
        coordinates_1.append((x1,y1))
        coordinates_2.append((x2,y2))
    return coordinates_1, coordinates_2

# calculate the mean distance between the matching keypoints in both images
def calculate_mean_distance(coordinates_1, coordinates_2):
    all_distances = 0
    merged_coordinates = list(zip(coordinates_1, coordinates_2))
    for coordinate in merged_coordinates:
        x_difference = coordinate[0][0] - coordinate[1][0]
        y_difference = coordinate[0][1] - coordinate[1][1]
        distance = math.hypot(x_difference, y_difference)
        all_distances = all_distances + distance
    return all_distances / len(merged_coordinates)

# calculate the speed in km/s using the feature distance, GSD and time difference
def calculate_speed_in_kmps(feature_distance, GSD, time_difference):
    distance = feature_distance * GSD / 100000
    speed = distance / time_difference
    return speed

camera = Camera()
base_folder = Path(__file__).parent.resolve()

# main function to take photos, calculate speed and write the result to a text file
if __name__ == "__main__":
    try:

        # target to finish the process within 10 minutes, less than 42 images
        # take 36 photos with 5 seconds interval, which will take around 3 minutes, and the ISS will travel around 1200 km during that time, which is enough to capture the movement of the ISS in the photos
        num_photos = 36

        for i in range(1,num_photos+1):
            camera.take_photo(f"{base_folder}/image{i}.jpg")
            sleep(5)

        # count the no. of files in the folder
        image_folder = base_folder
        num_files = len(list(image_folder.glob("image*.jpg")))
        # print('num_files:', num_files)

        # total_speed = 0
        speed_list = []
        GSD = 12648 # GSD in cm/pixel, get from astropi-iss-speed web site, a typical value for ISS altitude and RPi HQ Camera

        # loop through the images and append the speed between each pair of consecutive images to the speed_list[]
        for index in range(1, num_files):
            photo_1 = f"{image_folder}/image{index}.jpg"
            photo_2 = f"{image_folder}/image{index+1}.jpg"
            time_difference = get_time_difference(photo_1, photo_2) # Get time difference between images
            
            image_1_cv, image_2_cv = convert_to_cv(photo_1, photo_2) # Create OpenCV image objects
            
            keypoints_1, keypoints_2, descriptors_1, descriptors_2 = calculate_features(image_1_cv, image_2_cv, 1000) # Get keypoints and descriptors
            matches = calculate_matches(descriptors_1, descriptors_2) # Match descriptors
            coordinates_1, coordinates_2 = find_matching_coordinates(keypoints_1, keypoints_2, matches)
            
            average_feature_distance = calculate_mean_distance(coordinates_1, coordinates_2)
            speed = calculate_speed_in_kmps(average_feature_distance, GSD, time_difference)
            print("speed:", speed)

            # total_speed = total_speed + speed
            speed_list.append(speed)

        # get the average of speed by filtering out the outliers which are in the top 20% and bottom 20% of the sorted speed_list
        def average_speed_exclude_outliers(speed_list):
            sorted_speed_list = sorted(speed_list)
            n = len(sorted_speed_list)
            lower_bound = int(n * 0.2)
            upper_bound = int(n * 0.8)
            filtered_speed_list = sorted_speed_list[lower_bound:upper_bound]

            # print(filtered_speed_list)
            Average_Speed = sum(filtered_speed_list) / len(filtered_speed_list)
            return Average_Speed

        # Average_Speed = total_speed/(num_files-1)
        Average_Speed = average_speed_exclude_outliers(speed_list)
        print(f"Average speed: {Average_Speed:.4f} km/s")
    
        estimate_kms_formatted = "{:.4f}".format(Average_Speed)
        output_speed = estimate_kms_formatted
     
        with open(base_folder/"result.txt","w") as file:
            file.write(output_speed)
            
        print("Data written to", base_folder/"result.txt")
        print(output_speed)
        
    except Exception as e:
        logger.error(f"{e.__class__.__name__}:{e}")