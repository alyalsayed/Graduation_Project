import os
import base64
import numpy as np
import cv2
from ultralytics import YOLO
from flask_cors import CORS
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import uuid
import tempfile
import sys
sys.path.append("../utils")
from utils import draw_arabic_text, reverse_arabic, COLORS, CLASS_LABELS_MAPPING, process_video

app = Flask(__name__)
CORS(app, origins='*')

MODEL_PATH = '../models/v2/best.onnx'

# Load YOLO model
model = YOLO(MODEL_PATH)

@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' in request.files:
        return predict_image()
    elif 'video' in request.files:
        return predict_video()
    else:
        return jsonify({'error': 'No file provided'}), 400

def predict_image():
    try:
        image_file = request.files['image']
        image_np = np.frombuffer(image_file.read(), np.uint8)
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Failed to decode image")

        results = model(image)
        concatenated_text = ''
        predictions = []

        for i, result in enumerate(results):
            sorted_boxes = sorted(result.boxes.data, key=lambda box: box[0])
            for j, box in enumerate(sorted_boxes):
                x1, y1, x2, y2, conf, cls = box[:6]
                class_label = CLASS_LABELS_MAPPING.get(int(cls.item()), 'Unknown')
                color_index = j % len(COLORS)
                color = COLORS[color_index]
                cv2.rectangle(image, (int(x1), int(y1)),
                              (int(x2), int(y2)), color, 2)
                image = draw_arabic_text(
                    image, class_label, (int(x1), int(y1 - 35)), color)
                concatenated_text += class_label
                predictions.append({
                    'class': class_label,
                    'confidence': conf.item(),
                    'x1': x1.item(),
                    'y1': y1.item(),
                    'x2': x2.item(),
                    'y2': y2.item()
                })

        concatenated_text_reversed = reverse_arabic(concatenated_text)
        ret, buffer = cv2.imencode('.jpg', image)
        modified_image_base64 = base64.b64encode(buffer).decode()

        response_data = {
            'modified_image': modified_image_base64,
            'concatenated_text': concatenated_text_reversed,
            'predictions': predictions
        }

        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def predict_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file uploaded'}), 400

    try:
        video_file = request.files['video']

        if not video_file.filename.endswith(('.mp4', '.mov', '.avi', '.mkv')):
            return jsonify({'error': 'Unsupported video format. Supported formats: mp4, mov, avi, mkv'}), 400

        video_filename = secure_filename(video_file.filename)

        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, f'{uuid.uuid4()}_{video_filename}')
            video_file.save(video_path)

            processed_video_path = process_video(video_path, model)

            if processed_video_path:
                return send_file(processed_video_path, mimetype='video/mp4')
            else:
                return jsonify({'error': 'Failed to process video'}), 500
    except Exception as e:
        return jsonify({'error': 'An error occurred while processing the video'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
