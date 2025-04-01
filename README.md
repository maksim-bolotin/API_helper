# Gesture Recognition API Helper

A utility toolkit for testing and interacting with the Hand Gesture Recognition API running in Docker containers.

## Overview

This project provides Python utilities to test the gesture recognition API endpoints by allowing users to:
- Send individual images for gesture detection
- Process entire directories of images in batch
- Stream webcam video for real-time gesture detection testing

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

Alternatively, you can install the dependencies manually:

```bash
pip install requests pathlib aiohttp opencv-python
```

## Usage

### Single Image Processing

To process a single image and get detection results:

```bash
python send_image.py
```

Edit the `image_path` variable in the script to point to your image file:

```python
image_path = "path/to/your/image.jpg"
```

The script will:
1. Send the image to the gesture detection API
2. Save the JSON response as `[image_name]_result.json`
3. Display the detected gestures in the console

### Directory Batch Processing

To process all images in a directory:

```bash
python send_image_directory.py
```

Edit the `directory_path` variable in the script to specify your images directory:

```python
directory_path = "path/to/your/images"
```

The script will:
1. Find all JPG, JPEG, and PNG images in the specified directory
2. Process each image sequentially
3. Save individual results as JSON files
4. Create a summary file `detection_summary.json` with all detection results
5. Display a summary of detected gestures for each image

#### Configuration Options

You can customize the behavior by modifying these variables:
- `api_url` - API endpoint URL (default: "http://localhost:8000/detect/gesture/image")
- `image_extensions` - File types to process (default: '.jpg', '.jpeg', '.png')
- `delay` - Time delay between processing images (default: 0.5 seconds)

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

## Docker Configuration

These scripts are designed to work with a gesture recognition API running in Docker at `http://localhost:8000`. 

If your Docker container uses a different address or port, update the `api_url` variable in the scripts:

```python
api_url = "http://your-docker-host:port/detect/gesture/image"
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
4. Edit the `image_path` or `directory_path` in the respective scripts
5. Run one of the scripts to begin testing

## Contributing

Feel free to extend and improve these utilities. Possible enhancements:
- Command-line arguments for easier configuration
- GUI for visualizing detection results
- Integration with other gesture recognition services
- Real-time detection visualization
