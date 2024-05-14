import os
import argparse
import cv2
import numpy as np
import csv
from PIL import ImageFont, ImageDraw, Image
from tensorflow.keras.preprocessing.image import load_img
import arabic_reshaper
from bidi.algorithm import get_display
from ultralytics import YOLO
import time
import pandas as pd
# Load YOLO models
ocr_model = YOLO('best.onnx')
plate_detector_model = YOLO('car_plate_detector.onnx')

# Define font path
font_path = "alfont_com_arial-1.ttf"

# Define class labels mapping
class_labels_mapping = {
    0: "0",
    1: "1",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "ح",
    9: "8",
    10: "9",
    11: "ط",
    12: "ظ",
    13: "ع",
    14: "ا",
    15: "ب",
    16: "ض",
    17: "د",
    18: "ف",
    19: "غ",
    20: "ه",
    21: "ج",
    22: "ك",
    23: "خ",
    24: "ل",
    25: "م",
    26: "ن",
    27: "ق",
    28: "ر",
    29: "ص",
    30: "س",
    31: "ش",
    32: "ت",
    33: "ث",
    34: "و",
    35: "ي",
    36: "ذ",
    37: "ز"
}

# Define colors for each character
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255),
          (255, 255, 0), (255, 0, 255), (0, 255, 255), (66, 50, 168)]

# Function to draw Arabic text on an image


def draw_arabic_text(image, text, position, color):
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    img_pil = Image.fromarray(image)
    draw = ImageDraw.Draw(img_pil)
    # Load the Arabic font
    font = ImageFont.truetype(font_path, 32)
    draw.text(position, bidi_text, font=font, fill=color)
    return np.array(img_pil)

# Function to detect ROI


def detect_roi(image_path, plate_detector_model):
    try:
        # Perform prediction
        results = plate_detector_model(image_path)

        if len(results) == 0:
            raise ValueError("No boxes predicted for image.")

        # Extract box coordinates from results
        box = results[0].boxes.data[0].tolist()
        x1, y1, x2, y2 = box[0:4]
        x1, y1, x2, y2 = [int(i) for i in [x1, y1, x2, y2]]

        # Load original image
        img = np.array(load_img(image_path))

        # Extract region of interest (ROI)
        roi = img[y1:y2, x1:x2]
        roi = cv2.resize(roi, (220, 220))

        # Convert ROI to BGR format
        image_bgr = cv2.cvtColor(roi, cv2.COLOR_RGB2BGR)

        # Save ROI image in "plates" folder
        roi_filename = os.path.basename(image_path)
        roi_filename = os.path.splitext(roi_filename)[0]
        roi_path = os.path.join("./plates", f"{roi_filename}.jpg")
        cv2.imwrite(roi_path, image_bgr)

        return roi_path, image_bgr, (x1, y1, x2, y2)
    except Exception as e:
        print(f"Failed to predict boxes for image: {image_path}")
        print(f"Error: {str(e)}")
        return None, None, None

# Function to draw characters on ROI


def draw_char(roi_path, roi, ocr_model):
    if roi_path is None:
        print("No plate detected.")
        return None, False, ''

    try:
        # Perform prediction
        results = ocr_model(roi_path)

        detected_plate = False
        predicted_label = ''

        # Process results list
        for i, result in enumerate(results):
            # Sort boxes based on their x-coordinate (left to right)
            sorted_boxes = sorted(result.boxes.data, key=lambda box: box[0])

            for j, box in enumerate(sorted_boxes):
                # Extract box coordinates, confidence, and class
                x1, y1, x2, y2, conf, cls = box[:6]

                # Convert class number to Arabic character
                class_label = class_labels_mapping.get(
                    int(cls.item()), 'Unknown')

                # Reverse Arabic characters if not a number
                if class_label not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                    class_label = class_label[::-1]

                # Determine the color for the character
                color_index = j % len(colors)
                color = colors[color_index]

                # Draw rectangle around the character
                roi = cv2.rectangle(roi, (int(x1), int(y1)),
                                    (int(x2), int(y2)), color, 2)

                # Add class label text
                roi = draw_arabic_text(
                    roi, class_label, (int(x1), int(y1 - 35)), color)

                predicted_label += class_label

                detected_plate = True
        print(predicted_label)
        return roi, detected_plate, predicted_label
    except Exception as e:
        print(f"Error in drawing characters on ROI: {str(e)}")
        return None, False, ''

# Function to predict images in a folder and write results to CSV


def predict_images_in_folder(input_folder, output_folder, plate_detector_model, ocr_model):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Open CSV file for writing with UTF-8 encoding
    with open(os.path.join(output_folder, 'predictions.csv'), mode='w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Image_Path', 'x1', 'y1', 'x2',
                            'y2', 'Predicted_Label', 'Plate_Detected'])

        # Iterate over images in input folder
        for filename in os.listdir(input_folder):
            if filename.endswith(".jpg") or filename.endswith(".png"):
                image_path = os.path.join(input_folder, filename)
                # Detect ROI
                roi_path, roi, coordinates = detect_roi(
                    image_path, plate_detector_model)
                # Draw characters on ROI
                roi_with_chars, plate_detected, predicted_label = draw_char(
                    roi_path, roi, ocr_model)
                # Save ROI with characters to output folder
                if roi_with_chars is not None:
                    output_path_roi = os.path.join(
                        output_folder, f"roi_{filename}")
                    cv2.imwrite(output_path_roi, roi_with_chars)

                # Write to CSV
                if plate_detected:
                    csv_writer.writerow(
                        [image_path, *coordinates, predicted_label, plate_detected])
                else:
                    # Write information for undetected plates
                    csv_writer.writerow(
                        [image_path, '*', '*', '*', '*', '*', False])
                time.sleep(1)


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Predict on images and create a new folder of predictions")
    parser.add_argument("-p", "--path", type=str,
                        help="Path to the folder of test images", required=True)
    args = parser.parse_args()

    # Perform predictions on images in input folder and save ROIs to output folder
    predict_images_in_folder(args.path, "results",
                             plate_detector_model, ocr_model)

    df = pd.read_csv("./results/predictions.csv")
    print(df.head())
