import math
import cv2
from enums import CameraAngle, CPRMode
from config import TARGET_COMPRESSION_RATE, TARGET_DEPTH_CM
from detection import PoseDetector, HandDetector, HolisticDetector, CameraManager
from analysis import CPRAnalyzer
from visualization import CPRVisualizer

class AdvancedCPRAssistant:
    """Main CPR Assistant class that coordinates all components"""
    
    def __init__(self) -> None:
        # Initialize components
        self.pose_detector = PoseDetector()
        self.hand_detector = HandDetector()
        self.holistic_detector = HolisticDetector()
        self.camera_manager = CameraManager()
        self.analyzer = CPRAnalyzer()
        self.visualizer = CPRVisualizer()
        
        # Current mode and angle
        self.current_angle = CameraAngle.OVERHEAD
        self.current_mode = CPRMode.POSITIONING
        
        # CPR parameters
        self.target_compression_rate = TARGET_COMPRESSION_RATE
        self.target_depth_cm = TARGET_DEPTH_CM
        
        # Calibration
        self.calibrated = False
        self.calibration_frames = 0
        self.calibration_data = []
        
        print("Advanced CPR Assistant initialized")
        print("Current Mode: OVERHEAD POSITIONING")
        self.print_controls()
    
    def print_controls(self) -> None:
        """Print current controls based on mode"""
        print("\n=== CONTROLS ===")
        if self.current_angle == CameraAngle.OVERHEAD:
            print("OVERHEAD MODE - Hand Positioning:")
            print("'1' - Switch to SIDE VIEW mode")
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
    
    def get_hand_center(self, landmarks, width, height) -> tuple[int, int]:
        """Get center point of hand landmarks"""
        x_coords = [lm.x * width for lm in landmarks.landmark]
        y_coords = [lm.y * height for lm in landmarks.landmark]
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)
        return (int(center_x), int(center_y))
    
    def calculate_distance(self, point1, point2) -> int:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def switch_angle(self, new_angle) -> None:
        """Switch camera angle and mode"""
        if isinstance(new_angle, str):
            new_angle = CameraAngle(new_angle)
        
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
            self.analyzer.reset_baseline()
    
    def emergency_call_simulation(self) -> None:
        """Simulate emergency call"""
        print("\n🚨 EMERGENCY CALL INITIATED 🚨")
        print("Calling emergency services...")
        print(f"CPR Status: {self.analyzer.compression_count} compressions delivered")
        if self.analyzer.current_rate > 0:
            print(f"Current rate: {self.analyzer.current_rate:.0f}/min")
        print("Location: [GPS coordinates would be sent]")
    
    def reset_counters(self) -> None:
        """Reset all counters and tracking"""
        self.analyzer.reset_counters()
        print("All counters reset")
    
    def calibrate_current_mode(self) -> None:
        """Calibrate based on current mode"""
        if self.current_angle == CameraAngle.SIDE_VIEW:
            self.analyzer.reset_baseline()
            print("Compression baseline reset - position for new baseline")
    
    def run(self):
        """Main application loop"""
        _, frame = self.camera_manager.read_frame()
                        
        # Flip frame for mirror effect
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
        # Process frame based on current mode
        if self.current_angle == CameraAngle.OVERHEAD:
            # Use holistic for both pose and hands
            holistic_results = self.holistic_detector.process_frame(frame_rgb)
                    
            # Analyze positioning
            feedback = self.analyzer.analyze_hand_positioning_overhead(
                holistic_results, holistic_results, frame.shape,
                self.get_hand_center, self.calculate_distance)
                    
            # Draw overlay
            self.visualizer.draw_overhead_overlay(
                frame, holistic_results, holistic_results,
                self.analyzer.detected_chest_center, self.analyzer.chest_width,
                self.analyzer.positioning_accuracy, self.get_hand_center)
                    
        else:  # SIDE_VIEW
            # Process hands and pose separately for better performance
            hands_results = self.hand_detector.process_frame(frame_rgb)
            pose_results = self.pose_detector.process_frame(frame_rgb)
                    
            # Analyze compressions
            feedback = self.analyzer.analyze_compression_side_view(
            hands_results, pose_results, frame.shape, self.get_hand_center)
                    
            # Draw overlay
            self.visualizer.draw_side_view_overlay(
                frame, hands_results, pose_results,
                self.analyzer.baseline_chest_y, self.analyzer.current_rate,
                self.analyzer.compression_count, self.analyzer.average_depth,
                self.get_hand_center)
                
        # Draw feedback
        self.visualizer.draw_feedback(frame, feedback)
            
        # Draw mode and status indicators
        self.visualizer.draw_mode_indicator(frame, self.current_angle)

        return frame