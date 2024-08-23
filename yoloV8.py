#!/usr/bin/env python3

# imports
from PIL import Image as PImage
from ultralytics import YOLO
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
import time
import json
import rospy
from messages.msg import Prediction
from messages.msg import Prediction_element
from casualty import Casualty

# constants
RUN_WITH_CAMERA         = 0
RUN_WITH_PATH           = 1
CONFIDENCE_THRESHOLD    = 0

TRAUMA_HEAD             = 0
TRAUMA_TORSO            = 1
TRAUMA_LOWER_EXT        = 2
AMPUTATION_LOWER_EXT    = 3
TRAUMA_UPPER_EXT        = 4
AMPUTATION_UPPER_EXT    = 5
SEVERE_HEMORRHAGE       = 6

# creating publisher
publisher = rospy.Publisher('model_1_predictions', Prediction, queue_size=10)

# initializing yoloV8 model
model = YOLO("./yoloV8_weights/best.pt")

# creating bridge object
bridge = CvBridge()

# publishes the results of a prediction to "yoloV8_prediction"
def publish_results(results):
    # formatting results into a json
    for result in results:
        combined_data = [{"affliction_class": int(cls), "confidence": float(conf)} for cls, conf in zip(result.boxes.cls.cpu().numpy(), result.boxes.conf.cpu().numpy())]
        json.dumps(combined_data)
        print(combined_data)
        print("---------------------------------------------------------------------")

    casualty = Casualty()

    # converting results to casualty object
    for item in combined_data:
        if item["confidence"] < CONFIDENCE_THRESHOLD:
            # skipping values with confidence values below the threshold
            continue
        else:
            if item["affliction_class"] == TRAUMA_HEAD:
                casualty.trauma_head = 1
            elif item["affliction_class"] == TRAUMA_TORSO:
                casualty.trauma_torso = 1
            elif item["affliction_class"] == TRAUMA_LOWER_EXT:
                if casualty.trauma_lower_ext != 2:
                    casualty.trauma_lower_ext = 1
            elif item["affliction_class"] == AMPUTATION_LOWER_EXT:
                casualty.trauma_lower_ext = 2
            elif item["affliction_class"] == TRAUMA_UPPER_EXT:
                if casualty.trauma_upper_ext != 2:
                    casualty.trauma_upper_ext = 1
            elif item["affliction_class"] == AMPUTATION_UPPER_EXT:
                casualty.trauma_upper_ext = 2
            elif item["affliction_class"] == SEVERE_HEMORRHAGE:
                casualty.severe_hemorrhage = 1
            else:
                print("system: ERROR - invalid affliction class")

    casualty.alertness_motor = 1
    
    casualty.print_self()

    prediction = Prediction()
    # prediction_element = Prediction_element()

    # creating prediction element for trauma_head
    prediction_element = Prediction_element()
    prediction_element.affliction_class = Casualty.TRAUMA_HEAD
    if casualty.trauma_head == -1:
        prediction_element.affliction_value = 0
    else:
        prediction_element.affliction_value = casualty.trauma_head
    prediction.prediction_elements.append(prediction_element)

    # creating prediction element for trauma_torso
    prediction_element = Prediction_element()
    prediction_element.affliction_class = Casualty.TRAUMA_TORSO
    if casualty.trauma_torso == -1:
        prediction_element.affliction_value = 0
    else:
        prediction_element.affliction_value = casualty.trauma_torso
    prediction.prediction_elements.append(prediction_element)

    # creating prediction element for trauma_torso
    prediction_element = Prediction_element()
    prediction_element.affliction_class = Casualty.TRAUMA_LOWER_EXT
    if casualty.trauma_lower_ext == -1:
        prediction_element.affliction_value = 0
    else:
        prediction_element.affliction_value = casualty.trauma_lower_ext
    prediction.prediction_elements.append(prediction_element)

    # creating prediction element for trauma_torso
    prediction_element = Prediction_element()
    prediction_element.affliction_class = Casualty.TRAUMA_UPPER_EXT
    if casualty.trauma_upper_ext == -1:
        prediction_element.affliction_value = 0
    else:
        prediction_element.affliction_value = casualty.trauma_upper_ext
    prediction.prediction_elements.append(prediction_element)

    # creating prediction element for trauma_torso
    prediction_element = Prediction_element()
    prediction_element.affliction_class = Casualty.SEVERE_HEMORRHAGE
    if casualty.severe_hemorrhage == -1:
        prediction_element.affliction_value = 1
    else:
        prediction_element.affliction_value = casualty.severe_hemorrhage
    prediction.prediction_elements.append(prediction_element)


    # # iterating over predictions to create ROS message
    # prediction = Prediction()
    # for item in combined_data:
    #     prediction_element = Prediction_element()
    #     prediction_element.affliction_class = item['class']
    #     prediction_element.affliction_value = item['confidence']
    #     prediction.prediction_elements.append(prediction_element)

    # printing ROS message for reference
    print(prediction)
    print("---------------------------------------------------------------------")

    # Publishing ROS message
    publisher.publish(prediction)

# runs yoloV8 on an image published to the "usb_cam/image_raw"
def run_predictor_with_camera(raw_image):

    # converting image to a cv image
    cv_image = bridge.imgmsg_to_cv2(raw_image, desired_encoding='passthrough')

    # converting cv image to numpy array
    np_image = np.array(cv_image)

    print("---------------------------------------------------------------------")

    # running model on the numpy array
    results = model.predict(np_image)

    # publishing resutls to ros topic
    publish_results(results)



# runs yoloV8 on an image specified by a path to an image
def run_predictor_with_path():
    while True:
        # getting image path from user
        image_path = input("Enter a path to an image:\n\u001b[34m-> \u001b[0m")

        print("---------------------------------------------------------------------")

        # check if the user chose to quit
        if image_path == 'q' or image_path == 'Q':
            print("Exiting...")
            print("---------------------------------------------------------------------")
            break

        # opening image
        image = PImage.open(image_path)

        # running model on image
        results = model.predict(source=image)

        # publishing resutls to ros topic
        publish_results(results)



# sets up the predictor based on the users mode choice
def setup_predictor(choice):

    # creating ROS node
    rospy.init_node('model_1', anonymous=True)

    # checking which mode to run the predictor in
    if choice == RUN_WITH_CAMERA:
        # registering callback functions
        rospy.Subscriber('usb_cam/image_raw', Image, run_predictor_with_camera)
    else:
        # running predictor on image paths
        run_predictor_with_path()
        return

    # running node until user terminates the process
    while not rospy.is_shutdown():
        # sleeping to slow the loop down
        time.sleep(0.2)


# main function if script is run independently
if __name__ == "__main__":
    # prompting user
    print("Choose how you would like to run this program\na. Run using usb_camera node\nb. Run using a path to an image")

    # looping unitl a valid choice is entered or the program is quit
    while True:
        # prompting user
        choice = input("\u001b[34m-> \u001b[0m")

        # checking user's choice
        if choice == 'a':
            print("---------------------------------------------------------------------")
            setup_predictor(RUN_WITH_CAMERA)
            break
        elif choice == 'b':
            print("---------------------------------------------------------------------")
            setup_predictor(RUN_WITH_PATH)
            break
        elif choice == 'q' or choice == 'Q':
            print("---------------------------------------------------------------------")
            print("Exiting...")
            print("---------------------------------------------------------------------")
            break
        else:
            print("\u001b[34m-> \u001b[0m \u001b[31mInvalid choice...\u001b[0m")
