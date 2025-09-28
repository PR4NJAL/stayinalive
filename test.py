import cv2
import mediapipe as mp
import time
import math
from collections import deque
import pygame
# import threading

class CPRAssistant:
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # CPR parameters
        self.target_compression_rate = 110  # compressions per minute
        self.target_depth = 5.0  # cm (estimated)
        self.chest_center = None
        self.calibrated = False
        
        # Tracking variables
        self.hand_positions = deque(maxlen=10)
        self.compression_times = deque(maxlen=20)
        self.compression_count = 0
        self.last_compression_time = 0
        self.current_rate = 0
        self.position_accuracy = 0
        self.is_compressing = False
        self.last_hand_y = 0
        
        # Initialize pygame for audio feedback
        pygame.mixer.init()
        
        # Colors (BGR format for OpenCV)
        self.colors = {
            'green': (0, 255, 0),
            'red': (0, 0, 255),
            'blue': (255, 0, 0),
            'yellow': (0, 255, 255),
            'orange': (0, 165, 255),
            'white': (255, 255, 255),
            'black': (0, 0, 0)
        }
        
        print("CPR Assistant initialized. Press 'c' to calibrate, 'q' to quit, 's' to start/stop guidance")
        
    def calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def calibrate_chest_position(self, frame):
        """Calibrate the chest center position"""
        height, width = frame.shape[:2]
        # Default chest position (center of frame, slightly above middle)
        self.chest_center = (width // 2, height // 2 - 50)
        self.calibrated = True
        print(f"Chest position calibrated at: {self.chest_center}")
        
    def analyze_hand_placement(self, hand_landmarks, frame_shape):
        """Analyze hand placement for CPR positioning"""
        if not self.calibrated:
            return "Please calibrate chest position first (press 'c')"
        
        height, width = frame_shape[:2]
        
        # Get hand center position
        hand_center = self.get_hand_center(hand_landmarks, width, height)
        
        # Calculate distance from chest center
        distance_from_chest = self.calculate_distance(hand_center, self.chest_center)
        
        # Calculate accuracy (closer = better, with tolerance zone)
        tolerance_radius = 80  # pixels
        if distance_from_chest <= tolerance_radius:
            accuracy = max(0, (tolerance_radius - distance_from_chest) / tolerance_radius * 100)
        else:
            accuracy = 0
            
        return accuracy, hand_center, distance_from_chest
    
    def get_hand_center(self, landmarks, width, height):
        """Get center point of hand landmarks"""
        x_coords = [lm.x * width for lm in landmarks.landmark]
        y_coords = [lm.y * height for lm in landmarks.landmark]
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)
        return (int(center_x), int(center_y))
    
    def detect_compression(self, hand_center):
        """Detect compression movement based on hand vertical movement"""
        current_time = time.time()
        
        if len(self.hand_positions) > 0:
            prev_y = self.hand_positions[-1][1]
            current_y = hand_center[1]
            
            # Detect downward movement (compression)
            if current_y > prev_y + 15 and not self.is_compressing:
                self.is_compressing = True
                self.compression_count += 1
                self.compression_times.append(current_time)
                
                # Calculate compression rate
                if len(self.compression_times) >= 2:
                    time_window = self.compression_times[-1] - self.compression_times[0]
                    if time_window > 0:
                        self.current_rate = (len(self.compression_times) - 1) / time_window * 60
                        
            # Reset compression state when hand moves up
            elif current_y < prev_y - 10:
                self.is_compressing = False
        
        self.hand_positions.append(hand_center)
    
    def draw_guidance_overlay(self, frame):
        """Draw CPR guidance overlay on frame"""
        height, width = frame.shape[:2]
        
        # Draw chest target area
        if self.calibrated and self.chest_center:
            # Main target circle
            cv2.circle(frame, self.chest_center, 80, self.colors['yellow'], 3)
            cv2.circle(frame, self.chest_center, 40, self.colors['green'], 2)
            cv2.circle(frame, self.chest_center, 5, self.colors['red'], -1)
            
            # Labels
            cv2.putText(frame, "CHEST CENTER", 
                       (self.chest_center[0] - 60, self.chest_center[1] - 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.colors['white'], 2)
            cv2.putText(frame, "TARGET ZONE", 
                       (self.chest_center[0] - 50, self.chest_center[1] + 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.colors['yellow'], 2)
        
        # Draw compression rate indicator
        rate_color = self.colors['green'] if 100 <= self.current_rate <= 120 else self.colors['red']
        cv2.putText(frame, f"Rate: {self.current_rate:.0f}/min", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, rate_color, 2)
        
        # Draw compression count
        cv2.putText(frame, f"Compressions: {self.compression_count}", 
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.colors['white'], 2)
        
        # Draw accuracy if available
        if hasattr(self, 'last_accuracy'):
            acc_color = self.colors['green'] if self.last_accuracy > 70 else self.colors['red']
            cv2.putText(frame, f"Accuracy: {self.last_accuracy:.0f}%", 
                       (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, acc_color, 2)
    
    def provide_feedback(self, frame, accuracy=0, distance=0):
        """Provide visual and text feedback"""
        height, width = frame.shape[:2]
        feedback_y = height - 100
        
        if not self.calibrated:
            feedback = "Press 'c' to calibrate chest position"
            color = self.colors['yellow']
        elif accuracy > 80:
            feedback = "EXCELLENT hand placement! Continue compressions"
            color = self.colors['green']
        elif accuracy > 50:
            feedback = "Good placement - adjust slightly toward center"
            color = self.colors['blue']
        elif accuracy > 20:
            feedback = "Move hands closer to chest center"
            color = self.colors['orange']
        else:
            feedback = "Position hands over chest center"
            color = self.colors['red']
            
        # Rate feedback
        if self.current_rate > 0:
            if self.current_rate < 100:
                rate_feedback = "COMPRESS FASTER!"
                rate_color = self.colors['red']
            elif self.current_rate > 120:
                rate_feedback = "COMPRESS SLOWER!"
                rate_color = self.colors['red']
            else:
                rate_feedback = "Good compression rate!"
                rate_color = self.colors['green']
        else:
            rate_feedback = "Start compressions"
            rate_color = self.colors['white']
        
        # Draw feedback background
        cv2.rectangle(frame, (0, feedback_y - 40), (width, height), (0, 0, 0), -1)
        
        # Draw feedback text
        cv2.putText(frame, feedback, (10, feedback_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, rate_feedback, (10, feedback_y + 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, rate_color, 2)
    
    def draw_hand_guidance(self, frame, hand_landmarks, hand_center, accuracy):
        """Draw hand-specific guidance"""
        height, width = frame.shape[:2]
        
        # Draw hand landmarks
        self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
        
        # Draw hand center
        color = self.colors['green'] if accuracy > 70 else self.colors['red']
        cv2.circle(frame, hand_center, 10, color, -1)
        cv2.circle(frame, hand_center, 20, color, 2)
        
        # Draw connection line to chest center if calibrated
        if self.calibrated:
            cv2.line(frame, hand_center, self.chest_center, color, 2)
    
    def emergency_call_simulation(self):
        """Simulate emergency call functionality"""
        print("\n🚨 EMERGENCY CALL INITIATED 🚨")
        print("In a real implementation, this would:")
        print("- Dial emergency services (911/999/112)")
        print("- Send GPS location")
        print("- Provide CPR status updates")
        print("- Connect to emergency dispatcher")
        
    def run(self):
        """Main application loop"""
        guidance_active = False
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process hands
            results = self.hands.process(frame_rgb)
            
            # Draw base overlay
            if guidance_active:
                self.draw_guidance_overlay(frame)
            
            # Process hand detections
            if results.multi_hand_landmarks and guidance_active:
                for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    # Analyze hand placement
                    if self.calibrated:
                        accuracy, hand_center, distance = self.analyze_hand_placement(
                            hand_landmarks, frame.shape)
                        self.last_accuracy = accuracy
                        
                        # Detect compressions
                        self.detect_compression(hand_center)
                        
                        # Draw hand guidance
                        self.draw_hand_guidance(frame, hand_landmarks, hand_center, accuracy)
                        
                        # Provide feedback
                        self.provide_feedback(frame, accuracy, distance)
                    else:
                        # Just draw landmarks if not calibrated
                        self.mp_draw.draw_landmarks(frame, hand_landmarks, 
                                                  self.mp_hands.HAND_CONNECTIONS)
            elif guidance_active:
                self.provide_feedback(frame)
            
            # Draw instructions
            if not guidance_active:
                cv2.putText(frame, "Press 's' to start CPR guidance", 
                           (frame.shape[1]//2 - 150, frame.shape[0]//2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.colors['white'], 2)
            
            # Draw controls
            controls = [
                "Controls:",
                "'c' - Calibrate chest position",
                "'s' - Start/Stop guidance", 
                "'e' - Emergency call",
                "'r' - Reset counters",
                "'q' - Quit"
            ]
            
            for i, control in enumerate(controls):
                cv2.putText(frame, control, (frame.shape[1] - 280, 30 + i*25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['white'], 1)
            
            # Show frame
            cv2.imshow('CPR Hand Placement Assistant', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                self.calibrate_chest_position(frame)
            elif key == ord('s'):
                guidance_active = not guidance_active
                status = "ACTIVE" if guidance_active else "INACTIVE"
                print(f"CPR Guidance: {status}")
            elif key == ord('e'):
                self.emergency_call_simulation()
            elif key == ord('r'):
                self.compression_count = 0
                self.compression_times.clear()
                self.current_rate = 0
                print("Counters reset")
        
        # Cleanup
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.cap.release()
        cv2.destroyAllWindows()
        print("CPR Assistant shutdown complete")

# Additional utility functions
def create_cpr_trainer():
    """Create and return a CPR training assistant"""
    return CPRAssistant()

def run_cpr_training():
    """Main function to run CPR training"""
    print("🫀 CPR Hand Placement Assistant Starting...")
    print("Make sure you have a webcam connected and adequate lighting")
    print("Position yourself so your torso is visible in the camera")
    
    try:
        assistant = create_cpr_trainer()
        assistant.run()
    except Exception as e:
        print(f"Error running CPR assistant: {e}")
        print("Make sure you have installed: pip install opencv-python mediapipe pygame numpy")

if __name__ == "__main__":
    # Installation check
    try:
        import cv2
        import mediapipe as mp
        import pygame
    except ImportError as e:
        print("Missing required packages. Please install:")
        print("pip install opencv-python mediapipe pygame numpy")
        exit(1)
    
    run_cpr_training()