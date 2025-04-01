import requests
import json
import os
from pathlib import Path
import time


def detect_gesture_in_image(image_path, api_url="http://localhost:8000/detect/gesture/image"):
    """
    Send an image to the gesture detection endpoint and return the JSON response.

    Args:
        image_path (str): Path to the image file
        api_url (str): URL of the gesture detection endpoint

    Returns:
        dict: JSON response with detection results
    """
    # Check if the file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Prepare the files for upload
    files = {
        'image': (Path(image_path).name, open(image_path, 'rb'), 'image/jpeg')
    }

    try:
        # Send the request to the API
        response = requests.post(api_url, files=files)

        # Check if the request was successful
        response.raise_for_status()

        # Parse the JSON response
        result = response.json()

        # Save the result to a JSON file
        output_filename = f"{Path(image_path).stem}_result.json"
        with open(output_filename, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"Detection completed for {Path(image_path).name}. Results saved to {output_filename}")
        return result

    except requests.exceptions.RequestException as e:
        print(f"Error making request for {Path(image_path).name}: {e}")
        return None
    finally:
        # Make sure to close the file handle
        files['image'][1].close()


def process_image_directory(directory_path, api_url="http://localhost:8000/detect/gesture/image",
                            image_extensions=('.jpg', '.jpeg', '.png'), delay=0.5):
    """
    Process all images in a directory.

    Args:
        directory_path (str): Path to the directory containing images
        api_url (str): URL of the gesture detection endpoint
        image_extensions (tuple): File extensions to process
        delay (float): Delay between requests in seconds

    Returns:
        dict: Dictionary with image paths as keys and detection results as values
    """
    # Check if the directory exists
    directory = Path(directory_path)
    if not directory.exists() or not directory.is_dir():
        raise NotADirectoryError(f"Directory not found: {directory_path}")

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
        result = detect_gesture_in_image(str(image_path), api_url)
        results[str(image_path)] = result

        # Add delay between requests to avoid overwhelming the server
        if i < len(image_files) and delay > 0:
            time.sleep(delay)

    # Create a summary file
    summary_path = directory / "detection_summary.json"
    with open(summary_path, 'w') as f:
        # Create a simplified summary with just the essentials
        summary = {
            str(path): {
                "gestures": result.get("gestures", []) if result else None,
                "count": result.get("count", 0) if result else 0
            } for path, result in results.items()
        }
        json.dump(summary, f, indent=2)

    print(f"\nProcessing complete. Processed {len(image_files)} images.")
    print(f"Summary saved to {summary_path}")

    return results


if __name__ == "__main__":
    # Example usage
    directory_path = "path/to/your/images"

    # Optional: customize API URL if needed
    api_url = "http://localhost:8000/detect/gesture/image"

    # Process all images in the directory
    results = process_image_directory(directory_path, api_url)

    # Print a simple summary of results
    print("\nDetection Summary:")
    for path, result in results.items():
        if result and "gestures" in result and result["gestures"]:
            gestures_text = ", ".join([f"{g['hand_side']} {g['gesture_name']}" for g in result["gestures"]])
            print(f"{Path(path).name}: {gestures_text}")
        else:
            print(f"{Path(path).name}: No gestures detected")
