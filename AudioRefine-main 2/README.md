# AudioRefine

## Overview
This project is a **Streamlit-based AI-Driven Video Audio Refinement Tool.** The application allows users to upload a video and processes it to provide a corrected version with grammatically accurate audio. The system extracts audio from the video, transcribes it using Google's Speech-to-Text API, corrects the transcription with Gemini, regenerates the corrected audio, and synchronizes it back into the video. The final output is a seamlessly corrected video with enhanced audio quality.

## Key Features

1. **Audio Extraction**
   - Extracts the audio track from uploaded video files using `moviepy.editor`.
   - Converts stereo audio to mono for improved compatibility and processing.

2. **Accurate Transcription**
   - Utilizes Google Cloud Speech-to-Text API for precise audio transcription.
   - Provides word timings, including start and end timestamps, to aid in synchronization.

3. **Grammar and Filler Correction**
   - Segments transcriptions into coherent sentences based on natural pauses.
   - Sends text segments to Gemini for grammar correction and filler word removal while preserving the original meaning and timing.

4. **Text-to-Speech Transformation**
   - Generates new audio using Google Cloud Text-to-Speech API.
   - Adjusts audio durations to match original transcription timings for seamless integration.

5. **Audio and Video Synchronization**
   - Combines corrected audio segments into a single track, aligning them with the video.
   - Replaces the original audio track in the video with the corrected version using FFmpeg.

6. **User-Friendly Interface**
   - Interactive Streamlit app for easy video uploads and processing.
   - Displays the final corrected video for download and sharing.



## Prerequisites

- Python 3.8+
- ffmpeg
  ```sh
  brew install ffmpeg
  ```


## Project and environment setup
  
 1. **Clone the repository:**

    ```sh
    git clone https://github.com/Nitish-Biswas/AudioRefine.git
    cd AudioRefine
    ```
2. **Create a virtual environment and activate it:**

    ```sh
    python3 -m venv venv
    ```
    
   ***On macOS***
   ```sh
   source venv/bin/activate
   ```
   
   ***On Windows***
   ```sh
   venv\Scripts\activate
   ```


3. **Install the dependencies:**

    ```sh
    pip install -r requirements.txt
    ```


4. **Set the Google Cloud credentials:**

   ****Each time you activate your virtual environment, you must set the GOOGLE_APPLICATION_CREDENTIALS environment variable. This can be done by running the following command:****

   ```sh
    export GOOGLE_APPLICATION_CREDENTIALS="\path\to\your\json\file.json "
    ```

## Run the APP:

   ```sh
    streamlit run app.py
   ```


## Demo

[Click Here](https://youtu.be/0U4-pR-lRas) to watch the project demonstration.

