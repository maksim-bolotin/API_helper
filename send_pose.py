"""
Script for sending images to the pose detection API.
This utility allows users to send an image file to the pose detection API 
and retrieve the detection results.
"""
import requests
import json
import os
import argparse
from pathlib import Path
from typing import Dict, Tuple, Optional, Union, Any


def detect_pose_in_image(
    image_path: str, 
    api_url: str = "http://localhost:8000/detect/pose/image",
    return_image: bool = False,
    save_image: bool = False,
    save_results: bool = False
) -> Union[Dict, Tuple[Dict, bytes]]:
    """
    Send an image to the pose detection endpoint and return the JSON response.

    Args:
        image_path (str): Path to the image file
        api_url (str): URL of the pose detection endpoint
        return_image (bool): If True, also return the processed image with marked poses
        save_image (bool): If True, save processed image on the server
        save_results (bool): If True, request to save detailed results in JSON file

    Returns:
        Union[Dict, Tuple[Dict, bytes]]: 
            - If return_image=False: JSON response with detection results
            - If return_image=True: Tuple of (JSON response, image bytes)
    """
    # Check if the file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Get file info for logging
    file_size = os.path.getsize(image_path) / (1024 * 1024)  # MB
    filename = Path(image_path).name
    print(f"Processing image: {filename} ({file_size:.2f} MB)")

    # Prepare the files for upload
    with open(image_path, 'rb') as file_handle:
        files = {
            'image': (filename, file_handle, 'image/jpeg')
        }

        # Set up parameters
        params = {}
        if save_image:
            params['save_image'] = 'true'
        if save_results:
            params['save_results'] = 'true'

        try:
            # Make JSON request
            print(f"Sending request to {api_url}...")
            response = requests.post(api_url, files=files, params=params)
            
            # Check for errors
            response.raise_for_status()
            
            # Parse JSON response
            json_response = response.json()
            print(f"Received response with status code: {response.status_code}")
            
            # If we need to get the processed image
            if return_image:
                # Re-open the file for a second request
                with open(image_path, 'rb') as file_handle:
                    files = {
                        'image': (filename, file_handle, 'image/jpeg')
                    }
                    # Add return_image parameter
                    img_params = params.copy()
                    img_params['return_image'] = 'true'
                    
                    # Send request for image
                    print("Requesting processed image...")
                    img_response = requests.post(api_url, files=files, params=img_params)
                    img_response.raise_for_status()
                    
                    # Check if we got an image back
                    if img_response.headers.get('content-type') == 'application/json':
                        print(f"Warning: Received JSON instead of image: {img_response.text}")
                        return json_response, None
                    
                    print(f"Received image data: {len(img_response.content)} bytes")
                    return json_response, img_response.content
            
            return json_response

        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    print(f"Server error: {error_json.get('detail', str(e))}")
                    return error_json
                except:
                    pass
            return {"detail": str(e)}


