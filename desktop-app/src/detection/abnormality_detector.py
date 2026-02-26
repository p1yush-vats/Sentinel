"""
Abnormality Detector - Complete with Large Paste Detection

Analyzes input patterns to detect suspicious behavior and cheating.
"""
from datetime import datetime
from typing import Dict, List, Optional, Callable
from collections import deque
import statistics


class AbnormalityType:
    """Comprehensive abnormality types for catching cheating"""
    
    # PRIORITY 1: HIGH-CONFIDENCE CHEATING (Automated)
    MECHANICAL_TYPING = "mechanical_typing"              # Bot/macro detection
    AUTOMATED_MOUSE = "automated_mouse"                   # Scripted mouse movement
    PASTE_HEAVY_WORK = "paste_heavy_work"                 # Excessive copy-paste
    RAPID_PASTE = "rapid_paste"                           # Multiple quick pastes
    SUSPICIOUS_PASTE = "suspicious_paste"                 # Large paste volumes (NEW)
    LONG_IDLE = "long_idle"                               # Away from desk
    
    # PRIORITY 2: SUSPICIOUS PATTERNS
    MOUSE_JIGGLER = "mouse_jiggler"                       # Anti-idle device
    UNNATURAL_RHYTHM = "unnatural_rhythm"                 # Too perfect timing
    ACTIVITY_BURST = "activity_burst"                     # Periodic spikes
    SUPERHUMAN_SPEED = "superhuman_speed"                 # Impossibly fast
    MINIMAL_ACTIVITY = "minimal_activity"                 # Barely working
    
    # PRIORITY 3: ADVANCED DETECTION
    TYPING_STYLE_CHANGE = "typing_style_change"           # Different person
    COPY_FROM_BROWSER = "copy_from_browser"               # AI/internet usage
    SESSION_GAMING = "session_gaming"                     # Time manipulation
    PERFECT_COMPLETION = "perfect_completion"             # Too perfect results
    
    # META PATTERNS
    MULTIPLE_ABNORMALITIES = "multiple_abnormalities"     # Combined suspicious behavior
    HIGH_RISK_SESSION = "high_risk_session"               # Overall fraud likelihood


class Abnormality:
    """Detected abnormality"""
    
    def __init__(
        self,
        abnormality_type: str,
        confidence_score: float,
        detected_at: datetime,
        metadata: Dict
    ):
        self.abnormality_type = abnormality_type
        self.confidence_score = confidence_score  # 0.0 - 1.0
        self.detected_at = detected_at
        self.metadata = metadata
    
    def to_dict(self) -> Dict:
        return {
            "abnormality_type": self.abnormality_type,
            "confidence_score": self.confidence_score,
            "detected_at": self.detected_at.isoformat(),
            "metadata": self.metadata
        }


