"""
Abnormality Detector

Analyzes input patterns to detect suspicious behavior.

FIXES IN THIS VERSION:
  1. detect_minimal_activity() — 5-minute grace period at session start
  2. detect_mouse_jiggler()    — now called from run_comprehensive_analysis()
  3. _report_abnormality()     — callback is UI-only; aggregator writes happen
                                 in main.py._save_abnormality_to_aggregator()
                                 to prevent double-counting
"""
from datetime import datetime
from typing import Dict, List, Optional, Callable
from collections import deque
import statistics


class AbnormalityType:
    """Comprehensive abnormality types"""

    # PRIORITY 1: HIGH-CONFIDENCE CHEATING
    MECHANICAL_TYPING  = "mechanical_typing"
    AUTOMATED_MOUSE    = "automated_mouse"
    PASTE_HEAVY_WORK   = "paste_heavy_work"
    RAPID_PASTE        = "rapid_paste"
    SUSPICIOUS_PASTE   = "suspicious_paste"
    LONG_IDLE          = "long_idle"

    # PRIORITY 2: SUSPICIOUS PATTERNS
    MOUSE_JIGGLER      = "mouse_jiggler"
    UNNATURAL_RHYTHM   = "unnatural_rhythm"
    ACTIVITY_BURST     = "activity_burst"
    SUPERHUMAN_SPEED   = "superhuman_speed"
    MINIMAL_ACTIVITY   = "minimal_activity"

    # PRIORITY 3: ADVANCED DETECTION
    TYPING_STYLE_CHANGE  = "typing_style_change"
    COPY_FROM_BROWSER    = "copy_from_browser"
    SESSION_GAMING       = "session_gaming"
    PERFECT_COMPLETION   = "perfect_completion"

    # META PATTERNS
    MULTIPLE_ABNORMALITIES = "multiple_abnormalities"
    HIGH_RISK_SESSION      = "high_risk_session"


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
        self.confidence_score = confidence_score
        self.detected_at      = detected_at
        self.metadata         = metadata

    def to_dict(self) -> Dict:
        return {
            "abnormality_type": self.abnormality_type,
            "confidence_score": self.confidence_score,
            "detected_at":      self.detected_at.isoformat(),
            "metadata":         self.metadata
        }