def process_pose_result(result: Dict, image_path: str, image_bytes: Optional[bytes] = None) -> str:
    """
    Process pose detection result and save to files.
    
    Args:
        result: Detection result dictionary
        image_path: Path to the original image
        image_bytes: Optional bytes of the processed image
        
    Returns:
        str: Summary of the detection results
    """
    # Save the JSON result to a file
    output_path = Path(image_path).parent
    output_json = output_path / f"{Path(image_path).stem}_pose_result.json"
    with open(output_json, 'w') as f:
        json.dump(result, f, indent=2)
    
    # Save the processed image if available
    if image_bytes:
        output_image = output_path / f"{Path(image_path).stem}_pose_processed.jpg"
        with open(output_image, 'wb') as f:
            f.write(image_bytes)
        print(f"Processed image saved to {output_image}")
    
    # Generate summary text
    summary = f"Pose detection completed for {Path(image_path).name}\n"
    summary += f"Results saved to {output_json}\n\n"
    
    if result and "detail" in result:
        # Error response
        summary += f"Error: {result['detail']}\n"
    elif result:
        # Normal response with poses
        summary += f"Total poses detected: {result.get('count', 0)}\n"
        
        # Add paths to results files if available
        if "results_file" in result and result["results_file"]:
            summary += f"Detailed results saved on server at: {result['results_file']}\n"
        
        if "image_path" in result and result["image_path"]:
            summary += f"Processed image saved on server at: {result['image_path']}\n"
        
        # Add action statistics if available
        if "detected_actions" in result and result["detected_actions"]:
            summary += "\nDetected actions:\n"
            for action, count in result["detected_actions"].items():
                summary += f"- {action}: {count} instances\n"
        
        # Show pose information
        if "poses" in result and result["poses"]:
            summary += "\nDetected poses:\n"
            for i, pose in enumerate(result["poses"]):
                confidence = pose.get("confidence", 0.0)
                action = pose.get("action", "Not classified")
                landmark_count = len(pose.get("landmarks", []))
                summary += f"- Pose {i+1}: Action={action}, Confidence={confidence:.2f}, Landmarks={landmark_count}\n"
        
        # Add download info if available
        if "download_url" in result and result["download_url"]:
            summary += f"\nDownload URL: {result['download_url']}\n"
    else:
        summary += "No poses detected or empty response received."
    
    return summary


def detect_pose_in_video(
    video_path: str,
    api_url: str = "http://localhost:8000/detect/pose/video",
    return_video: bool = False,
    save_video: bool = False,
    save_results: bool = False
) -> Union[Dict, Tuple[Dict, bytes]]:
    """
    Send a video to the pose detection endpoint and return the JSON response.

    Args:
        video_path (str): Path to the video file
        api_url (str): URL of the pose detection endpoint
        return_video (bool): If True, also return the processed video with marked poses
        save_video (bool): If True, save processed video on the server
        save_results (bool): If True, request to save detailed results in JSON file

    Returns:
        Union[Dict, Tuple[Dict, bytes]]: 
            - If return_video=False: JSON response with detection results
            - If return_video=True: Tuple of (JSON response, video bytes)
    """
    # Check if the file exists
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Get file info for logging
    file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
    filename = Path(video_path).name
    print(f"Processing video: {filename} ({file_size:.2f} MB)")

    # Prepare the files for upload
    with open(video_path, 'rb') as file_handle:
        files = {
            'video': (filename, file_handle, 'video/mp4')
        }

        # Set up parameters
        params = {}
        if save_video:
            params['save_video'] = 'true'
        if save_results:
            params['save_results'] = 'true'
        if return_video:
            params['return_video'] = 'true'

        try:
            # Make request
            print(f"Sending request to {api_url}...")
            print(f"This may take some time for larger videos...")
            response = requests.post(api_url, files=files, params=params)
            
            # Check for errors
            response.raise_for_status()
            
            # Check if we got a video or JSON
            if response.headers.get('content-type') == 'video/mp4':
                # For return_video=true, we've received the video directly
                print(f"Received video response: {len(response.content)} bytes")
                
                # Make a second request to get the JSON data
                with open(video_path, 'rb') as file_handle:
                    files = {
                        'video': (filename, file_handle, 'video/mp4')
                    }
                    # Remove return_video flag to get JSON
                    json_params = params.copy()
                    json_params.pop('return_video', None)
                    
                    print("Requesting JSON data...")
                    json_response = requests.post(api_url, files=files, params=json_params)
                    json_response.raise_for_status()
                    json_data = json_response.json()
                
                return json_data, response.content
            else:
                # Parse JSON response
                json_response = response.json()
                print(f"Received response with status code: {response.status_code}")
                
                return json_response

        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    print(f"Server error: {error_json.get('detail', str(e))}")
                    return error_json
                except:
                    pass
            return {"detail": str(e)}


