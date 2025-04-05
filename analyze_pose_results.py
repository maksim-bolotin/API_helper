"""
Utility script for analyzing pose detection results from saved JSON files.
This script helps visualize and analyze the results of pose detection operations
that were previously saved using send_pose.py or send_pose_directory.py.
"""
import json
import os
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional


def load_json_result(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON result file saved by the pose detection API.
    
    Args:
        file_path: Path to the JSON result file
        
    Returns:
        Dictionary containing the parsed JSON data
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return {}


def load_summary_file(directory: str) -> Dict[str, Any]:
    """
    Load the summary JSON file created by send_pose_directory.py.
    
    Args:
        directory: Directory path where the summary file is located
        
    Returns:
        Dictionary containing the parsed summary data
    """
    summary_path = Path(directory) / "pose_detection_summary.json"
    if not summary_path.exists():
        print(f"Summary file not found at {summary_path}")
        return {}
    
    try:
        with open(summary_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading summary file: {e}")
        return {}


def generate_action_report(summary_data: Dict[str, Any], output_file: str = None) -> str:
    """
    Generate a text report of action statistics from summary data.
    
    Args:
        summary_data: Summary data dictionary
        output_file: Optional path to save the report
        
    Returns:
        Report text
    """
    if not summary_data or "statistics" not in summary_data:
        return "No valid summary data found."
    
    stats = summary_data["statistics"]
    actions = stats.get("actions", {})
    
    if not actions:
        return "No actions detected in the processed files."
    
    # Format the report
    report = "=== Pose Detection Action Report ===\n\n"
    report += f"Total files processed: {stats.get('total_files', 0)}\n"
    report += f"Total poses detected: {stats.get('total_poses_detected', 0)}\n"
    report += f"Processing time: {stats.get('processing_time', 0):.2f} seconds\n\n"
    
    report += "Action Summary:\n"
    report += "-" * 40 + "\n"
    for action, count in sorted(actions.items(), key=lambda x: x[1], reverse=True):
        report += f"{action}: {count}\n"
    
    # Save to file if requested
    if output_file:
        try:
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"Report saved to {output_file}")
        except Exception as e:
            print(f"Error saving report: {e}")
    
    return report


def list_result_files(directory: str) -> List[Path]:
    """
    Find all pose result JSON files in a directory.
    
    Args:
        directory: Directory path to search
        
    Returns:
        List of paths to result files
    """
    dir_path = Path(directory)
    return list(dir_path.glob("*pose_result.json"))


def summarize_file_results(result_files: List[Path]) -> Dict[str, Any]:
    """
    Generate a summary of results from multiple result files.
    
    Args:
        result_files: List of paths to result files
        
    Returns:
        Summary dictionary
    """
    summary = {
        "total_files": len(result_files),
        "total_poses": 0,
        "actions": {},
        "files_with_poses": 0,
        "files_with_errors": 0
    }
    
    for file_path in result_files:
        data = load_json_result(str(file_path))
        
        if "detail" in data:
            # Error in this file
            summary["files_with_errors"] += 1
            continue
        
        pose_count = data.get("count", 0)
        summary["total_poses"] += pose_count
        
        if pose_count > 0:
            summary["files_with_poses"] += 1
        
        # Collect action data
        actions = data.get("detected_actions", {})
        for action, count in actions.items():
            if action not in summary["actions"]:
                summary["actions"][action] = 0
            summary["actions"][action] += count
    
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze pose detection results')
    
    parser.add_argument('directory', help='Directory containing pose detection results')
    parser.add_argument('--output', help='Output file for the report')
    parser.add_argument('--list', action='store_true', help='List all result files')
    parser.add_argument('--file', help='Analyze a specific result file')
    
    args = parser.parse_args()
    
    if args.file:
        # Analyze a specific file
        data = load_json_result(args.file)
        if data:
            print(f"File: {args.file}")
            print(f"Poses detected: {data.get('count', 0)}")
            
            if "poses" in data:
                for i, pose in enumerate(data["poses"]):
                    print(f"  Pose {i+1}:")
                    print(f"    Confidence: {pose.get('confidence', 0):.2f}")
                    print(f"    Action: {pose.get('action', 'Unknown')}")
                    print(f"    Landmarks: {len(pose.get('landmarks', []))}")
            
            if "detected_actions" in data:
                print("\nDetected actions:")
                for action, count in data["detected_actions"].items():
                    print(f"  {action}: {count}")
    
    elif args.list:
        # List all result files
        files = list_result_files(args.directory)
        print(f"Found {len(files)} result files in {args.directory}:")
        for file in files:
            data = load_json_result(str(file))
            pose_count = data.get("count", 0)
            print(f"  {file.name}: {pose_count} poses")
    
    else:
        # General analysis
        summary = load_summary_file(args.directory)
        
        if not summary:
            # Create summary from individual files
            print("No summary file found. Creating summary from individual files...")
            files = list_result_files(args.directory)
            if files:
                custom_summary = summarize_file_results(files)
                report = f"=== Custom Pose Detection Summary ===\n\n"
                report += f"Total files: {custom_summary['total_files']}\n"
                report += f"Files with poses: {custom_summary['files_with_poses']}\n"
                report += f"Files with errors: {custom_summary['files_with_errors']}\n"
                report += f"Total poses detected: {custom_summary['total_poses']}\n\n"
                
                report += "Action Summary:\n"
                report += "-" * 40 + "\n"
                for action, count in sorted(custom_summary["actions"].items(), key=lambda x: x[1], reverse=True):
                    report += f"{action}: {count}\n"
                
                print(report)
                
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(report)
                    print(f"Report saved to {args.output}")
            else:
                print(f"No pose detection result files found in {args.directory}")
        else:
            # Use existing summary
            report = generate_action_report(summary, args.output)
            print(report)
