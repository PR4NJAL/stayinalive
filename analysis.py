import time
from collections import deque
from config import TARGET_COMPRESSION_RATE, TARGET_DEPTH_CM

class CPRAnalyzer:
    """Handles CPR analysis and feedback generation"""
    
    def __init__(self):
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
    
    def analyze_hand_positioning_overhead(self, holistic_results, pose_results, frame_shape, get_hand_center_func, calculate_distance_func):
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
            hand_center = get_hand_center_func(holistic_results.left_hand_landmarks, 
                                             frame_shape[1], frame_shape[0])
            hand_centers.append(hand_center)
        
        # Check for right hand
        if holistic_results.right_hand_landmarks:
            hand_center = get_hand_center_func(holistic_results.right_hand_landmarks, 
                                             frame_shape[1], frame_shape[0])
            hand_centers.append(hand_center)
        
        # Calculate positioning accuracy
        if len(hand_centers) >= 1:
            primary_hand = hand_centers[0]
            distance_from_chest = calculate_distance_func(primary_hand, chest_center)
            
            # Accuracy based on chest width (adaptive to person size)
            tolerance_radius = chest_width * 0.6  # 60% of chest width
            if distance_from_chest <= tolerance_radius:
                self.positioning_accuracy = max(0, 
                    (tolerance_radius - distance_from_chest) / tolerance_radius * 100)
            else:
                self.positioning_accuracy = 0
            
            # Generate feedback
            if len(hand_centers) == 2:
                hand_distance = calculate_distance_func(hand_centers[0], hand_centers[1])
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
    
    def analyze_compression_side_view(self, hands_results, pose_results, frame_shape, get_hand_center_func):
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
            hand_center = get_hand_center_func(hand_landmarks, width, height)
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
    
    def detect_chest_from_pose(self, pose_landmarks, frame_shape):
        """Detect chest center from pose landmarks"""
        if not pose_landmarks:
            return None, None
            
        height, width = frame_shape[:2]
        
        # Get shoulder landmarks
        left_shoulder = pose_landmarks.landmark[11]
        right_shoulder = pose_landmarks.landmark[12]
        
        # Calculate chest center (midpoint between shoulders, slightly below)
        chest_center_x = int((left_shoulder.x + right_shoulder.x) / 2 * width)
        chest_center_y = int((left_shoulder.y + right_shoulder.y) / 2 * height + 
                           abs(left_shoulder.y - right_shoulder.y) * height * 0.3)
        
        # Calculate chest width for scale reference
        chest_width = int(abs(left_shoulder.x - right_shoulder.x) * width)
        
        return (chest_center_x, chest_center_y), chest_width
    
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
    
    def reset_counters(self):
        """Reset all counters and tracking"""
        self.compression_count = 0
        self.compression_times.clear()
        self.compression_depths.clear()
        self.compression_history.clear()
        self.current_rate = 0
        self.average_depth = 0
        self.positioning_accuracy = 0
    
    def reset_baseline(self):
        """Reset compression baseline"""
        self.baseline_chest_y = None
        self.compression_history.clear()
