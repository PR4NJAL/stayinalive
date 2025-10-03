import cv2
import numpy as np
import mediapipe as mp
from config import HANDS_CONFIG, POSE_CONFIG, HOLISTIC_CONFIG, CHEST_LANDMARKS

MatLike = np.typing.NDArray[np.uint8]

class PoseDetector:
    """Handles pose detection and landmark extraction"""
    
    def __init__(self) -> None:
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(**POSE_CONFIG)
        self.mp_draw = mp.solutions.drawing_utils
    
    def detect_chest_from_pose(self, pose_landmarks, frame_shape) -> tuple[tuple[int, int], int]:
        """Detect chest center from pose landmarks"""
        if not pose_landmarks:
            return None, None
            
        height, width = frame_shape[:2]
        
        # Get shoulder landmarks
        left_shoulder = pose_landmarks.landmark[CHEST_LANDMARKS['left_shoulder']]
        right_shoulder = pose_landmarks.landmark[CHEST_LANDMARKS['right_shoulder']]
        
        # Calculate chest center (midpoint between shoulders, slightly below)
        chest_center_x = int((left_shoulder.x + right_shoulder.x) / 2 * width)
        chest_center_y = int((left_shoulder.y + right_shoulder.y) / 2 * height + 
                           abs(left_shoulder.y - right_shoulder.y) * height * 0.3)
        
        # Calculate chest width for scale reference
        chest_width = int(abs(left_shoulder.x - right_shoulder.x) * width)
        
        return (chest_center_x, chest_center_y), chest_width
    
    def process_frame(self, frame_rgb) -> any:
        """Process frame for pose detection"""
        return self.pose.process(frame_rgb)
    
    def draw_landmarks(self, frame, pose_landmarks) -> None:
        """Draw pose landmarks on frame"""
        if pose_landmarks:
            self.mp_draw.draw_landmarks(
                frame, pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2),
                connection_drawing_spec=self.mp_draw.DrawingSpec(color=(0, 255, 255), thickness=1)
            )

class HandDetector:
    """Handles hand detection and landmark extraction"""
    
    def __init__(self) -> None:
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(**HANDS_CONFIG)
        self.mp_draw = mp.solutions.drawing_utils
    
    def get_hand_center(self, landmarks, width, height) -> tuple[int, int]:
        """Get center point of hand landmarks"""
        x_coords = [lm.x * width for lm in landmarks.landmark]
        y_coords = [lm.y * height for lm in landmarks.landmark]
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)
        return (int(center_x), int(center_y))
    
    def process_frame(self, frame_rgb) -> any:
        """Process frame for hand detection"""
        return self.hands.process(frame_rgb)
    
    def draw_landmarks(self, frame, hand_landmarks) -> None:
        """Draw hand landmarks on frame"""
        if hand_landmarks:
            self.mp_draw.draw_landmarks(
                frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

class HolisticDetector:
    """Handles holistic detection (pose + hands + face)"""
    
    def __init__(self) -> None:
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(**HOLISTIC_CONFIG)
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
    
    def process_frame(self, frame_rgb) -> any:
        """Process frame for holistic detection"""
        return self.holistic.process(frame_rgb)
    
    def draw_pose_landmarks(self, frame, pose_landmarks) -> None:
        """Draw pose landmarks on frame"""
        if pose_landmarks:
            self.mp_draw.draw_landmarks(
                frame, pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2),
                connection_drawing_spec=self.mp_draw.DrawingSpec(color=(0, 255, 255), thickness=1)
            )
    
    def draw_hand_landmarks(self, frame, hand_landmarks) -> None:
        """Draw hand landmarks on frame"""
        if hand_landmarks:
            self.mp_draw.draw_landmarks(
                frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

class CameraManager:
    """Handles camera initialization and configuration"""
    
    def __init__(self) -> None:
        self.cap = None
        self.initialize_camera()
    
    def initialize_camera(self) -> None:
        """Initialize camera with proper settings"""
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    def read_frame(self) -> tuple[bool, MatLike]:
        """Read frame from camera"""
        return self.cap.read()
    
    def release(self) -> None:
        """Release camera resources"""
        if self.cap:
            self.cap.release()
