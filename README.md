# Gesture Recognition API Helper

A utility toolkit for testing and interacting with the Hand Gesture Recognition API running in Docker containers.

## Overview

This project provides Python utilities to test the gesture recognition API endpoints by allowing users to:
- Send individual images for gesture detection
- Process entire directories of images in batch
- Stream webcam video for real-time gesture detection testing
- Use the detection function as an internal API

## Files

- `send_image.py` - Script for sending a single image to the gesture detection API
- `send_image_directory.py` - Script for processing multiple images in a directory
- `stream.py` - Local webcam streaming server for testing real-time detection
- `requirements.txt` - List of Python dependencies required for these scripts

## Requirements

- Python 3.6 or higher
- Required libraries are listed in `requirements.txt`

Install all dependencies easily with:

```bash
pip install -r requirements.txt
```

## Usage

### Single Image Processing

To process a single image and get detection results using command-line arguments:

```bash
python send_image.py path/to/your/image.jpg
```

Optional arguments:
```bash
python send_image.py path/to/your/image.jpg --url http://your-server:8000/detect/gesture/image
python send_image.py path/to/your/image.jpg --return-image
```

The script will:
1. Send the image to the gesture detection API
2. Save the JSON response as `[image_name]_result.json`
3. If `--return-image` is specified, also save the processed image with gesture markers as `[image_name]_processed.jpg`
4. Display the detected gestures in the console

### Directory Batch Processing

To process all images in a directory using command-line arguments:

```bash
python send_image_directory.py path/to/your/images/directory
```

Optional arguments:
```bash
python send_image_directory.py path/to/images --url http://your-server:8000/detect/gesture/image
python send_image_directory.py path/to/images --delay 1.0
python send_image_directory.py path/to/images --formats jpg,png
python send_image_directory.py path/to/images --output path/to/results
python send_image_directory.py path/to/images --return-images
```

The script will:
1. Find all images with the specified formats in the directory
2. Process each image sequentially
3. Save individual results as JSON files
4. If `--return-images` is specified, save processed images with gesture markers in a `processed_images` subdirectory
5. Create a summary file `detection_summary.json` with all detection results
6. Display a summary of detected gestures for each image

### Video Streaming

To set up a local webcam streaming server:

```bash
python stream.py
```

This will:
1. Start a local web server at http://localhost:8080
2. Stream your webcam video as MJPEG
3. Access the stream at http://localhost:8080/video

You can use this stream URL for testing real-time gesture detection with the API's stream endpoint:

```bash
curl -X POST "http://localhost:8000/detect/gesture/stream?stream_url=http://localhost:8080/video"
```

### Using as an Internal API

The updated `send_image.py` includes a function that can be imported and used in other scripts:

```python
from send_image import detect_gesture_as_function

# Using with file path
result = detect_gesture_as_function("path/to/image.jpg")

# Using with file path and getting processed image
result, image_bytes = detect_gesture_as_function("path/to/image.jpg", return_image_flag=True)

# Using with image bytes
with open("path/to/image.jpg", "rb") as f:
    image_data = f.read()
result = detect_gesture_as_function(image_data)
```

This function can return either just the detection results (as a dictionary) or both the results and the processed image (as a tuple).

## Docker Configuration

These scripts are designed to work with a gesture recognition API running in Docker at `http://localhost:8000`. 

If your Docker container uses a different address or port, you can specify it using the `--url` parameter:

```bash
python send_image.py path/to/image.jpg --url http://your-docker-host:port/detect/gesture/image
```

## API Endpoints

The gesture recognition API supports several endpoints:

- `POST /detect/gesture/image` - Process images
- `POST /detect/gesture/video` - Process videos
- `POST /detect/gesture/stream` - Process video streams
- `GET /detect/gesture/detections` - View all detection records
- `GET /detect/gesture/stats` - Get detection statistics

## Example Response Format

```json
{
  "count": 1,
  "gestures": [
    {
      "gesture_name": "Thumbs Up",
      "confidence": 0.92,
      "hand_side": "Right"
    }
  ],
  "image_path": null
}
```

## Supported Gestures

The API can detect various hand gestures, including:
- Thumbs Up
- Thumbs Down
- Victory (Peace sign)
- Open Palm
- Closed Fist
- Pointing
- ILoveYou sign (combination of the ASL signs for I, L, and Y)

## Error Handling

The scripts include robust error handling:
- Image decoding errors are properly caught and reported
- Connection issues to the API are handled gracefully
- When image visualization fails, JSON results are still returned
- Detailed error messages help diagnose issues with the API or images

## Troubleshooting

### Connection Issues
- Ensure the Docker container is running: `docker ps`
- Check if the API is accessible: `curl http://localhost:8000/health`
- Verify network settings if running on a different host

### Image Processing Issues
- Confirm the image format is supported (JPG, JPEG, PNG)
- Check if the image file size is within limits (typically under 10MB)
- Ensure the image contains visible hand gestures

### Streaming Issues
- Make sure your webcam is properly connected and accessible
- Check if ports 8080 (stream server) and 8000 (API) are not blocked by firewall
- For cross-machine testing, replace 'localhost' with your machine's IP address

## Quick Setup Guide

For a quick start:

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Make sure your Docker container with the gesture recognition API is running
4. Run one of the scripts with your desired parameters:
   ```bash
   python send_image.py path/to/image.jpg
   # or
   python send_image_directory.py path/to/images/directory
   # Get processed images with visualized gestures:
   python send_image.py path/to/image.jpg --return-image
   # Process a directory and get all processed images:
   python send_image_directory.py path/to/images/directory --return-images
   ```

## Contributing

Feel free to extend and improve these utilities. Possible enhancements:
- GUI for visualizing detection results in real-time
- Integration with other gesture recognition services
- Support for additional file formats and detection options
