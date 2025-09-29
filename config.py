# Configuration constants for CPR Assistant

# CPR Parameters
TARGET_COMPRESSION_RATE = 110
TARGET_DEPTH_CM = 5.0

# MediaPipe Configuration
HANDS_CONFIG = {
    'static_image_mode': False,
    'max_num_hands': 2,
    'min_detection_confidence': 0.7,
    'min_tracking_confidence': 0.7
}

POSE_CONFIG = {
    'static_image_mode': False,
    'min_detection_confidence': 0.7,
    'min_tracking_confidence': 0.7
}

HOLISTIC_CONFIG = {
    'static_image_mode': False,
    'min_detection_confidence': 0.7,
    'min_tracking_confidence': 0.7
}

# Camera Configuration
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

# Tracking Configuration
COMPRESSION_HISTORY_SIZE = 30
COMPRESSION_DEPTHS_SIZE = 20
COMPRESSION_TIMES_SIZE = 20

# Colors (BGR format for OpenCV)
COLORS = {
    'green': (0, 255, 0),
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'yellow': (0, 255, 255),
    'orange': (0, 165, 255),
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'purple': (255, 0, 255)
}

# Pose Landmarks for Chest Detection
CHEST_LANDMARKS = {
    'left_shoulder': 11,
    'right_shoulder': 12,
    'chest_center': None  # Will be calculated
}