class AbnormalityDetector:
    """
    Comprehensive abnormality detector.

    Detection Methods:
    - Mechanical typing (bot-like consistency)
    - Excessive paste operations
    - Large paste detection (300+ characters)
    - Unusual idle periods during work time
    - Copy-paste heavy workflows
    - Mouse jiggler detection
    - Superhuman typing speed
    - Minimal activity (with 5-min grace period)
    """

    def __init__(
        self,
        on_abnormality_detected: Optional[Callable] = None,
        confidence_threshold: float = 0.7
    ):
        """
        Args:
            on_abnormality_detected: Callback fired on detection — used for UI
                                     updates only. Aggregator writes happen in
                                     main.py._save_abnormality_to_aggregator().
            confidence_threshold: Minimum confidence to report (default 0.7)
        """
        self.on_abnormality_detected = on_abnormality_detected
        self.confidence_threshold    = confidence_threshold

        # Detection history
        self.detected_abnormalities: List[Abnormality] = []
        self.recent_pastes = deque(maxlen=50)

        # Tracking buffers
        self.keystroke_intervals = deque(maxlen=200)
        self.mouse_movements     = deque(maxlen=200)
        self.paste_events        = deque(maxlen=50)
        self.activity_timeline   = deque(maxlen=1000)

        # Baseline tracking
        self.baseline_typing_speed = None
        self.baseline_accuracy     = None
        self.session_start_time    = None

        # Thresholds
        self.MECHANICAL_VARIANCE_THRESHOLD  = 0.15   # Low variance = mechanical
        self.RAPID_PASTE_THRESHOLD          = 2      # pastes in 30 seconds
        self.PASTE_RATIO_THRESHOLD          = 0.3    # >30% paste vs keystrokes
        self.LARGE_PASTE_RATIO_THRESHOLD    = 0.5    # >50% of pastes are large
        self.IDLE_THRESHOLD_SECONDS         = 300    # 5 minutes
        self.JIGGLER_MOVEMENT_SIZE          = 10     # pixels
        self.SUPERHUMAN_WPM                 = 150
        self.MINIMAL_ACTIVITY_THRESHOLD     = 10     # keystrokes per minute
        self.MINIMAL_ACTIVITY_GRACE_SECONDS = 300    # 5-min grace period on start

    # ============================================
    # PRIORITY 1: HIGH-CONFIDENCE DETECTIONS
    # ============================================

    def analyze_keystroke_pattern(self, pattern_data: Dict) -> Optional[Abnormality]:
        """Analyze keystroke patterns for mechanical/bot behavior"""
        if not pattern_data or pattern_data.get("status") != "ok":
            return None

        consistency = pattern_data.get("consistency_score", 1.0)

        if consistency < self.MECHANICAL_VARIANCE_THRESHOLD:
            confidence = 1.0 - (consistency / self.MECHANICAL_VARIANCE_THRESHOLD)

            if confidence >= self.confidence_threshold:
                abnormality = Abnormality(
                    abnormality_type=AbnormalityType.MECHANICAL_TYPING,
                    confidence_score=confidence,
                    detected_at=datetime.now(),
                    metadata={
                        "consistency_score": consistency,
                        "description": f"Mechanical typing pattern detected (consistency: {consistency:.3f})"
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
        """Detect copy-paste heavy work"""
        if session_duration_seconds < 60 or total_keystrokes < 10:
            return None

        paste_ratio = total_pastes / total_keystrokes if total_keystrokes > 0 else 0

        if paste_ratio > self.PASTE_RATIO_THRESHOLD and total_pastes >= 5:
            confidence = min(paste_ratio / 0.5, 1.0)

            if confidence >= self.confidence_threshold:
                abnormality = Abnormality(
                    abnormality_type=AbnormalityType.PASTE_HEAVY_WORK,
                    confidence_score=confidence,
                    detected_at=datetime.now(),
                    metadata={
                        "paste_ratio":      round(paste_ratio, 3),
                        "total_pastes":     total_pastes,
                        "total_keystrokes": total_keystrokes,
                        "description":      f"Work is {int(paste_ratio*100)}% paste operations"
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
        """Detect suspicious large-paste patterns (300+ char pastes)"""
        if session_duration_seconds < 60 or total_pastes == 0:
            return None

        large_paste_ratio = total_large_pastes / total_pastes

        if large_paste_ratio > self.LARGE_PASTE_RATIO_THRESHOLD and total_large_pastes >= 3:
            confidence = min(large_paste_ratio, 1.0)

            if confidence >= self.confidence_threshold:
                abnormality = Abnormality(
                    abnormality_type=AbnormalityType.SUSPICIOUS_PASTE,
                    confidence_score=confidence,
                    detected_at=datetime.now(),
                    metadata={
                        "large_paste_ratio":  round(large_paste_ratio, 3),
                        "total_large_pastes": total_large_pastes,
                        "total_pastes":       total_pastes,
                        "description":        f"{int(large_paste_ratio*100)}% of pastes are large (300+ chars)"
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
        """Detect extended idle periods during work time"""
        if not is_work_time:
            return None

        if idle_seconds > self.IDLE_THRESHOLD_SECONDS:
            confidence = min(idle_seconds / (self.IDLE_THRESHOLD_SECONDS * 2), 1.0)

            if confidence >= self.confidence_threshold:
                abnormality = Abnormality(
                    abnormality_type=AbnormalityType.LONG_IDLE,
                    confidence_score=confidence,
                    detected_at=datetime.now(),
                    metadata={
                        "idle_seconds": idle_seconds,
                        "idle_minutes": round(idle_seconds / 60, 1),
                        "description":  f"Idle for {idle_seconds/60:.1f} minutes during work time"
                    }
                )
                self._report_abnormality(abnormality)
                return abnormality

        return None

    def track_paste_event(self, timestamp: datetime) -> Optional[Abnormality]:
        """Track individual paste and detect rapid-paste bursts"""
        self.recent_pastes.append(timestamp)

        if len(self.recent_pastes) >= self.RAPID_PASTE_THRESHOLD:
            recent    = list(self.recent_pastes)[-self.RAPID_PASTE_THRESHOLD:]
            time_span = (recent[-1] - recent[0]).total_seconds()

            if time_span < 30:
                confidence = min(self.RAPID_PASTE_THRESHOLD / 3, 1.0)

                if confidence >= self.confidence_threshold:
                    abnormality = Abnormality(
                        abnormality_type=AbnormalityType.RAPID_PASTE,
                        confidence_score=confidence,
                        detected_at=datetime.now(),
                        metadata={
                            "paste_count":        len(recent),
                            "time_span_seconds":  time_span,
                            "description":        f"{len(recent)} pastes in {time_span:.1f} seconds"
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
        Detect mouse jiggler devices/software.

        Works with InputCollector's movement format (interval_ms field).
        Also supports distance field if present for extra precision.

        WHAT IT CATCHES:
        - Physical USB mouse jigglers
        - Anti-idle software
        - Automated mouse movers
        """
        if len(movements) < 20:
            return None

        # ── Strategy 1: distance-based (if InputCollector provides it) ──
        movements_with_distance = [m for m in movements if 'distance' in m]
        if len(movements_with_distance) >= 20:
            small_movements = [m for m in movements_with_distance
                               if m.get('distance', 0) < self.JIGGLER_MOVEMENT_SIZE]

            if len(small_movements) > 10:
                intervals = []
                for i in range(1, len(small_movements)):
                    diff = (small_movements[i]['timestamp'] -
                            small_movements[i-1]['timestamp']).total_seconds()
                    intervals.append(diff)

                if intervals:
                    avg_interval   = statistics.mean(intervals)
                    stdev_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0

                    if stdev_interval < 2 and 5 < avg_interval < 60:
                        confidence = 0.9
                        if confidence >= self.confidence_threshold:
                            abnormality = Abnormality(
                                abnormality_type=AbnormalityType.MOUSE_JIGGLER,
                                confidence_score=confidence,
                                detected_at=datetime.now(),
                                metadata={
                                    "small_movements":       len(small_movements),
                                    "avg_interval_seconds":  avg_interval,
                                    "regularity":            1.0 - (stdev_interval / avg_interval)
                                                             if avg_interval > 0 else 0,
                                    "description":           f"Mouse jiggler detected (moves every {avg_interval:.1f}s)"
                                }
                            )
                            self._report_abnormality(abnormality)
                            return abnormality

        # ── Strategy 2: interval_ms-based (InputCollector default format) ──
        recent = list(movements)[-20:]
        intervals_ms = [m['interval_ms'] for m in recent if 'interval_ms' in m]

        if len(intervals_ms) >= 10:
            avg_ms  = sum(intervals_ms) / len(intervals_ms)
            var_ms  = sum((x - avg_ms) ** 2 for x in intervals_ms) / len(intervals_ms)
            std_ms  = var_ms ** 0.5

            # Regular 1-10 second movements with low variance = jiggler
            if std_ms < 500 and 1000 < avg_ms < 10000:
                regularity = max(0.0, 1.0 - (std_ms / avg_ms)) if avg_ms > 0 else 0
                confidence = max(0.7, regularity)

                if confidence >= self.confidence_threshold:
                    abnormality = Abnormality(
                        abnormality_type=AbnormalityType.MOUSE_JIGGLER,
                        confidence_score=round(confidence, 2),
                        detected_at=datetime.now(),
                        metadata={
                            "avg_interval_ms": round(avg_ms),
                            "std_dev_ms":      round(std_ms),
                            "regularity":      round(regularity, 2),
                            "description":     f"Mouse jiggler detected (interval {avg_ms/1000:.1f}s ±{std_ms/1000:.1f}s)"
                        }
                    )
                    self._report_abnormality(abnormality)
                    return abnormality

        return None

    def detect_superhuman_speed(self, wpm: float) -> Optional[Abnormality]:
        """Detect impossibly fast typing (automation / multiple people)"""
        if wpm > self.SUPERHUMAN_WPM:
            confidence = min((wpm - self.SUPERHUMAN_WPM) / self.SUPERHUMAN_WPM, 1.0)

            if confidence >= self.confidence_threshold:
                abnormality = Abnormality(
                    abnormality_type=AbnormalityType.SUPERHUMAN_SPEED,
                    confidence_score=confidence,
                    detected_at=datetime.now(),
                    metadata={
                        "wpm":         wpm,
                        "description": f"Typing speed ({wpm:.0f} WPM) exceeds human capability"
                    }
                )
                self._report_abnormality(abnormality)
                return abnormality

        return None

    def detect_minimal_activity(
        self,
        keystrokes_per_minute: float,
        is_work_time: bool,
        session_duration_seconds: float = 0
    ) -> Optional[Abnormality]:
        """
        Detect barely-working behaviour during work time.

        WHAT IT CATCHES:
        - Minimal effort to avoid idle detection
        - Not actually working
        - Gaming the system

        Grace period: no flag for the first 5 minutes of a session.
        Employees need time to open apps and settle in before we judge them.
        """
        if not is_work_time or keystrokes_per_minute > self.MINIMAL_ACTIVITY_THRESHOLD:
            return None

        # ── 5-minute grace period ─────────────────────────────
        if session_duration_seconds < self.MINIMAL_ACTIVITY_GRACE_SECONDS:
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

    # ============================================
    # COMPREHENSIVE ANALYSIS (called every 30s)
    # ============================================

    def run_comprehensive_analysis(
        self,
        keystroke_pattern: Dict,
        activity_summary: Dict,
        is_work_time: bool
    ) -> List[Abnormality]:
        """
        Run all detection algorithms. Called by _detection_loop every 30s.

        Returns list of detected Abnormality objects. The loop in main.py
        saves each one via _save_abnormality_to_aggregator() — single write
        path, no double-counting.
        """
        detected = []

        # 1. Mechanical typing
        abn = self.analyze_keystroke_pattern(keystroke_pattern)
        if abn:
            detected.append(abn)

        # 2. Paste-heavy work
        abn = self.analyze_paste_behavior(
            total_pastes=activity_summary.get("total_pastes", 0),
            total_keystrokes=activity_summary.get("total_keystrokes", 0),
            session_duration_seconds=activity_summary.get("session_duration_seconds", 0)
        )
        if abn:
            detected.append(abn)

        # 3. Large paste
        abn = self.analyze_large_paste_behavior(
            total_large_pastes=activity_summary.get("total_large_pastes", 0),
            total_pastes=activity_summary.get("total_pastes", 0),
            session_duration_seconds=activity_summary.get("session_duration_seconds", 0)
        )
        if abn:
            detected.append(abn)

        # 4. Idle period
        abn = self.analyze_idle_period(
            idle_seconds=activity_summary.get("idle_seconds", 0),
            is_work_time=is_work_time
        )
        if abn:
            detected.append(abn)

        # 5. Minimal activity — with grace period
        keystrokes = activity_summary.get("total_keystrokes", 0)
        duration   = activity_summary.get("session_duration_seconds", 1)
        kpm        = (keystrokes / duration) * 60 if duration > 0 else 0

        abn = self.detect_minimal_activity(kpm, is_work_time, duration)
        if abn:
            detected.append(abn)

        # 6. Mouse jiggler — uses internal buffer populated by InputCollector
        movements = list(self.mouse_movements)
        abn = self.detect_mouse_jiggler(movements)
        if abn:
            detected.append(abn)

        return detected

    # ============================================
    # INTERNAL HELPERS
    # ============================================

    def _report_abnormality(self, abnormality: Abnormality):
        """
        Store detection + fire UI callback.

        NOTE: does NOT write to aggregator/SQLite — that is handled
        exclusively by main.py._save_abnormality_to_aggregator() to
        prevent double-counting.
        """
        self.detected_abnormalities.append(abnormality)

        if self.on_abnormality_detected:
            self.on_abnormality_detected(abnormality)

    def get_session_abnormalities(self) -> List[Dict]:
        """Return all detected abnormalities for current session"""
        return [abn.to_dict() for abn in self.detected_abnormalities]

    def clear_session(self):
        """Clear session data"""
        self.detected_abnormalities.clear()
        self.recent_pastes.clear()

    def get_risk_score(self) -> float:
        """Calculate overall risk score 0–100"""
        if not self.detected_abnormalities:
            return 0.0

        weights = {
            AbnormalityType.MECHANICAL_TYPING: 1.0,
            AbnormalityType.MOUSE_JIGGLER:     1.0,
            AbnormalityType.PASTE_HEAVY_WORK:  0.8,
            AbnormalityType.SUSPICIOUS_PASTE:  0.9,
            AbnormalityType.SESSION_GAMING:    1.0,
            AbnormalityType.TYPING_STYLE_CHANGE: 0.9,
            AbnormalityType.SUPERHUMAN_SPEED:  0.9,
            AbnormalityType.ACTIVITY_BURST:    0.7,
            AbnormalityType.LONG_IDLE:         0.6,
            AbnormalityType.MINIMAL_ACTIVITY:  0.5,
            AbnormalityType.RAPID_PASTE:       0.7,
        }

        total_weight = 0
        total_score  = 0

        for abn in self.detected_abnormalities:
            weight       = weights.get(abn.abnormality_type, 0.5)
            total_score += abn.confidence_score * weight * 100
            total_weight += weight

        risk_score = total_score / total_weight if total_weight > 0 else 0

        if len(self.detected_abnormalities) >= 3:
            risk_score *= 1.2  # 20% boost for multiple simultaneous flags

        return min(risk_score, 100)


# Backward-compat alias
EnhancedAbnormalityDetector = AbnormalityDetector