# File for all of the OpenCV code, including movement control depending on the OpenCV view.
import time
import cv2
import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera

# variables used to divide screen evenly, do not change
hei = 300
wid = 1100
pink = (255, 192, 203)
# change the following 2 variables to adjust range of screen to scan
h_start = int(hei*0.1)
h_end = int(hei*0.4)
# fixed variables, do not change
w_1 = int(wid*0.2)
w_2 = int(wid*0.4)
w_3 = int(wid*0.6)
w_4 = int(wid*0.8)

# camera variables
camera = None
rawCapture = None


# search in strip to get next direction
def get_dir(img, mainframe, cur_thread):
    global hei, wid, h_start, h_end, w_1, w_2, w_3, w_4
    print("opencv get dir")
    result = [0, 0, 0, 0, 0]
    max_index = 0

    # search through 5 blocks
    for w in range(0, w_1):
        for h in range(h_start, h_end):
            if img[h][w] == 0:
                result[0] = result[0] + 1

    for w in range(w_1, w_2):
        for h in range(h_start, h_end):
            if img[h][w] == 0:
                result[1] = result[1] + 1

    for w in range(w_2, w_3):
        for h in range(h_start, h_end):
            if img[h][w] == 0:
                result[2] = result[2] + 1

    for w in range(w_3, w_4):
        for h in range(h_start, h_end):
            if img[h][w] == 0:
                result[3] = result[3] + 1

    for w in range(w_4, wid):
        for h in range(h_start, h_end):
            if img[h][w] == 0:
                result[4] = result[4] + 1
    #print(result)

    # find target zone with most white pixels
    for i in range(0, 5):
        if result[i] <= result[max_index]:
            max_index = i

    # uses sonars to detect walls. If within 30cm, evade
    if mainframe.read_sonar(cur_thread.getName()) <= 30:
        return 5

    # initiate action based on results of zone scanning
    if max_index is 4 and result[4] > 19780:
        print("No object detected in frame")
        # alternate between going left and right if no object is detected
        # DO NOT use other actions, this prevents robot to stuck in circle
        return 2
    else:
        print("The area with most white pixel is zone: " + str(max_index))
        # go towards target area to clean
        turn_count = 0
        return max_index


# Dir is an int ranging from 0 to 4, representing the 5 zones scanned by get_dir
# Todo: Calculate angles, speed, time needed for this method to move robot to target area ahead
def step_forward(zone, mainframe, cur_thread):
    print("opencv step")
    if zone is 0:
        mainframe.movement((0, -0.3, 1.0), cur_thread.getName())
        mainframe.movement((-0.3, -0.3, 2.7), cur_thread.getName())
        mainframe.movement((0, 0, 0.1), cur_thread.getName())
    elif zone is 1:
        mainframe.movement((0, -0.3, 0.35), cur_thread.getName())
        mainframe.movement((-0.3, -0.3, 2.5), cur_thread.getName())
        mainframe.movement((0, 0, 0.1), cur_thread.getName())
    elif zone is 2:
        mainframe.movement((-0.3, -0.3, 2.5), cur_thread.getName())
        mainframe.movement((0, 0, 0.1), cur_thread.getName())
    elif zone is 3:
        mainframe.movement((-0.3, 0, 0.35), cur_thread.getName())
        mainframe.movement((-0.3, -0.3, 2.5), cur_thread.getName())
        mainframe.movement((0, 0, 0.1), cur_thread.getName())
    elif zone is 4:
        mainframe.movement((-0.3, 0, 1.0), cur_thread.getName())
        mainframe.movement((-0.3, -0.3, 2.7), cur_thread.getName())
        mainframe.movement((0, 0, 0.1), cur_thread.getName())
    elif zone is 5:
        mainframe.movement((1, 0, 0.4), cur_thread.getName())
        mainframe.movement((0, 0, 0.1), cur_thread.getName())
    else:
        print("Error, zone index out of bound.")


# Initial method called by the program's main init.
# Configures initial settings for the OpenCV code and then starts the main loop for the thread.
#
# Requires: mainframe  - a reference to the program's framework. Used to interact with the robot's state.
#           cur_thread - a reference to the OpenCV thread. Allows for references to be passed on to other method.
def init(mainframe, cur_thread):
    # Variable initialization or any start up processes required
    # Todo: do this here
    global camera, rawCapture
    print("opencv initiating")
    camera = PiCamera()
    camera.resolution = (1104, 304)
    camera.framerate = 32
    rawCapture = PiRGBArray(camera, size=(1104, 304))

    # Start the main loop for the OpenCV thread
    main(mainframe, cur_thread)


# Main control loop for the OpenCV thread.
# All operations with the OpenCV integration stem from this method. This loop continues until the program quits.
#
# Requires: mainframe  - a reference to the program's framework. Used to interact with the robot.
#           cur_thread - a reference to the OpenCV thread. Allows for references to be passed on to other method.
def main(mainframe, cur_thread):
    while True:
        print(mainframe.get_control_mode())
        if mainframe.get_control_mode() == "camera":
            # Todo: Implement all of the OpenCV stuff here

            # Note: To do a movement, use mainframe.movement((l_motor, r_motor, dur), cur_thread.getName())
            #       See spec in movement.py for more info on the parameters

            #global w_1, w_2, w_3, w_4, wid, hei
            # live processing
            print("opencv main")
            for fr in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
                # Acquiring frames
                frame = fr.array
                hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                # Blur frame for better detection
                frame = cv2.blur(frame, (5, 5))
                kernel = np.ones((5, 5), np.uint8)
                # Red color filter
                low_red = np.array([2, 80, 80])
                high_red = np.array([255, 255, 126])
                red_mask = cv2.inRange(hsv_frame, low_red, high_red)
                # Blue color filter
                low_blue = np.array([94, 80, 2])
                high_blue = np.array([100, 255, 255])
                blue_mask = cv2.inRange(hsv_frame, low_blue, high_blue)
                # Green color filter
                low_green = np.array([25, 52, 72])
                high_green = np.array([255, 100, 255])
                green_mask = cv2.inRange(hsv_frame, low_green, high_green)
                # Overlap color masks
                mask = cv2.bitwise_or(red_mask, blue_mask)
                mask = cv2.bitwise_or(mask, green_mask)
                # Dilate
                dilation = cv2.dilate(mask, kernel, iterations=1)
                direction = get_dir(dilation, mainframe, cur_thread)
                print(direction)
                step_forward(direction, mainframe, cur_thread)

                # Draw frame for direction scanning
                '''frame = cv2.line(frame, (w_1, h_start), (w_1, h_end), pink, 3)
                frame = cv2.line(frame, (w_2, h_start), (w_2, h_end), pink, 3)
                frame = cv2.line(frame, (w_3, h_start), (w_3, h_end), pink, 3)
                frame = cv2.line(frame, (w_4, h_start), (w_4, h_end), pink, 3)
                frame = cv2.line(frame, (0, h_start), (wid, h_start), pink, 3)
                frame = cv2.line(frame, (0, h_end), (wid, h_end), pink, 3)'''
                # Show individual color mask
                '''cv2.imshow('blue', blue_mask)
                cv2.imshow('green', green_mask)
                cv2.imshow('red', red_mask)
                cv2.imshow('Multi color filter', dilation)
                cv2.imshow('Original', frame)'''

                # Cleanups
                key = cv2.waitKey(1) & 0xFF
                rawCapture.truncate(0)

                if key == ord("q"):
                    break
                if mainframe.get_control_mode() != "camera":
                    break
        else:
            # If the current control mode is not the camera, sleep this thread to reduce resource consumption
            time.sleep(1)
