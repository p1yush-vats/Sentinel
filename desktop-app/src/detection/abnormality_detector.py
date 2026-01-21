"""
Abnormality Detector

Analyzes input patterns to detect suspicious behavior.
"""
from datetime import datetime
from typing import Dict, List, Optional, Callable
from collections import deque
import statistics


class AbnormalityType:
    """Abnormality types"""
    MECHANICAL_TYPING = "mechanical_typing"
    RAPID_PASTE = "rapid_paste"
    EXCESSIVE_PASTE = "excessive_paste"
    IDLE_PERIOD = "idle_period"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    PASTE_HEAVY_WORK = "paste_heavy_work"


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
    Detects abnormal patterns in user input
    
    Detection Methods:
    - Mechanical typing (bot-like consistency)
    - Excessive paste operations
    - Unusual idle periods during work time
    - Copy-paste heavy workflows
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
        
        # Thresholds
        self.MECHANICAL_VARIANCE_THRESHOLD = 0.15  # Low variance = mechanical
        self.RAPID_PASTE_THRESHOLD = 5  # pastes in 30 seconds
        self.PASTE_RATIO_THRESHOLD = 0.3  # >30% paste vs keystrokes
        self.IDLE_THRESHOLD_SECONDS = 300  # 5 minutes
    
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
                    abnormality_type=AbnormalityType.IDLE_PERIOD,
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
        
        # Idle period check
        abn = self.analyze_idle_period(
            idle_seconds=activity_summary.get("idle_seconds", 0),
            is_work_time=is_work_time
        )
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
        
        # Average confidence of all abnormalities
        avg_confidence = sum(
            abn.confidence_score for abn in self.detected_abnormalities
        ) / len(self.detected_abnormalities)
        
        # Weight by number of abnormalities
        abnormality_factor = min(len(self.detected_abnormalities) / 10, 1.0)
        
        risk = (avg_confidence * 0.7 + abnormality_factor * 0.3) * 100
        
        return min(risk, 100.0)


# Example usage
if __name__ == "__main__":
    def on_detected(abnormality: Abnormality):
        print(f"\n🚨 ABNORMALITY DETECTED!")
        print(f"   Type: {abnormality.abnormality_type}")
        print(f"   Confidence: {abnormality.confidence_score:.2%}")
        print(f"   Details: {abnormality.metadata.get('description')}")
    
    detector = AbnormalityDetector(
        on_abnormality_detected=on_detected,
        confidence_threshold=0.7
    )
    
    # Test mechanical typing
    print("Testing mechanical typing pattern...")
    pattern = {
        "avg_interval_ms": 100,
        "consistency_score": 0.1,  # Very consistent = mechanical
        "std_deviation": 10,
        "sample_size": 100
    }
    detector.analyze_keystroke_pattern(pattern)
    
    # Test paste heavy work
    print("\nTesting paste-heavy work...")
    detector.analyze_paste_behavior(
        total_pastes=50,
        total_keystrokes=50,
        session_duration_seconds=300
    )
    
    # Get risk score
    print(f"\n📊 Overall Risk Score: {detector.get_risk_score():.1f}/100")