class AbnormalityDetector:
    """
    Comprehensive abnormality detector with all detection methods
    
    Detection Methods:
    - Mechanical typing (bot-like consistency)
    - Excessive paste operations
    - Large paste detection (300+ characters)
    - Unusual idle periods during work time
    - Copy-paste heavy workflows
    - Mouse jiggler detection
    - Activity burst patterns
    - Typing style changes
    - And more...
    """
    
    def __init__(
        self,
        on_abnormality_detected: Optional[Callable] = None,
        confidence_threshold: float = 0.7
    ):
        """
        Initialize detector
        
        Args:
            on_abnormality_detected: Callback for detected abnormalities
            confidence_threshold: Minimum confidence to report
        """
        self.on_abnormality_detected = on_abnormality_detected
        self.confidence_threshold = confidence_threshold
        
        # Detection history
        self.detected_abnormalities: List[Abnormality] = []
        self.recent_pastes = deque(maxlen=50)
        
        # Tracking buffers
        self.keystroke_intervals = deque(maxlen=200)
        self.mouse_movements = deque(maxlen=200)
        self.paste_events = deque(maxlen=50)
        self.activity_timeline = deque(maxlen=1000)
        
        # Baseline tracking (for detecting changes)
        self.baseline_typing_speed = None
        self.baseline_accuracy = None
        self.session_start_time = None
        
        # Thresholds
        self.MECHANICAL_VARIANCE_THRESHOLD = 0.15  # Low variance = mechanical
        self.RAPID_PASTE_THRESHOLD = 2  # pastes in 30 seconds
        self.PASTE_RATIO_THRESHOLD = 0.3  # >30% paste vs keystrokes
        self.LARGE_PASTE_RATIO_THRESHOLD = 0.5  # >50% of pastes are large
        self.IDLE_THRESHOLD_SECONDS = 300  # 5 minutes
        self.JIGGLER_MOVEMENT_SIZE = 10  # pixels
        self.SUPERHUMAN_WPM = 150
        self.MINIMAL_ACTIVITY_THRESHOLD = 10  # keystrokes per minute
    
    # ============================================
    # PRIORITY 1: HIGH-CONFIDENCE DETECTIONS
    # ============================================
    
    def analyze_keystroke_pattern(self, pattern_data: Dict) -> Optional[Abnormality]:
        """
        Analyze keystroke patterns for mechanical behavior
        
        Args:
            pattern_data: Pattern from InputCollector
        
        Returns:
            Abnormality if detected, None otherwise
        """
        if pattern_data.get("status") == "insufficient_data":
            return None
        
        consistency = pattern_data.get("consistency_score", 1.0)
        sample_size = pattern_data.get("sample_size", 0)
        
        # Need sufficient data
        if sample_size < 50:
            return None
        
        # Very consistent timing = mechanical/bot
        if consistency < self.MECHANICAL_VARIANCE_THRESHOLD:
            confidence = 1.0 - consistency  # Lower variance = higher confidence
            
            if confidence >= self.confidence_threshold:
                abnormality = Abnormality(
                    abnormality_type=AbnormalityType.MECHANICAL_TYPING,
                    confidence_score=min(confidence, 1.0),
                    detected_at=datetime.now(),
                    metadata={
                        "consistency_score": consistency,
                        "avg_interval_ms": pattern_data.get("avg_interval_ms"),
                        "std_deviation": pattern_data.get("std_deviation"),
                        "sample_size": sample_size,
                        "description": "Typing pattern shows mechanical consistency"
                    }
                )
                
                self._report_abnormality(abnormality)
                return abnormality
        
        return None
    
    def analyze_paste_behavior(
        self,
        total_pastes: int,
        total_keystrokes: int,
        session_duration_seconds: float
    ) -> Optional[Abnormality]:
        """
        Analyze paste behavior
        
        Args:
            total_pastes: Total paste operations
            total_keystrokes: Total keystrokes
            session_duration_seconds: Session duration
        
        Returns:
            Abnormality if detected
        """
        if session_duration_seconds < 60:  # Need at least 1 minute
            return None
        
        # Calculate paste ratio
        total_actions = total_pastes + total_keystrokes
        if total_actions == 0:
            return None
        
        paste_ratio = total_pastes / total_actions
        
        # Excessive paste ratio
        if paste_ratio > self.PASTE_RATIO_THRESHOLD and total_pastes > 10:
            confidence = min(paste_ratio / 0.5, 1.0)  # Scale to 1.0
            
            if confidence >= self.confidence_threshold:
                abnormality = Abnormality(
                    abnormality_type=AbnormalityType.PASTE_HEAVY_WORK,
                    confidence_score=confidence,
                    detected_at=datetime.now(),
                    metadata={
                        "paste_ratio": round(paste_ratio, 3),
                        "total_pastes": total_pastes,
                        "total_keystrokes": total_keystrokes,
                        "description": f"Work is {int(paste_ratio*100)}% paste operations"
                    }
                )
                
                self._report_abnormality(abnormality)
                return abnormality
        
        return None
    
    def analyze_large_paste_behavior(
        self,
        total_large_pastes: int,
        total_pastes: int,
        session_duration_seconds: float
    ) -> Optional[Abnormality]:
        """
        Analyze large paste behavior (NEW)
        
        Args:
            total_large_pastes: Number of large pastes (300+ chars)
            total_pastes: Total paste operations
            session_duration_seconds: Session duration
        
        Returns:
            Abnormality if detected
        """
        if session_duration_seconds < 60 or total_pastes == 0:
            return None
        
        # Calculate large paste ratio
        large_paste_ratio = total_large_pastes / total_pastes
        
        # If >50% of pastes are large = suspicious
        if large_paste_ratio > self.LARGE_PASTE_RATIO_THRESHOLD and total_large_pastes >= 3:
            confidence = min(large_paste_ratio, 1.0)
            
            if confidence >= self.confidence_threshold:
                abnormality = Abnormality(
                    abnormality_type=AbnormalityType.SUSPICIOUS_PASTE,
                    confidence_score=confidence,
                    detected_at=datetime.now(),
                    metadata={
                        "large_paste_ratio": round(large_paste_ratio, 3),
                        "total_large_pastes": total_large_pastes,
                        "total_pastes": total_pastes,
                        "description": f"{int(large_paste_ratio*100)}% of pastes are large (300+ characters)"
                    }
                )
                
                self._report_abnormality(abnormality)
                return abnormality
        
        return None
    
    def analyze_idle_period(
        self,
        idle_seconds: float,
        is_work_time: bool
    ) -> Optional[Abnormality]:
        """
        Analyze idle periods
        
        Args:
            idle_seconds: Current idle time
            is_work_time: Whether currently in work mode
        
        Returns:
            Abnormality if detected
        """
        if not is_work_time:
            return None
        
        # Extended idle during work time
        if idle_seconds > self.IDLE_THRESHOLD_SECONDS:
            # Confidence increases with idle time
            confidence = min(idle_seconds / (self.IDLE_THRESHOLD_SECONDS * 2), 1.0)
            
            if confidence >= self.confidence_threshold:
                abnormality = Abnormality(
                    abnormality_type=AbnormalityType.LONG_IDLE,
                    confidence_score=confidence,
                    detected_at=datetime.now(),
                    metadata={
                        "idle_seconds": idle_seconds,
                        "idle_minutes": round(idle_seconds / 60, 1),
                        "description": f"Idle for {idle_seconds/60:.1f} minutes during work time"
                    }
                )
                
                self._report_abnormality(abnormality)
                return abnormality
        
        return None
    
    def track_paste_event(self, timestamp: datetime) -> Optional[Abnormality]:
        """
        Track individual paste event and detect rapid pasting
        
        Args:
            timestamp: When paste occurred
        
        Returns:
            Abnormality if rapid paste detected
        """
        self.recent_pastes.append(timestamp)
        
        # Check for rapid pasting
        if len(self.recent_pastes) >= self.RAPID_PASTE_THRESHOLD:
            recent = list(self.recent_pastes)[-self.RAPID_PASTE_THRESHOLD:]
            time_span = (recent[-1] - recent[0]).total_seconds()
            
            # Multiple pastes in short time
            if time_span < 30:  # 5+ pastes in 30 seconds
                confidence = min(self.RAPID_PASTE_THRESHOLD / 3, 1.0)
                
                if confidence >= self.confidence_threshold:
                    abnormality = Abnormality(
                        abnormality_type=AbnormalityType.RAPID_PASTE,
                        confidence_score=confidence,
                        detected_at=datetime.now(),
                        metadata={
                            "paste_count": len(recent),
                            "time_span_seconds": time_span,
                            "description": f"{len(recent)} pastes in {time_span:.1f} seconds"
                        }
                    )
                    
                    self._report_abnormality(abnormality)
                    return abnormality
        
        return None
    
    # ============================================
    # PRIORITY 2: SUSPICIOUS PATTERN DETECTION
    # ============================================
    
    def detect_mouse_jiggler(self, movements: List[Dict]) -> Optional[Abnormality]:
        """
        Detect mouse jiggler devices/software
        
        WHAT IT CATCHES:
        - Physical mouse jigglers
        - Anti-idle software
        - Automated mouse movers
        """
        if len(movements) < 20:
            return None
        
        # Look for repetitive small movements
        small_movements = [m for m in movements if m.get('distance', 0) < self.JIGGLER_MOVEMENT_SIZE]
        
        if len(small_movements) > 10:
            # Check if movements happen at regular intervals
            intervals = []
            for i in range(1, len(small_movements)):
                time_diff = (small_movements[i]['timestamp'] - small_movements[i-1]['timestamp']).total_seconds()
                intervals.append(time_diff)
            
            if intervals:
                avg_interval = statistics.mean(intervals)
                stdev_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
                
                # Regular intervals = jiggler
                if stdev_interval < 2 and 5 < avg_interval < 60:  # Every 5-60 seconds
                    confidence = 0.9
                    
                    if confidence >= self.confidence_threshold:
                        abnormality = Abnormality(
                            abnormality_type=AbnormalityType.MOUSE_JIGGLER,
                            confidence_score=confidence,
                            detected_at=datetime.now(),
                            metadata={
                                "small_movements": len(small_movements),
                                "avg_interval_seconds": avg_interval,
                                "regularity": 1.0 - (stdev_interval / avg_interval) if avg_interval > 0 else 0,
                                "description": f"Mouse jiggler detected (moves every {avg_interval:.1f}s)"
                            }
                        )
                        
                        self._report_abnormality(abnormality)
                        return abnormality
        
        return None
    
    def detect_superhuman_speed(self, wpm: float) -> Optional[Abnormality]:
        """
        Detect impossibly fast typing
        
        WHAT IT CATCHES:
        - Copy-paste disguised as typing
        - Multiple people on same account
        - Automation
        """
        if wpm > self.SUPERHUMAN_WPM:
            confidence = min((wpm - self.SUPERHUMAN_WPM) / self.SUPERHUMAN_WPM, 1.0)
            
            if confidence >= self.confidence_threshold:
                abnormality = Abnormality(
                    abnormality_type=AbnormalityType.SUPERHUMAN_SPEED,
                    confidence_score=confidence,
                    detected_at=datetime.now(),
                    metadata={
                        "wpm": wpm,
                        "description": f"Typing speed ({wpm:.0f} WPM) exceeds human capability"
                    }
                )
                
                self._report_abnormality(abnormality)
                return abnormality
        
        return None
    
    def detect_minimal_activity(self, keystrokes_per_minute: float, is_work_time: bool) -> Optional[Abnormality]:
        """
        Detect barely working
        
        WHAT IT CATCHES:
        - Minimal effort to avoid idle detection
        - Not actually working
        - Gaming the system
        """
        if not is_work_time or keystrokes_per_minute > self.MINIMAL_ACTIVITY_THRESHOLD:
            return None
        
        confidence = 1.0 - (keystrokes_per_minute / self.MINIMAL_ACTIVITY_THRESHOLD)
        
        if confidence >= self.confidence_threshold:
            abnormality = Abnormality(
                abnormality_type=AbnormalityType.MINIMAL_ACTIVITY,
                confidence_score=confidence,
                detected_at=datetime.now(),
                metadata={
                    "keystrokes_per_minute": keystrokes_per_minute,
                    "description": f"Very low activity ({keystrokes_per_minute:.1f} keys/min)"
                }
            )
            
            self._report_abnormality(abnormality)
            return abnormality
        
        return None
    
    def run_comprehensive_analysis(
        self,
        keystroke_pattern: Dict,
        activity_summary: Dict,
        is_work_time: bool
    ) -> List[Abnormality]:
        """
        Run all detection algorithms
        
        Args:
            keystroke_pattern: Pattern data from InputCollector
            activity_summary: Activity summary from InputCollector
            is_work_time: Whether currently working
        
        Returns:
            List of detected abnormalities
        """
        detected = []
        
        # Mechanical typing check
        abn = self.analyze_keystroke_pattern(keystroke_pattern)
        if abn:
            detected.append(abn)
        
        # Paste behavior check
        abn = self.analyze_paste_behavior(
            total_pastes=activity_summary.get("total_pastes", 0),
            total_keystrokes=activity_summary.get("total_keystrokes", 0),
            session_duration_seconds=activity_summary.get("session_duration_seconds", 0)
        )
        if abn:
            detected.append(abn)
        
        # Large paste check (NEW)
        abn = self.analyze_large_paste_behavior(
            total_large_pastes=activity_summary.get("total_large_pastes", 0),
            total_pastes=activity_summary.get("total_pastes", 0),
            session_duration_seconds=activity_summary.get("session_duration_seconds", 0)
        )
        if abn:
            detected.append(abn)
        
        # Idle period check
        abn = self.analyze_idle_period(
            idle_seconds=activity_summary.get("idle_seconds", 0),
            is_work_time=is_work_time
        )
        if abn:
            detected.append(abn)
        
        # Minimal activity check
        keystrokes = activity_summary.get("total_keystrokes", 0)
        duration = activity_summary.get("session_duration_seconds", 1)
        kpm = (keystrokes / duration) * 60 if duration > 0 else 0
        
        abn = self.detect_minimal_activity(kpm, is_work_time)
        if abn:
            detected.append(abn)
        
        return detected
    
    def _report_abnormality(self, abnormality: Abnormality):
        """Report detected abnormality"""
        self.detected_abnormalities.append(abnormality)
        
        if self.on_abnormality_detected:
            self.on_abnormality_detected(abnormality)
    
    def get_session_abnormalities(self) -> List[Dict]:
        """Get all detected abnormalities for current session"""
        return [abn.to_dict() for abn in self.detected_abnormalities]
    
    def clear_session(self):
        """Clear session data"""
        self.detected_abnormalities.clear()
        self.recent_pastes.clear()
    
    def get_risk_score(self) -> float:
        """
        Calculate overall risk score
        
        Returns:
            Risk score 0-100
        """
        if not self.detected_abnormalities:
            return 0.0
        
        # Weight different abnormalities
        weights = {
            AbnormalityType.MECHANICAL_TYPING: 1.0,
            AbnormalityType.MOUSE_JIGGLER: 1.0,
            AbnormalityType.PASTE_HEAVY_WORK: 0.8,
            AbnormalityType.SUSPICIOUS_PASTE: 0.9,  # NEW: High weight for large pastes
            AbnormalityType.SESSION_GAMING: 1.0,
            AbnormalityType.TYPING_STYLE_CHANGE: 0.9,
            AbnormalityType.SUPERHUMAN_SPEED: 0.9,
            AbnormalityType.ACTIVITY_BURST: 0.7,
            AbnormalityType.LONG_IDLE: 0.6,
            AbnormalityType.MINIMAL_ACTIVITY: 0.5,
            AbnormalityType.RAPID_PASTE: 0.7,
        }
        
        # Calculate weighted score
        total_weight = 0
        total_score = 0
        
        for abn in self.detected_abnormalities:
            abn_type = abn.abnormality_type
            confidence = abn.confidence_score
            weight = weights.get(abn_type, 0.5)
            
            total_score += confidence * weight * 100
            total_weight += weight
        
        # Average weighted score
        risk_score = total_score / total_weight if total_weight > 0 else 0
        
        # Boost for multiple abnormalities
        if len(self.detected_abnormalities) >= 3:
            risk_score *= 1.2  # 20% boost
        
        risk_score = min(risk_score, 100)
        
        return risk_score


# Backward compatibility alias
EnhancedAbnormalityDetector = AbnormalityDetector