import requests
import json
import os
import argparse
from pathlib import Path
from typing import Dict, Tuple, Optional, Union, Any


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
                    print(f"Warning: Received JSON instead of image: {img_response.text}")
                    return json_response, None
                
                # Return both the JSON data and image bytes
                return json_response, img_response.content
            except requests.exceptions.RequestException as e:
                print(f"Error getting processed image: {e}")
                return json_response, None
        else:
            # Just return the JSON result
            return json_response

    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
    finally:
        # Make sure to close the file handle
        files['image'][1].close()


def process_and_save_result(result: Dict, image_path: str, image_bytes: Optional[bytes] = None) -> str:
    """
    Process detection result and save to files.
    
    Args:
        result: Detection result dictionary
        image_path: Path to the original image
        image_bytes: Optional bytes of the processed image
        
    Returns:
        str: Summary of the detection results
    """
    # Save the JSON result to a file
    output_json = f"{Path(image_path).stem}_result.json"
    with open(output_json, 'w') as f:
        json.dump(result, f, indent=2)
    
    # Save the processed image if available
    if image_bytes:
        output_image = f"{Path(image_path).stem}_processed.jpg"
        with open(output_image, 'wb') as f:
            f.write(image_bytes)
        print(f"Processed image saved to {output_image}")
    
    # Generate summary text
    summary = f"Detection completed. Results saved to {output_json}\n\n"
    
    if result and "detail" in result:
        # Error response
        summary += f"Error: {result['detail']}\n"
    elif result:
        # Normal response with gestures
        summary += "Detected gestures:\n"
        for gesture in result.get("gestures", []):
            summary += f"- {gesture['hand_side']} hand: {gesture['gesture_name']} ({gesture['confidence']:.2f})\n"
    else:
        summary += "No gestures detected."
    
    return summary


def detect_gesture_as_function(
    image_path_or_bytes: Union[str, bytes], 
    return_image_flag: bool = False,
    api_url: str = "http://localhost:8000/detect/gesture/image"
) -> Union[Dict, Tuple[Dict, bytes]]:
    """
    Function that takes an image (path or bytes) and returns detection results.
    
    Args:
        image_path_or_bytes: Either a path to an image file or image bytes
        return_image_flag: Whether to return the processed image
        api_url: URL of the API endpoint
        
    Returns:
        If return_image_flag is False, returns just the detection result dictionary
        If return_image_flag is True, returns a tuple of (detection result, processed image bytes)
    """
    # If input is a file path
    if isinstance(image_path_or_bytes, str):
        return detect_gesture_in_image(image_path_or_bytes, api_url, return_image_flag)
    
    # If input is image bytes
    elif isinstance(image_path_or_bytes, bytes):
        try:
            # Create a temporary file
            temp_file = Path("temp_image.jpg")
            
            # Write bytes to the file
            with open(temp_file, 'wb') as f:
                f.write(image_path_or_bytes)
            
            # Process the image
            result = detect_gesture_in_image(str(temp_file), api_url, return_image_flag)
            
            return result
        finally:
            # Clean up the temporary file
            if temp_file.exists():
                temp_file.unlink()
    else:
        raise TypeError("Input must be either a file path (str) or image bytes (bytes)")


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Detect gestures in an image')
    parser.add_argument('image_path', help='Path to the image file')
    parser.add_argument('--url', default="http://localhost:8000/detect/gesture/image",
                        help='URL of the gesture detection API endpoint')
    parser.add_argument('--return-image', action='store_true',
                        help='Return and save the processed image with gesture markers')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Call the function with the provided arguments
    if args.return_image:
        result, image_bytes = detect_gesture_in_image(args.image_path, args.url, True)
        summary = process_and_save_result(result, args.image_path, image_bytes)
    else:
        result = detect_gesture_in_image(args.image_path, args.url, False)
        summary = process_and_save_result(result, args.image_path)
    
    # Print the summary
    print(summary)
