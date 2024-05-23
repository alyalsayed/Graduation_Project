import streamlit as st
import requests
from PIL import Image
import io
import base64
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Define API URL
API_URL = os.getenv('API_URL')

def save_uploaded_video(uploaded_video, save_path):
    with open(save_path, 'wb') as out_file:
        out_file.write(uploaded_video.read())

# Streamlit app title
st.title("Car Plate OCR")

# File uploader for image or video
uploaded_file = st.file_uploader("Upload Image or Video", type=["jpg", "jpeg", "png", "mp4", "mov", "avi", "mkv"])

if uploaded_file is not None:
    if uploaded_file.type.startswith('image'):
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image', use_column_width=True)

        if st.button('Predict'):
            with st.spinner('Processing...'):
                try:
                    # Convert the image to bytes
                    img_bytes = io.BytesIO()
                    image.save(img_bytes, format=image.format)
                    img_bytes = img_bytes.getvalue()

                    # Send the image to the Flask API
                    files = {'image': (uploaded_file.name, img_bytes, uploaded_file.type)}
                    response = requests.post(API_URL, files=files)

                    if response.status_code == 200:
                        data = response.json()
                        # Decode the modified image
                        modified_image_data = base64.b64decode(data['modified_image'])
                        modified_image = Image.open(io.BytesIO(modified_image_data))

                        # Display the modified image and predictions
                        st.image(modified_image, caption='Modified Image with Predictions', use_column_width=True)
                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>Concatenated Text: {data['concatenated_text']}</div>", unsafe_allow_html=True)

                        # Save the modified image to a folder
                        processed_images_folder = os.path.join(os.getcwd(), 'static', 'processed_images')
                        os.makedirs(processed_images_folder, exist_ok=True)
                        modified_image_path = os.path.join(processed_images_folder, 'modified_image.jpg')
                        modified_image.save(modified_image_path)

                        

                        st.success(f"Modified image saved at: {modified_image_path}")
                    else:
                        st.error("Failed to get prediction from the API")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

    elif uploaded_file.type.startswith('video'):
        video_filename = os.path.join(os.getcwd(), uploaded_file.name)
        save_uploaded_video(uploaded_file, video_filename)

        # Show the original video
        st.video(video_filename)

        if st.button('Process Video'):
            with st.spinner('Processing...'):
                try:
                    # Send the video file to the Flask API for processing
                    files = {'video': open(video_filename, 'rb')}
                    response = requests.post(API_URL, files=files)

                    if response.status_code == 200:
                        processed_video_path = os.path.join(os.getcwd(), 'static', 'processed_videos')
                        os.makedirs(processed_video_path, exist_ok=True)
                        processed_video_file = os.path.join(processed_video_path, 'processed_video.mp4')
                        with open(processed_video_file, 'wb') as f:
                            f.write(response.content)

                        # Show the processed video
                        st.video(processed_video_file)

                        # Provide a download button for the processed video
                        with open(processed_video_file, 'rb') as f:
                            st.download_button(
                                label='Download Processed Video',
                                data=f,
                                file_name='processed_video.mp4',
                                mime='video/mp4'
                            )
                        st.success(f"Processed video saved at: {processed_video_file}")
                    else:
                        st.error("Failed to process video")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
