import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cpr_assistant import AdvancedCPRAssistant

def run_cpr_assistant():
    """Run the CPR assistant application"""
    try:
        assistant = AdvancedCPRAssistant()
        assistant.run()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure webcam is connected and properly configured")

if __name__ == '__main__':
    print("🫀 Advanced CPR Assistant Starting...")
    print("Multi-angle CPR training system")
    print("Supports both overhead positioning and side-view compression monitoring")
       
    # Installation check
    try:
        import cv2
        import mediapipe as mp
    except ImportError as e:
        print("Missing required packages. Please install:")
        print("pip install opencv-python mediapipe")
        sys.exit(1)
        
    run_cpr_assistant()