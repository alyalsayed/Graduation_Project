import io
import base64
import os
import time
from PIL import ImageFont, ImageDraw, Image
from bidi.algorithm import get_display
import arabic_reshaper
from ultralytics import YOLO
import cv2
import numpy as np

# Constants
FONT_PATH = "alfont_com_arial-1.ttf"
COLORS = [
    (255, 0, 0), (34, 75, 12), (0, 0, 255), (255, 255, 0),
    (255, 0, 255), (21, 52, 72), (66, 50, 168)
]
CLASS_LABELS_MAPPING = {
    0: "٠", 1: "١", 2: "٢", 3: "٣", 4: "٤", 5: "٥", 6: "٦", 7: "٧",
    8: "ح", 9: "٨", 10: "٩", 11: "ط", 12: "ظ", 13: "ع", 14: "أ", 15: "ب",
    16: "ض", 17: "د", 18: "ف", 19: "غ", 20: "ه", 21: "ج", 22: "ك", 23: "خ",
    24: "ل", 25: "م", 26: "ن", 27: "ق", 28: "ر", 29: "ص", 30: "س", 31: "ش",
    32: "ت", 33: "ث", 34: "و", 35: "ي", 36: "ذ", 37: "ز"
}


def draw_arabic_text(image, text, position, color):
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    img_pil = Image.fromarray(image)
    draw = ImageDraw.Draw(img_pil)
    font = ImageFont.truetype(FONT_PATH, 40)
    bbox = draw.textbbox(position, bidi_text, font=font)
    draw.rectangle(bbox, fill=color)
    draw.text(position, bidi_text, font=font, fill="black")
    return np.array(img_pil)


def process_video(video_path, model):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    size = (frame_width, frame_height)

    processed_video_path = os.path.join(os.getcwd(), 'processed_video.mp4')
    out = cv2.VideoWriter(processed_video_path, fourcc, original_fps, size)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        for i, result in enumerate(results):
            sorted_boxes = sorted(result.boxes.data, key=lambda box: box[0])

            for j, box in enumerate(sorted_boxes):
                x1, y1, x2, y2, conf, cls = box[:6]
                class_label = CLASS_LABELS_MAPPING.get(int(cls), 'Unknown')
                color_index = j % len(COLORS)
                color = COLORS[color_index]
                cv2.rectangle(frame, (int(x1), int(y1)),
                              (int(x2), int(y2)), color, 2)
                frame = draw_arabic_text(
                    frame, class_label, (int(x1), int(y1 - 40)), color)

        out.write(frame)
        time.sleep(1)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    return processed_video_path



def reverse_arabic(text):
    segments = []
    current_segment = ""
    is_number = text[0].isdigit()

    for char in text:
        if char.isdigit() == is_number:
            current_segment += char
        else:
            if current_segment:
                segments.append(current_segment)
            current_segment = char
            is_number = not is_number

    segments.append(current_segment)

    reversed_text = ""
    for segment in segments:
        if segment[0].isdigit():
            reversed_text += segment
        else:
            reversed_text = segment[::-1] + reversed_text

    return reversed_text