def process_pose_video_result(result: Dict, video_path: str, video_bytes: Optional[bytes] = None) -> str:
    """
    Process pose video detection result and save to files.
    
    Args:
        result: Detection result dictionary
        video_path: Path to the original video
        video_bytes: Optional bytes of the processed video
        
    Returns:
        str: Summary of the detection results
    """
    # Save the JSON result to a file
    output_path = Path(video_path).parent
    output_json = output_path / f"{Path(video_path).stem}_pose_result.json"
    with open(output_json, 'w') as f:
        json.dump(result, f, indent=2)
    
    # Save the processed video if available
    if video_bytes:
        output_video = output_path / f"{Path(video_path).stem}_pose_processed.mp4"
        with open(output_video, 'wb') as f:
            f.write(video_bytes)
        print(f"Processed video saved to {output_video}")
    
    # Generate summary text
    summary = f"Pose detection completed for {Path(video_path).name}\n"
    summary += f"Results saved to {output_json}\n\n"
    
    if result and "detail" in result:
        # Error response
        summary += f"Error: {result['detail']}\n"
    elif result:
        # Normal response with poses
        summary += f"Total poses detected: {result.get('count', 0)}\n"
        
        # Add paths to results files if available
        if "results_file" in result and result["results_file"]:
            summary += f"Detailed results saved on server at: {result['results_file']}\n"
        
        if "video_path" in result and result["video_path"]:
            summary += f"Processed video saved on server at: {result['video_path']}\n"
        
        # Add action statistics if available
        if "detected_actions" in result and result["detected_actions"]:
            summary += "\nDetected actions:\n"
            for action, count in sorted(result["detected_actions"].items(), key=lambda x: x[1], reverse=True):
                summary += f"- {action}: {count} instances\n"
        
        # Add download info if available
        if "download_url" in result and result["download_url"]:
            summary += f"\nDownload URL: {result['download_url']}\n"
    else:
        summary += "No poses detected or empty response received."
    
    return summary


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Detect human poses in an image or video')
    parser.add_argument('file_path', help='Path to the image or video file')
    parser.add_argument('--url', help='URL of the pose detection API endpoint')
    parser.add_argument('--return-media', action='store_true',
                        help='Return and save the processed image/video with pose markers')
    parser.add_argument('--save-media', action='store_true',
                        help='Save the processed image/video on the server')
    parser.add_argument('--save-results', action='store_true',
                        help='Save detailed results in JSON on server')
    parser.add_argument('--mode', choices=['auto', 'image', 'video'], default='auto',
                        help='Processing mode: auto, image, or video')
    
    # Parse arguments
    args = parser.parse_args()
    file_path = args.file_path
    file_ext = Path(file_path).suffix.lower()
    
    # Determine processing mode
    mode = args.mode
    if mode == 'auto':
        if file_ext in ['.jpg', '.jpeg', '.png']:
            mode = 'image'
        elif file_ext in ['.mp4', '.avi', '.mov', '.wmv', '.mkv']:
            mode = 'video'
        else:
            print(f"Warning: Cannot determine file type from extension '{file_ext}'. Using 'image' mode.")
            mode = 'image'
    
    print(f"Processing mode: {mode}")
    
    # Set default URL based on mode
    if args.url:
        api_url = args.url
    else:
        api_url = f"http://localhost:8000/detect/pose/{mode}"
    
    try:
        # Process based on mode
        if mode == 'image':
            if args.return_media:
                result, image_bytes = detect_pose_in_image(
                    file_path, 
                    api_url, 
                    True, 
                    args.save_media,
                    args.save_results
                )
                summary = process_pose_result(result, file_path, image_bytes)
            else:
                result = detect_pose_in_image(
                    file_path, 
                    api_url, 
                    False, 
                    args.save_media,
                    args.save_results
                )
                summary = process_pose_result(result, file_path)
        else:  # video mode
            if args.return_media:
                result, video_bytes = detect_pose_in_video(
                    file_path, 
                    api_url, 
                    True, 
                    args.save_media,
                    args.save_results
                )
                summary = process_pose_video_result(result, file_path, video_bytes)
            else:
                result = detect_pose_in_video(
                    file_path, 
                    api_url, 
                    False, 
                    args.save_media,
                    args.save_results
                )
                summary = process_pose_video_result(result, file_path)
        
        # Print the summary
        print("\n" + summary)
        
    except Exception as e:
        print(f"Error processing file: {e}")
