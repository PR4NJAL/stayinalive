import cv2
import mediapipe as mp
import time
import math
from collections import deque
import pygame
# import threading
from enum import Enum

class CameraAngle(Enum):
    OVERHEAD = "overhead"  # Camera above CPR recipient, hands positioning
    SIDE_VIEW = "side_view"  # Camera from side, compression monitoring

class CPRMode(Enum):
    POSITIONING = "positioning"  # Hand placement guidance
    COMPRESSION = "compression"  # Compression rate/depth monitoring

class AdvancedCPRAssistant:
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.mp_holistic = mp.solutions.holistic
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        self.mp_draw = mp.solutions.drawing_utils
        
        # Camera setup
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Current mode and angle
        self.current_angle = CameraAngle.OVERHEAD
        self.current_mode = CPRMode.POSITIONING
        
        # CPR parameters
        self.target_compression_rate = 110
        self.target_depth_cm = 5.0
        self.compression_depth_pixels = 0  # Will be calibrated
        
        # Pose landmarks for chest detection
        self.chest_landmarks = {
            'left_shoulder': 11,
            'right_shoulder': 12,
            'chest_center': None  # Will be calculated
        }
        
        # Tracking for overhead mode (positioning)
        self.detected_chest_center = None
        self.chest_width = None
        self.hand_positions = []
        self.positioning_accuracy = 0
        
        # Tracking for side view mode (compression)
        self.compression_history = deque(maxlen=30)  # Last 30 compressions
        self.compression_depths = deque(maxlen=20)
        self.compression_times = deque(maxlen=20)
        self.compression_count = 0
        self.current_rate = 0
        self.average_depth = 0
        self.is_compressing = False
        self.baseline_chest_y = None  # Chest position when not compressed
        
        # Calibration
        self.calibrated = False
        self.calibration_frames = 0
        self.calibration_data = []
        
        # Initialize pygame for audio
        pygame.mixer.init() # NOTE: Just realised do we even need this?
        
        # Colors
        self.colors = {
            'green': (0, 255, 0),
            'red': (0, 0, 255),
            'blue': (255, 0, 0),
            'yellow': (0, 255, 255),
            'orange': (0, 165, 255),
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'purple': (255, 0, 255)
        }
        
        print("Advanced CPR Assistant initialized")
        print("Current Mode: OVERHEAD POSITIONING")
        self.print_controls()
    
    def print_controls(self):
        """Print current controls based on mode"""
        print("\n=== CONTROLS ===")
        if self.current_angle == CameraAngle.OVERHEAD:
            print("OVERHEAD MODE - Hand Positioning:")
            print("'1' - Switch to SIDE VIEW mode")
            print("'c' - Calibrate chest detection")
            print("'s' - Start/Stop positioning guidance")
        else:
            print("SIDE VIEW MODE - Compression Monitoring:")
            print("'2' - Switch to OVERHEAD mode")
            print("'c' - Calibrate compression baseline")
            print("'s' - Start/Stop compression monitoring")
        
        print("'r' - Reset all counters")
        print("'e' - Emergency call simulation")
        print("'q' - Quit")
        print("================\n")
    
    def detect_chest_from_pose(self, pose_landmarks, frame_shape):
        """Detect chest center from pose landmarks"""
        if not pose_landmarks:
            return None, None
            
        height, width = frame_shape[:2]
        
        # Get shoulder landmarks
        left_shoulder = pose_landmarks.landmark[self.chest_landmarks['left_shoulder']]
        right_shoulder = pose_landmarks.landmark[self.chest_landmarks['right_shoulder']]
        
        # Calculate chest center (midpoint between shoulders, slightly below)
        chest_center_x = int((left_shoulder.x + right_shoulder.x) / 2 * width)
        chest_center_y = int((left_shoulder.y + right_shoulder.y) / 2 * height + 
                           abs(left_shoulder.y - right_shoulder.y) * height * 0.3)
        
        # Calculate chest width for scale reference
        chest_width = int(abs(left_shoulder.x - right_shoulder.x) * width)
        
        return (chest_center_x, chest_center_y), chest_width
    
    def analyze_hand_positioning_overhead(self, holistic_results, pose_results, frame_shape):
        """Analyze hand positioning from overhead view"""
        if not holistic_results or not holistic_results.pose_landmarks:
            return "No person detected - position CPR recipient in frame"
        
        # Detect chest center from pose
        chest_center, chest_width = self.detect_chest_from_pose(
            holistic_results.pose_landmarks, frame_shape)
        
        if not chest_center:
            return "Cannot detect chest - ensure person is visible"
        
        self.detected_chest_center = chest_center
        self.chest_width = chest_width
        
        if not holistic_results or not holistic_results.left_hand_landmarks and not holistic_results.right_hand_landmarks:
            return "Position hands over chest center for CPR"
        
        # Analyze hand positions
        hand_centers = []
        
        # Check for left hand
        if holistic_results.left_hand_landmarks:
            hand_center = self.get_hand_center(holistic_results.left_hand_landmarks, 
                                             frame_shape[1], frame_shape[0])
            hand_centers.append(hand_center)
        
        # Check for right hand
        if holistic_results.right_hand_landmarks:
            hand_center = self.get_hand_center(holistic_results.right_hand_landmarks, 
                                             frame_shape[1], frame_shape[0])
            hand_centers.append(hand_center)
        
        # Calculate positioning accuracy
        if len(hand_centers) >= 1:
            primary_hand = hand_centers[0]
            distance_from_chest = self.calculate_distance(primary_hand, chest_center)
            
            # Accuracy based on chest width (adaptive to person size)
            tolerance_radius = chest_width * 0.6  # 60% of chest width
            if distance_from_chest <= tolerance_radius:
                self.positioning_accuracy = max(0, 
                    (tolerance_radius - distance_from_chest) / tolerance_radius * 100)
            else:
                self.positioning_accuracy = 0
            
            # Generate feedback
            if len(hand_centers) == 2:
                hand_distance = self.calculate_distance(hand_centers[0], hand_centers[1])
                if hand_distance < chest_width * 0.3:
                    return f"Good! Both hands positioned (Accuracy: {self.positioning_accuracy:.0f}%)"
                else:
                    return "Bring hands closer together on chest center"
            else:
                if self.positioning_accuracy > 80:
                    return f"Excellent positioning! (Accuracy: {self.positioning_accuracy:.0f}%)"
                elif self.positioning_accuracy > 50:
                    return f"Good - adjust toward center (Accuracy: {self.positioning_accuracy:.0f}%)"
                else:
                    return "Move hands to chest center"
        
        return "Position hands over chest"
    
    def analyze_compression_side_view(self, hands_results, pose_results, frame_shape):
        """Analyze compression from side view"""
        if not pose_results or not pose_results.pose_landmarks:
            return "No person detected in side view"
        
        if not hands_results or not hands_results.multi_hand_landmarks:
            return "Position hands visible in side view"
        
        # Get chest reference point from pose (sternum area)
        height, width = frame_shape[:2]
        pose_landmarks = pose_results.pose_landmarks.landmark
        
        # Use midpoint between left/right shoulder as chest reference
        left_shoulder = pose_landmarks[11]
        right_shoulder = pose_landmarks[12]
        chest_ref_y = int((left_shoulder.y + right_shoulder.y) / 2 * height + 
                         abs(left_shoulder.y - right_shoulder.y) * height * 0.4)
        
        # Get hand position (use lowest hand - closest to chest)
        hand_centers = []
        for hand_landmarks in hands_results.multi_hand_landmarks:
            hand_center = self.get_hand_center(hand_landmarks, width, height)
            hand_centers.append(hand_center)
        
        if not hand_centers:
            return "No hands detected"
        
        # Use the hand closest to chest reference
        closest_hand = min(hand_centers, key=lambda h: abs(h[1] - chest_ref_y))
        
        # Initialize baseline if not set
        if self.baseline_chest_y is None:
            self.baseline_chest_y = closest_hand[1]
            return "Baseline set - begin compressions"
        
        # Detect compression
        self.detect_compression_side_view(closest_hand, chest_ref_y)
        
        # Generate feedback
        feedback = []
        
        # Rate feedback
        if self.current_rate > 0:
            if self.current_rate < 100:
                feedback.append(f"Rate: {self.current_rate:.0f}/min - COMPRESS FASTER!")
            elif self.current_rate > 120:
                feedback.append(f"Rate: {self.current_rate:.0f}/min - COMPRESS SLOWER!")
            else:
                feedback.append(f"Rate: {self.current_rate:.0f}/min - GOOD!")
        else:
            feedback.append("Start compressions")
        
        # Depth feedback
        if self.average_depth > 0:
            if self.average_depth < 30:  # pixels, adjust based on calibration
                feedback.append("PRESS HARDER - increase depth")
            elif self.average_depth > 60:
                feedback.append("PRESS SOFTER - too deep")
            else:
                feedback.append("Good compression depth")
        
        feedback.append(f"Total compressions: {self.compression_count}")
        
        return " | ".join(feedback)
    
    def detect_compression_side_view(self, hand_center, chest_ref_y):
        """Detect compression from side view using vertical movement"""
        current_time = time.time()
        current_y = hand_center[1]
        
        # Calculate compression depth relative to baseline
        if self.baseline_chest_y:
            compression_depth = abs(current_y - self.baseline_chest_y)
            
            # Detect compression cycle
            if len(self.compression_history) > 0:
                prev_depth = self.compression_history[-1]['depth']
                
                # Compression detected: significant increase in depth
                if compression_depth > prev_depth + 10 and not self.is_compressing:
                    self.is_compressing = True
                    self.compression_count += 1
                    self.compression_times.append(current_time)
                    self.compression_depths.append(compression_depth)
                    
                    # Calculate rate
                    if len(self.compression_times) >= 2:
                        time_window = self.compression_times[-1] - self.compression_times[0]
                        if time_window > 0:
                            self.current_rate = (len(self.compression_times) - 1) / time_window * 60
                    
                    # Calculate average depth
                    if self.compression_depths:
                        self.average_depth = sum(self.compression_depths) / len(self.compression_depths)
                
                # Release detected: return toward baseline
                elif compression_depth < prev_depth - 5:
                    self.is_compressing = False
            
            # Store current state
            self.compression_history.append({
                'time': current_time,
                'depth': compression_depth,
                'hand_y': current_y
            })
    
    def get_hand_center(self, landmarks, width, height):
        """Get center point of hand landmarks"""
        x_coords = [lm.x * width for lm in landmarks.landmark]
        y_coords = [lm.y * height for lm in landmarks.landmark]
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)
        return (int(center_x), int(center_y))
    
    def calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def draw_overhead_overlay(self, frame, holistic_results, pose_results):
        """Draw overlay for overhead positioning mode"""
        if holistic_results and holistic_results.pose_landmarks:
            # Draw pose landmarks (torso area)
            self.mp_draw.draw_landmarks(
                frame, holistic_results.pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2),
                connection_drawing_spec=self.mp_draw.DrawingSpec(color=(0, 255, 255), thickness=1)
            )
            
            # Draw chest center and target zone
            if self.detected_chest_center and self.chest_width:
                chest_x, chest_y = self.detected_chest_center
                
                # Main target zone (adaptive to chest size)
                target_radius = int(self.chest_width * 0.3)
                cv2.circle(frame, (chest_x, chest_y), target_radius, self.colors['yellow'], 3)
                cv2.circle(frame, (chest_x, chest_y), target_radius//2, self.colors['green'], 2)
                cv2.circle(frame, (chest_x, chest_y), 8, self.colors['red'], -1)
                
                # Labels
                cv2.putText(frame, "CHEST CENTER", 
                           (chest_x - 60, chest_y - target_radius - 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.colors['white'], 2)
                cv2.putText(frame, f"TARGET ZONE", 
                           (chest_x - 50, chest_y + target_radius + 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['yellow'], 2)
        
        # Draw hand landmarks and positioning
        if holistic_results:
            # Draw left hand
            if holistic_results.left_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame, holistic_results.left_hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                hand_center = self.get_hand_center(holistic_results.left_hand_landmarks, 
                                                 frame.shape[1], frame.shape[0])
                color = self.colors['green'] if self.positioning_accuracy > 70 else self.colors['red']
                cv2.circle(frame, hand_center, 8, color, -1)
                cv2.circle(frame, hand_center, 15, color, 2)
                
                # Draw connection to chest if detected
                if self.detected_chest_center:
                    cv2.line(frame, hand_center, self.detected_chest_center, color, 2)
            
            # Draw right hand
            if holistic_results.right_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame, holistic_results.right_hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                hand_center = self.get_hand_center(holistic_results.right_hand_landmarks, 
                                                 frame.shape[1], frame.shape[0])
                color = self.colors['green'] if self.positioning_accuracy > 70 else self.colors['red']
                cv2.circle(frame, hand_center, 8, color, -1)
                cv2.circle(frame, hand_center, 15, color, 2)
                
                # Draw connection to chest if detected
                if self.detected_chest_center:
                    cv2.line(frame, hand_center, self.detected_chest_center, color, 2)
    
    def draw_side_view_overlay(self, frame, hands_results, pose_results):
        """Draw overlay for side view compression mode"""
        height, width = frame.shape[:2]
        
        # Draw pose landmarks
        if pose_results and pose_results.pose_landmarks:
            self.mp_draw.draw_landmarks(
                frame, pose_results.pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2)
            )
        
        # Draw compression visualization
        if hands_results and hands_results.multi_hand_landmarks:
            for hand_landmarks in hands_results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                hand_center = self.get_hand_center(hand_landmarks, width, height)
                
                # Draw compression depth indicator
                if self.baseline_chest_y:
                    compression_depth = abs(hand_center[1] - self.baseline_chest_y)
                    
                    # Color based on compression depth
                    if compression_depth < 20:
                        depth_color = self.colors['red']  # Too shallow
                    elif compression_depth > 60:
                        depth_color = self.colors['orange']  # Too deep
                    else:
                        depth_color = self.colors['green']  # Good depth
                    
                    # Draw compression indicator
                    cv2.circle(frame, hand_center, 12, depth_color, -1)
                    cv2.circle(frame, hand_center, 20, depth_color, 3)
                    
                    # Draw baseline reference
                    cv2.line(frame, (0, self.baseline_chest_y), 
                            (width, self.baseline_chest_y), self.colors['blue'], 2)
                    cv2.putText(frame, "BASELINE", (10, self.baseline_chest_y - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['blue'], 1)
        
        # Draw compression metrics
        cv2.putText(frame, f"Rate: {self.current_rate:.0f}/min", 
                   (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.colors['white'], 2)
        cv2.putText(frame, f"Compressions: {self.compression_count}", 
                   (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.colors['white'], 2)
        cv2.putText(frame, f"Avg Depth: {self.average_depth:.0f}px", 
                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.colors['white'], 2)
    
    def draw_feedback(self, frame, feedback_text):
        """Draw feedback text on frame"""
        height, width = frame.shape[:2]
        
        # Split feedback into lines
        lines = feedback_text.split(' | ') if ' | ' in feedback_text else [feedback_text]
        
        # Draw background
        feedback_height = len(lines) * 30 + 20
        cv2.rectangle(frame, (0, height - feedback_height - 10), 
                     (width, height), (0, 0, 0), -1)
        
        # Draw text lines
        for i, line in enumerate(lines):
            y_pos = height - feedback_height + (i * 30) + 25
            cv2.putText(frame, line, (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.colors['white'], 2)
    
    def switch_angle(self, new_angle):
        """Switch camera angle and mode"""
        self.current_angle = new_angle
        if new_angle == CameraAngle.OVERHEAD:
            self.current_mode = CPRMode.POSITIONING
            print("\n🔄 Switched to OVERHEAD mode - Hand Positioning")
        else:
            self.current_mode = CPRMode.COMPRESSION
            print("\n🔄 Switched to SIDE VIEW mode - Compression Monitoring")
        
        self.print_controls()
        
        # Reset relevant tracking
        if new_angle == CameraAngle.SIDE_VIEW:
            self.baseline_chest_y = None
            self.compression_history.clear()
    
    def emergency_call_simulation(self):
        """Simulate emergency call"""
        print("\n🚨 EMERGENCY CALL INITIATED 🚨")
        print("Calling emergency services...")
        print(f"CPR Status: {self.compression_count} compressions delivered")
        if self.current_rate > 0:
            print(f"Current rate: {self.current_rate:.0f}/min")
        print("Location: [GPS coordinates would be sent]")
    
    def run(self):
        """Main application loop"""
        guidance_active = False
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame based on current mode
            if guidance_active:
                if self.current_angle == CameraAngle.OVERHEAD:
                    # Use holistic for both pose and hands
                    holistic_results = self.holistic.process(frame_rgb)
                    
                    # Analyze positioning (pass correct attributes)
                    feedback = self.analyze_hand_positioning_overhead(
                        holistic_results, holistic_results, frame.shape)
                    
                    # Draw overlay
                    self.draw_overhead_overlay(frame, holistic_results, holistic_results)
                    
                else:  # SIDE_VIEW
                    # Process hands and pose separately for better performance
                    hands_results = self.hands.process(frame_rgb)
                    pose_results = self.pose.process(frame_rgb)
                    
                    # Analyze compressions
                    feedback = self.analyze_compression_side_view(
                        hands_results, pose_results, frame.shape)
                    
                    # Draw overlay
                    self.draw_side_view_overlay(frame, hands_results, pose_results)
                
                # Draw feedback
                self.draw_feedback(frame, feedback)
            
            # Draw mode indicator
            mode_text = f"Mode: {self.current_angle.value.upper()}"
            cv2.putText(frame, mode_text, (frame.shape[1] - 250, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.colors['yellow'], 2)
            
            # Draw status
            status = "ACTIVE" if guidance_active else "INACTIVE"
            status_color = self.colors['green'] if guidance_active else self.colors['red']
            cv2.putText(frame, f"Status: {status}", (frame.shape[1] - 200, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
            
            # Show frame
            cv2.imshow('Advanced CPR Assistant', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('1'):
                self.switch_angle(CameraAngle.OVERHEAD)
            elif key == ord('2'):
                self.switch_angle(CameraAngle.SIDE_VIEW)
            elif key == ord('s'):
                guidance_active = not guidance_active
                status = "ACTIVE" if guidance_active else "INACTIVE"
                print(f"\nGuidance: {status}")
            elif key == ord('e'):
                self.emergency_call_simulation()
            elif key == ord('r'):
                self.reset_counters()
            elif key == ord('c'):
                self.calibrate_current_mode()
        
        self.cleanup()
    
    def reset_counters(self):
        """Reset all counters and tracking"""
        self.compression_count = 0
        self.compression_times.clear()
        self.compression_depths.clear()
        self.compression_history.clear()
        self.current_rate = 0
        self.average_depth = 0
        self.positioning_accuracy = 0
        print("All counters reset")
    
    def calibrate_current_mode(self):
        """Calibrate based on current mode"""
        if self.current_angle == CameraAngle.SIDE_VIEW:
            self.baseline_chest_y = None
            print("Compression baseline reset - position for new baseline")
        else:
            print("Overhead mode auto-calibrates using pose detection")
    
    def cleanup(self):
        """Clean up resources"""
        self.cap.release()
        cv2.destroyAllWindows()
        pygame.mixer.quit()
        print("CPR Assistant shutdown complete")

if __name__ == "__main__":
    # Installation check
    try:
        import cv2
        import mediapipe as mp
        import pygame
        import numpy as np
    except ImportError as e:
        print("Missing required packages. Please install:")
        print("pip install opencv-python mediapipe pygame numpy")
        exit(1)
    
    print("🫀 Advanced CPR Assistant Starting...")
    print("Multi-angle CPR training system")
    print("Supports both overhead positioning and side-view compression monitoring")
    
    try:
        assistant = AdvancedCPRAssistant()
        assistant.run()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure webcam is connected and properly configured")