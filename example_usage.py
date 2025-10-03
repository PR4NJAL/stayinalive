#!/usr/bin/env python3
"""
Example usage of the modular CPR Assistant components.

This script demonstrates how to use individual components
without running the full application.
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enums import CameraAngle, CPRMode
from config import COLORS, TARGET_COMPRESSION_RATE
from detection import PoseDetector, HandDetector, CameraManager
from analysis import CPRAnalyzer
from visualization import CPRVisualizer

def example_enum_usage() -> None:
    """Demonstrate enum usage"""
    print("=== Enum Usage Example ===")
    
    # Camera angles
    overhead = CameraAngle.OVERHEAD
    side_view = CameraAngle.SIDE_VIEW
    print(f"Overhead angle: {overhead.value}")
    print(f"Side view angle: {side_view.value}")
    
    # CPR modes
    positioning = CPRMode.POSITIONING
    compression = CPRMode.COMPRESSION
    print(f"Positioning mode: {positioning.value}")
    print(f"Compression mode: {compression.value}")

def example_config_usage() -> None:
    """Demonstrate configuration usage"""
    print("\n=== Configuration Usage Example ===")
    
    print(f"Target compression rate: {TARGET_COMPRESSION_RATE}")
    print(f"Available colors: {list(COLORS.keys())}")
    print(f"Green color (BGR): {COLORS['green']}")

def example_detection_usage() -> None:
    """Demonstrate detection component usage"""
    print("\n=== Detection Components Example ===")
    
    # Initialize detectors
    pose_detector = PoseDetector()
    hand_detector = HandDetector()
    
    print("Pose detector initialized")
    print("Hand detector initialized")
    
    # Note: In a real application, you would process frames here
    print("(Frame processing would happen here)")

def example_analysis_usage() -> None:
    """Demonstrate analysis component usage"""
    print("\n=== Analysis Component Example ===")
    
    analyzer = CPRAnalyzer()
    print("CPR analyzer initialized")
    
    # Reset counters
    analyzer.reset_counters()
    print("Counters reset")
    
    # Reset baseline
    analyzer.reset_baseline()
    print("Baseline reset")

def example_visualization_usage() -> None:
    """Demonstrate visualization component usage"""
    print("\n=== Visualization Component Example ===")
    
    visualizer = CPRVisualizer()
    print("CPR visualizer initialized")
    print(f"Available colors: {list(visualizer.colors.keys())}")

def example_camera_usage() -> None:
    """Demonstrate camera management"""
    print("\n=== Camera Management Example ===")
    
    try:
        camera_manager = CameraManager()
        print("Camera manager initialized")
        
        # Note: In a real application, you would read frames here
        print("(Frame reading would happen here)")
        
        # Clean up
        camera_manager.release()
        print("Camera resources released")
    except Exception as e:
        print(f"Camera initialization failed: {e}")
        print("(This is expected if no camera is available)")

def main() -> None:
    """Run all examples"""
    print("🫀 CPR Assistant - Modular Components Example")
    print("=" * 50)
    
    example_enum_usage()
    example_config_usage()
    example_detection_usage()
    example_analysis_usage()
    example_visualization_usage()
    example_camera_usage()
    
    print("\n" + "=" * 50)
    print("Example completed successfully!")
    print("\nTo run the full application, use: python main.py")

if __name__ == "__main__":
    main()
