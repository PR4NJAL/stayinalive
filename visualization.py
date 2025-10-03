import cv2
from config import COLORS

class CPRVisualizer:
    """Handles all visualization and drawing operations"""
    
    def __init__(self) -> None:
        self.colors = COLORS
    
    def draw_overhead_overlay(self, frame, holistic_results, pose_results, detected_chest_center, chest_width, positioning_accuracy, get_hand_center_func) -> None:
        """Draw overlay for overhead positioning mode"""
        if holistic_results and holistic_results.pose_landmarks:
            # Draw pose landmarks (torso area)
            self._draw_pose_landmarks(frame, holistic_results.pose_landmarks)
            
            # Draw chest center and target zone
            if detected_chest_center and chest_width:
                self._draw_chest_target_zone(frame, detected_chest_center, chest_width)
        
        # Draw hand landmarks and positioning
        if holistic_results:
            self._draw_hand_positioning(frame, holistic_results, detected_chest_center, positioning_accuracy, get_hand_center_func)
    
    def draw_side_view_overlay(self, frame, hands_results, pose_results, baseline_chest_y, current_rate, compression_count, average_depth, get_hand_center_func) -> None:
        """Draw overlay for side view compression mode"""
        # Draw pose landmarks
        if pose_results and pose_results.pose_landmarks:
            self._draw_pose_landmarks(frame, pose_results.pose_landmarks)
        
        # Draw compression visualization
        if hands_results and hands_results.multi_hand_landmarks:
            self._draw_compression_visualization(frame, hands_results, baseline_chest_y, get_hand_center_func)
        
        # Draw compression metrics
        self._draw_compression_metrics(frame, current_rate, compression_count, average_depth)
    
    def draw_feedback(self, frame, feedback_text) -> None:
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
    
    def draw_mode_indicator(self, frame, current_angle) -> None:
        """Draw mode and status indicators"""
        # Draw mode indicator
        mode_text = f"Mode: {current_angle.value.upper()}"
        cv2.putText(frame, mode_text, (frame.shape[1] - 250, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.colors['yellow'], 2)
        
        # Draw status
        status = "ACTIVE"
        status_color = self.colors['green']
        cv2.putText(frame, f"Status: {status}", (frame.shape[1] - 200, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
    
    def _draw_pose_landmarks(self, frame, pose_landmarks) -> None:
        """Draw pose landmarks on frame"""
        import mediapipe as mp
        mp_draw = mp.solutions.drawing_utils
        mp_pose = mp.solutions.pose
        
        mp_draw.draw_landmarks(
            frame, pose_landmarks, 
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2),
            connection_drawing_spec=mp_draw.DrawingSpec(color=(0, 255, 255), thickness=1)
        )
    
    def _draw_chest_target_zone(self, frame, detected_chest_center, chest_width) -> None:
        """Draw chest target zone"""
        chest_x, chest_y = detected_chest_center
        
        # Main target zone (adaptive to chest size)
        target_radius = int(chest_width * 0.3)
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
    
    def _draw_hand_positioning(self, frame, holistic_results, detected_chest_center, positioning_accuracy, get_hand_center_func) -> None:
        """Draw hand positioning visualization"""
        import mediapipe as mp
        mp_draw = mp.solutions.drawing_utils
        mp_hands = mp.solutions.hands
        
        # Draw left hand
        if holistic_results.left_hand_landmarks:
            mp_draw.draw_landmarks(
                frame, holistic_results.left_hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            hand_center = get_hand_center_func(holistic_results.left_hand_landmarks, 
                                             frame.shape[1], frame.shape[0])
            color = self.colors['green'] if positioning_accuracy > 70 else self.colors['red']
            cv2.circle(frame, hand_center, 8, color, -1)
            cv2.circle(frame, hand_center, 15, color, 2)
            
            # Draw connection to chest if detected
            if detected_chest_center:
                cv2.line(frame, hand_center, detected_chest_center, color, 2)
        
        # Draw right hand
        if holistic_results.right_hand_landmarks:
            mp_draw.draw_landmarks(
                frame, holistic_results.right_hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            hand_center = get_hand_center_func(holistic_results.right_hand_landmarks, 
                                             frame.shape[1], frame.shape[0])
            color = self.colors['green'] if positioning_accuracy > 70 else self.colors['red']
            cv2.circle(frame, hand_center, 8, color, -1)
            cv2.circle(frame, hand_center, 15, color, 2)
            
            # Draw connection to chest if detected
            if detected_chest_center:
                cv2.line(frame, hand_center, detected_chest_center, color, 2)
    
    def _draw_compression_visualization(self, frame, hands_results, baseline_chest_y, get_hand_center_func) -> None:
        """Draw compression visualization for side view"""
        import mediapipe as mp
        mp_draw = mp.solutions.drawing_utils
        mp_hands = mp.solutions.hands
        
        height, width = frame.shape[:2]
        
        for hand_landmarks in hands_results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            hand_center = get_hand_center_func(hand_landmarks, width, height)
            
            # Draw compression depth indicator
            if baseline_chest_y:
                compression_depth = abs(hand_center[1] - baseline_chest_y)
                
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
                cv2.line(frame, (0, baseline_chest_y), 
                        (width, baseline_chest_y), self.colors['blue'], 2)
                cv2.putText(frame, "BASELINE", (10, baseline_chest_y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['blue'], 1)
    
    def _draw_compression_metrics(self, frame, current_rate, compression_count, average_depth) -> None:
        """Draw compression metrics on frame"""
        cv2.putText(frame, f"Rate: {current_rate:.0f}/min", 
                   (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.colors['white'], 2)
        cv2.putText(frame, f"Compressions: {compression_count}", 
                   (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.colors['white'], 2)
        cv2.putText(frame, f"Avg Depth: {average_depth:.0f}px", 
                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.colors['white'], 2)
