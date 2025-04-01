import requests
import json
import os
from pathlib import Path


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

        print(f"Detection completed. Results saved to {output_filename}")
        return result

    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
    finally:
        # Make sure to close the file handle
        files['image'][1].close()


if __name__ == "__main__":
    # Example usage
    image_path = "C:/Users/vk071/Downloads/front-view-hand-showing-palm.jpg"
    result = detect_gesture_in_image(image_path)

    if result:
        print("\nDetected gestures:")
        for gesture in result.get("gestures", []):
            print(f"- {gesture['hand_side']} hand: {gesture['gesture_name']} ({gesture['confidence']:.2f})")
