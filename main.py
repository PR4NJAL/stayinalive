import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui import CPRApp, CPRMainWindow
from cpr_assistant import AdvancedCPRAssistant

def run_cpr_assistant():
    """Run the CPR assistant application"""
    try:
        assistant = AdvancedCPRAssistant()
        assistant.run()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure webcam is connected and properly configured")

def run_kivy_app():
    """Run the Kivy UI application"""
    app = CPRApp()
    app.run()

if __name__ == '__main__':
    print("🫀 Advanced CPR Assistant Starting...")
    print("Multi-angle CPR training system")
    print("Supports both overhead positioning and side-view compression monitoring")
    print("\nChoose mode:")
    print("1. Run CPR Assistant (Computer Vision)")
    print("2. Run Kivy UI Application")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        # Installation check
        try:
            import cv2
            import mediapipe as mp
        except ImportError as e:
            print("Missing required packages. Please install:")
            print("pip install opencv-python mediapipe")
            sys.exit(1)
        
        run_cpr_assistant()
    elif choice == "2":
        try:
            import kivy
        except ImportError as e:
            print("Missing required packages. Please install:")
            print("pip install kivy")
            sys.exit(1)
        
        run_kivy_app()
    else:
        print("Invalid choice. Please run again and choose 1 or 2.")