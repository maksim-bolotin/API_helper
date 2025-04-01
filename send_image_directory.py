import requests
import json
import os
import argparse
from pathlib import Path
import time
import shutil
from typing import Dict, List, Tuple, Optional, Union, Any


def detect_gesture_in_image(
    image_path: str, 
    api_url: str = "http://localhost:8000/detect/gesture/image",
    return_image: bool = False
) -> Union[Dict, Tuple[Dict, bytes]]:
    """
    Send an image to the gesture detection endpoint and return the JSON response.

    Args:
        image_path (str): Path to the image file
        api_url (str): URL of the gesture detection endpoint
        return_image (bool): If True, also return the processed image with marked gestures

    Returns:
        Union[Dict, Tuple[Dict, bytes]]: 
            - If return_image=False: JSON response with detection results
            - If return_image=True: Tuple of (JSON response, image bytes)
    """
    # Check if the file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Prepare the files for upload
    files = {
        'image': (Path(image_path).name, open(image_path, 'rb'), 'image/jpeg')
    }

    params = {}
    if return_image:
        params['return_image'] = 'true'

    try:
        # First make a call to get the JSON data
        json_response = requests.post(api_url, files=files).json()
        
        # If return_image is True, make a second call to get the image
        if return_image:
            # Reopen the file for the second request
            files = {
                'image': (Path(image_path).name, open(image_path, 'rb'), 'image/jpeg')
            }
            try:
                # Send request with return_image parameter
                img_response = requests.post(api_url, files=files, params=params)
                
                # Check if we got an image or an error
                if img_response.headers.get('content-type') == 'application/json':
                    print(f"Warning: Received JSON instead of image for {Path(image_path).name}: {img_response.text}")
                    return json_response, None
                
                # Return both the JSON data and image bytes
                return json_response, img_response.content
            except requests.exceptions.RequestException as e:
                print(f"Error getting processed image for {Path(image_path).name}: {e}")
                return json_response, None
            finally:
                files['image'][1].close()
        else:
            # Just return the JSON result
            return json_response

    except requests.exceptions.RequestException as e:
        print(f"Error making request for {Path(image_path).name}: {e}")
        return None
    finally:
        # Make sure to close the file handle
        if not return_image:  # Only close if we didn't already close it above
            files['image'][1].close()


def process_image_directory(
    directory_path: str, 
    api_url: str = "http://localhost:8000/detect/gesture/image",
    image_extensions: Tuple[str, ...] = ('.jpg', '.jpeg', '.png'), 
    delay: float = 0.5,
    output_dir: str = None,
    return_images: bool = False
) -> Dict[str, Any]:
    """
    Process all images in a directory.

    Args:
        directory_path (str): Path to the directory containing images
        api_url (str): URL of the gesture detection endpoint
        image_extensions (tuple): File extensions to process
        delay (float): Delay between requests in seconds
        output_dir (str): Optional directory to save results to (defaults to same as input)
        return_images (bool): If True, request and save processed images with detections

    Returns:
        dict: Dictionary with image paths as keys and detection results as values
    """
    # Check if the directory exists
    directory = Path(directory_path)
    if not directory.exists() or not directory.is_dir():
        raise NotADirectoryError(f"Directory not found: {directory_path}")

    # Set up output directory
    if output_dir:
        output_directory = Path(output_dir)
        output_directory.mkdir(parents=True, exist_ok=True)
    else:
        output_directory = directory

    # Create a processed_images directory if returning images
    if return_images:
        processed_dir = output_directory / "processed_images"
        processed_dir.mkdir(exist_ok=True)
    
    # Find all image files in the directory
    image_files = []
    for ext in image_extensions:
        image_files.extend(directory.glob(f"*{ext}"))
        image_files.extend(directory.glob(f"*{ext.upper()}"))

    if not image_files:
        print(f"No images with extensions {image_extensions} found in {directory_path}")
        return {}

    print(f"Found {len(image_files)} images to process in {directory_path}")

    # Process each image
    results = {}
    for i, image_path in enumerate(sorted(image_files), 1):
        print(f"Processing image {i}/{len(image_files)}: {image_path.name}")
        
        if return_images:
            # Get both JSON and image
            result, image_bytes = detect_gesture_in_image(str(image_path), api_url, True)
            
            # Save processed image if available
            if image_bytes:
                output_image = processed_dir / f"{image_path.stem}_processed{image_path.suffix}"
                with open(output_image, 'wb') as f:
                    f.write(image_bytes)
                print(f"  - Saved processed image to {output_image}")
        else:
            # Get only JSON result
            result = detect_gesture_in_image(str(image_path), api_url)
        
        # Save the individual result to a JSON file
        output_json = output_directory / f"{image_path.stem}_result.json"
        with open(output_json, 'w') as f:
            json.dump(result, f, indent=2)
        
        results[str(image_path)] = result

        # Add delay between requests to avoid overwhelming the server
        if i < len(image_files) and delay > 0:
            time.sleep(delay)

    # Create a summary file
    summary_path = output_directory / "detection_summary.json"
    with open(summary_path, 'w') as f:
        # Create a simplified summary with just the essentials
        summary = {
            str(path): {
                "gestures": result.get("gestures", []) if result else None,
                "count": result.get("count", 0) if result else 0,
                "processed_image": str(processed_dir / f"{Path(path).stem}_processed{Path(path).suffix}") if return_images else None
            } for path, result in results.items()
        }
        json.dump(summary, f, indent=2)

    print(f"\nProcessing complete. Processed {len(image_files)} images.")
    print(f"Summary saved to {summary_path}")

    return results


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process multiple images in a directory for gesture detection')
    
    parser.add_argument('directory_path', help='Path to the directory containing images')
    parser.add_argument('--url', default="http://localhost:8000/detect/gesture/image",
                        help='URL of the gesture detection API endpoint')
    parser.add_argument('--delay', type=float, default=0.5,
                        help='Delay between processing images (seconds)')
    parser.add_argument('--formats', default='jpg,jpeg,png',
                        help='Comma-separated list of image formats to process')
    parser.add_argument('--output', help='Directory to save results (default: same as input)')
    parser.add_argument('--return-images', action='store_true',
                        help='Request and save processed images with gesture markers')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Convert formats string to tuple
    formats = tuple(f'.{fmt}' for fmt in args.formats.split(','))
    
    # Process all images in the directory
    results = process_image_directory(
        args.directory_path, 
        args.url, 
        formats,
        args.delay,
        args.output,
        args.return_images
    )
    
    # Print a simple summary of results
    print("\nDetection Summary:")
    for path, result in results.items():
        if result and "gestures" in result and result["gestures"]:
            gestures_text = ", ".join([f"{g['hand_side']} {g['gesture_name']}" for g in result["gestures"]])
            print(f"{Path(path).name}: {gestures_text}")
        elif result and "detail" in result:
            print(f"{Path(path).name}: Error - {result['detail']}")
        else:
            print(f"{Path(path).name}: No gestures detected")
