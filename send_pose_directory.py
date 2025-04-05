"""
Script for processing multiple files in a directory with the pose detection API.
This utility allows users to send multiple images or videos from a directory
to the pose detection API and retrieve the detection results.
"""
import requests
import json
import os
import argparse
from pathlib import Path
import time
import shutil
from typing import Dict, List, Tuple, Optional, Union, Any


def detect_pose_in_image(
    image_path: str, 
    api_url: str = "http://localhost:8001/detect/pose/image",
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
        save_image (bool): If True, save the processed image on the server
        save_results (bool): If True, save detailed results to JSON on server

    Returns:
        Union[Dict, Tuple[Dict, bytes]]: 
            - If return_image=False: JSON response with detection results
            - If return_image=True: Tuple of (JSON response, image bytes)
    """
    # Check if the file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Prepare the files for upload
    with open(image_path, 'rb') as file_handle:
        files = {
            'image': (Path(image_path).name, file_handle, 'image/jpeg')
        }

        # Set up parameters
        params = {}
        if save_image:
            params['save_image'] = 'true'
        if save_results:
            params['save_results'] = 'true'

        try:
            # First make a call to get the JSON data
            response = requests.post(api_url, files=files, params=params)
            response.raise_for_status()
            json_response = response.json()
            
            # If return_image is True, make a second call to get the image
            if return_image:
                # Reopen the file for the second request
                with open(image_path, 'rb') as file_handle:
                    files = {
                        'image': (Path(image_path).name, file_handle, 'image/jpeg')
                    }
                    # Add return_image parameter
                    img_params = params.copy()
                    img_params['return_image'] = 'true'
                    
                    try:
                        # Send request with return_image parameter
                        img_response = requests.post(api_url, files=files, params=img_params)
                        img_response.raise_for_status()
                        
                        # Check if we got an image or an error
                        if img_response.headers.get('content-type') == 'application/json':
                            print(f"Warning: Received JSON instead of image for {Path(image_path).name}: {img_response.text}")
                            return json_response, None
                        
                        # Return both the JSON data and image bytes
                        return json_response, img_response.content
                    except requests.exceptions.RequestException as e:
                        print(f"Error getting processed image for {Path(image_path).name}: {e}")
                        return json_response, None
            else:
                # Just return the JSON result
                return json_response

        except requests.exceptions.RequestException as e:
            print(f"Error making request for {Path(image_path).name}: {e}")
            
            # Try to extract error details
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    return error_json
                except:
                    pass
            
            return {"detail": str(e)}


def detect_pose_in_video(
    video_path: str,
    api_url: str = "http://localhost:8001/detect/pose/video",
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
        save_video (bool): If True, save the processed video on the server
        save_results (bool): If True, save detailed results to JSON on server

    Returns:
        Union[Dict, Tuple[Dict, bytes]]: 
            - If return_video=False: JSON response with detection results
            - If return_video=True: Tuple of (JSON response, video bytes)
    """
    # Check if the file exists
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Prepare the files for upload
    with open(video_path, 'rb') as file_handle:
        files = {
            'video': (Path(video_path).name, file_handle, 'video/mp4')
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
            # Make the request
            response = requests.post(api_url, files=files, params=params)
            response.raise_for_status()
            
            # Check if we got a video or JSON
            if response.headers.get('content-type') == 'video/mp4':
                # For return_video=true, we've received the video directly
                
                # Make a second request to get the JSON data
                with open(video_path, 'rb') as file_handle:
                    files = {
                        'video': (Path(video_path).name, file_handle, 'video/mp4')
                    }
                    # Remove return_video flag to get JSON
                    json_params = params.copy()
                    json_params.pop('return_video', None)
                    
                    json_response = requests.post(api_url, files=files, params=json_params)
                    json_response.raise_for_status()
                    json_data = json_response.json()
                
                return json_data, response.content
            else:
                # Parse JSON response
                json_response = response.json()
                return json_response

        except requests.exceptions.RequestException as e:
            print(f"Error making request for {Path(video_path).name}: {e}")
            
            # Try to extract error details
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    return error_json
                except:
                    pass
            
            return {"detail": str(e)}


def process_directory(
    directory_path: str,
    api_url_image: str = "http://localhost:8001/detect/pose/image",
    api_url_video: str = "http://localhost:8001/detect/pose/video",
    image_extensions: Tuple[str, ...] = ('.jpg', '.jpeg', '.png'),
    video_extensions: Tuple[str, ...] = ('.mp4', '.avi', '.mov', '.wmv', '.mkv'),
    delay: float = 0.5,
    output_dir: str = None,
    return_media: bool = False,
    save_media: bool = False,
    save_results: bool = False,
    mode: str = 'both'
) -> Dict[str, Any]:
    """
    Process all images and/or videos in a directory for pose detection.

    Args:
        directory_path (str): Path to the directory containing media files
        api_url_image (str): URL of the pose detection image endpoint
        api_url_video (str): URL of the pose detection video endpoint
        image_extensions (tuple): File extensions for images to process
        video_extensions (tuple): File extensions for videos to process
        delay (float): Delay between requests in seconds
        output_dir (str): Optional directory to save results to (defaults to same as input)
        return_media (bool): If True, request and save processed media with detections
        save_media (bool): If True, save processed media on server
        save_results (bool): If True, save detailed results in JSON on server
        mode (str): Processing mode - 'image', 'video', or 'both'

    Returns:
        dict: Dictionary with file paths as keys and detection results as values
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

    # Create processed directories if returning media
    if return_media:
        processed_dir = output_directory / "processed_poses"
        processed_dir.mkdir(exist_ok=True)
    
    # Find all media files in the directory
    image_files = []
    video_files = []
    
    if mode in ['image', 'both']:
        for ext in image_extensions:
            image_files.extend(directory.glob(f"*{ext}"))
            image_files.extend(directory.glob(f"*{ext.upper()}"))
    
    if mode in ['video', 'both']:
        for ext in video_extensions:
            video_files.extend(directory.glob(f"*{ext}"))
            video_files.extend(directory.glob(f"*{ext.upper()}"))

    total_files = len(image_files) + len(video_files)
    if total_files == 0:
        print(f"No media files found in {directory_path} for mode '{mode}'")
        return {}

    print(f"Found {len(image_files)} images and {len(video_files)} videos to process in {directory_path}")

    # Set up a stats dictionary
    stats = {
        "total_files": total_files,
        "images_processed": len(image_files),
        "videos_processed": len(video_files),
        "total_poses_detected": 0,
        "actions": {},
        "processing_time": 0,
        "errors": []
    }
    
    # Process each file
    start_time = time.time()
    results = {}
    
    # Process images
    for i, image_path in enumerate(sorted(image_files), 1):
        print(f"Processing image {i}/{len(image_files)}: {image_path.name}")
        image_start_time = time.time()
        
        try:
            if return_media:
                # Get both JSON and image
                result, image_bytes = detect_pose_in_image(
                    str(image_path), 
                    api_url_image, 
                    True, 
                    save_media,
                    save_results
                )
                
                # Save processed image if available
                if image_bytes:
                    output_image = processed_dir / f"{image_path.stem}_processed{image_path.suffix}"
                    with open(output_image, 'wb') as f:
                        f.write(image_bytes)
                    print(f"  - Saved processed image to {output_image}")
            else:
                # Get only JSON result
                result = detect_pose_in_image(
                    str(image_path), 
                    api_url_image, 
                    False, 
                    save_media,
                    save_results
                )
            
            # Save the individual result to a JSON file
            output_json = output_directory / f"{image_path.stem}_pose_result.json"
            with open(output_json, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Add to results
            results[str(image_path)] = result
            
            # Update statistics
            if isinstance(result, dict):
                if "detail" in result:
                    stats["errors"].append({
                        "file": str(image_path),
                        "error": result["detail"]
                    })
                else:
                    stats["total_poses_detected"] += result.get("count", 0)
                    
                    # Track actions
                    if "detected_actions" in result and result["detected_actions"]:
                        for action, count in result["detected_actions"].items():
                            if action not in stats["actions"]:
                                stats["actions"][action] = 0
                            stats["actions"][action] += count
            
            image_time = time.time() - image_start_time
            print(f"  - Processing time: {image_time:.2f} seconds")

        except Exception as e:
            print(f"  - Error processing image: {e}")
            stats["errors"].append({
                "file": str(image_path),
                "error": str(e)
            })
        
        # Add delay between requests
        if i < len(image_files) and delay > 0:
            time.sleep(delay)
    
    # Process videos
    for i, video_path in enumerate(sorted(video_files), 1):
        print(f"Processing video {i}/{len(video_files)}: {video_path.name}")
        video_start_time = time.time()
        
        try:
            if return_media:
                # Get both JSON and video
                result, video_bytes = detect_pose_in_video(
                    str(video_path), 
                    api_url_video, 
                    True, 
                    save_media,
                    save_results
                )
                
                # Save processed video if available
                if video_bytes:
                    output_video = processed_dir / f"{video_path.stem}_processed{video_path.suffix}"
                    with open(output_video, 'wb') as f:
                        f.write(video_bytes)
                    print(f"  - Saved processed video to {output_video}")
            else:
                # Get only JSON result
                result = detect_pose_in_video(
                    str(video_path), 
                    api_url_video, 
                    False, 
                    save_media,
                    save_results
                )
            
            # Save the individual result to a JSON file
            output_json = output_directory / f"{video_path.stem}_pose_result.json"
            with open(output_json, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Add to results
            results[str(video_path)] = result
            
            # Update statistics
            if isinstance(result, dict):
                if "detail" in result:
                    stats["errors"].append({
                        "file": str(video_path),
                        "error": result["detail"]
                    })
                else:
                    stats["total_poses_detected"] += result.get("count", 0)
                    
                    # Track actions
                    if "detected_actions" in result and result["detected_actions"]:
                        for action, count in result["detected_actions"].items():
                            if action not in stats["actions"]:
                                stats["actions"][action] = 0
                            stats["actions"][action] += count
            
            video_time = time.time() - video_start_time
            print(f"  - Processing time: {video_time:.2f} seconds")

        except Exception as e:
            print(f"  - Error processing video: {e}")
            stats["errors"].append({
                "file": str(video_path),
                "error": str(e)
            })
        
        # Add delay between requests
        if i < len(video_files) and delay > 0:
            time.sleep(delay)

    # Calculate total processing time
    stats["processing_time"] = time.time() - start_time

    # Create a summary file with detailed statistics
    summary_path = output_directory / "pose_detection_summary.json"
    with open(summary_path, 'w') as f:
        summary = {
            "statistics": stats,
            "results_by_file": {
                str(path): {
                    "poses": result.get("count", 0) if isinstance(result, dict) else 0,
                    "actions": result.get("detected_actions", {}) if isinstance(result, dict) else {},
                    "results_file": result.get("results_file") if isinstance(result, dict) else None,
                    "media_path": result.get("image_path", result.get("video_path")) if isinstance(result, dict) else None
                } for path, result in results.items()
            }
        }
        json.dump(summary, f, indent=2)

    print(f"\nProcessing complete. Processed {len(image_files)} images and {len(video_files)} videos in {stats['processing_time']:.2f} seconds.")
    print(f"Total poses detected: {stats['total_poses_detected']}")
    
    if stats["actions"]:
        print("\nDetected actions:")
        for action, count in sorted(stats["actions"].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {action}: {count} instances")
    
    if stats["errors"]:
        print(f"\nErrors encountered: {len(stats['errors'])}")
        for error in stats["errors"][:5]:  # Show only first 5 errors
            print(f"  - {Path(error['file']).name}: {error['error']}")
        if len(stats["errors"]) > 5:
            print(f"  ... and {len(stats['errors']) - 5} more errors")
    
    print(f"\nSummary saved to {summary_path}")

    return results


def create_action_chart(stats: Dict[str, Any], output_dir: Path):
    """
    Create a simple text-based chart of detected actions.
    
    Args:
        stats: Statistics dictionary with action counts
        output_dir: Directory to save the chart
    """
    # Extract action data
    if not stats.get("actions"):
        print("No actions detected, chart not created")
        return
        
    # Sort actions by count (descending)
    actions = sorted(stats["actions"].items(), key=lambda x: x[1], reverse=True)
    
    # Determine the maximum length of action names for formatting
    max_name_len = max(len(name) for name, _ in actions)
    max_count = max(count for _, count in actions)
    
    # Create chart file
    chart_path = output_dir / "action_summary.txt"
    with open(chart_path, 'w') as f:
        f.write(f"{'Action':{max_name_len}} | Count | Chart\n")
        f.write("-" * (max_name_len + 2 + 7 + 2 + 50) + "\n")
        
        # Generate chart lines
        for action, count in actions:
            # Calculate bar length (proportional to count, max 40 chars)
            bar_length = int((count / max_count) * 40) if max_count > 0 else 0
            bar = "#" * bar_length
            
            f.write(f"{action:{max_name_len}} | {count:5} | {bar}\n")
    
    print(f"\nAction summary chart saved to {chart_path}")


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process multiple files in a directory for pose detection')
    
    parser.add_argument('directory_path', help='Path to the directory containing media files to process')
    parser.add_argument('--image-url', default="http://localhost:8001/detect/pose/image",
                        help='URL of the pose detection image API endpoint')
    parser.add_argument('--video-url', default="http://localhost:8001/detect/pose/video",
                        help='URL of the pose detection video API endpoint')
    parser.add_argument('--delay', type=float, default=0.5,
                        help='Delay between processing files (seconds)')
    parser.add_argument('--image-formats', default='jpg,jpeg,png',
                        help='Comma-separated list of image formats to process')
    parser.add_argument('--video-formats', default='mp4,avi,mov,wmv,mkv',
                        help='Comma-separated list of video formats to process')
    parser.add_argument('--output', help='Directory to save results (default: same as input)')
    parser.add_argument('--return-media', action='store_true',
                        help='Request and save processed media with pose markers')
    parser.add_argument('--save-media', action='store_true',
                        help='Save processed media on the server')
    parser.add_argument('--save-results', action='store_true',
                        help='Save detailed results in JSON on server')
    parser.add_argument('--mode', choices=['image', 'video', 'both'], default='both',
                        help='Process only images, only videos, or both')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Convert formats strings to tuples
    image_formats = tuple(f'.{fmt}' for fmt in args.image_formats.split(','))
    video_formats = tuple(f'.{fmt}' for fmt in args.video_formats.split(','))
    
    # Process the directory
    try:
        print(f"Starting to process directory: {args.directory_path}")
        print(f"Mode: {args.mode}, Return media: {args.return_media}, Save media: {args.save_media}")
        
        results = process_directory(
            args.directory_path,
            args.image_url,
            args.video_url,
            image_formats,
            video_formats,
            args.delay,
            args.output,
            args.return_media,
            args.save_media,
            args.save_results,
            args.mode
        )
        
        # Load summary for action chart
        output_dir = Path(args.output) if args.output else Path(args.directory_path)
        summary_path = output_dir / "pose_detection_summary.json"
        
        if summary_path.exists():
            with open(summary_path, 'r') as f:
                summary = json.load(f)
                stats = summary.get("statistics", {})
                create_action_chart(stats, output_dir)
        
        print("\nProcessing completed successfully!")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
