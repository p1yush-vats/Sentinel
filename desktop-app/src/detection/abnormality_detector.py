"""
Abnormality Detector — SENTINEL Desktop App

DETECTION COVERAGE:
  Priority 1 — High Confidence:
    ✅ mechanical_typing     Bot/macro-like consistent keystroke timing
    ✅ paste_heavy_work      Work is mostly copy-paste operations
    ✅ suspicious_paste      Repeated very large paste operations (1000+ chars)
    ✅ rapid_paste           Multiple pastes in quick succession
    ✅ long_idle             Extended idle during work time
    ✅ superhuman_speed      Typing speed exceeding human capability (macro replay)

  Priority 2 — Suspicious Patterns:
    ✅ mouse_jiggler         Physical jiggler device or anti-idle software
    ✅ minimal_activity      Almost no keystrokes during work time
    ✅ clock_in_clock_out    Session started and immediately gone idle
    ✅ burst_then_idle       Flurry of activity followed by long silence

  Priority 3 — Advanced:
    ✅ activity_burst        Suspiciously periodic burst/idle cycles (scripted)

ARCHITECTURE NOTES:
  - _report_abnormality() fires the UI callback ONLY. Does NOT write to DB.
  - run_comprehensive_analysis() returns a list — main.py saves each via
    _save_abnormality_to_aggregator(). Single write path, no double-counting.
  - DEMO_MODE = True collapses all time thresholds to seconds for live demos.
"""

# ╔══════════════════════════════════════════════════════════════╗
# ║                    DEMO MODE SWITCH                         ║
# ║  Set DEMO_MODE = True before your presentation.             ║
# ║  All timing thresholds drop to seconds so detections fire   ║
# ║  within the first 30s cycle instead of waiting minutes.     ║
# ║                                                             ║
# ║  DEMO_MODE = True   → fast triggers  (presentation)        ║
# ║  DEMO_MODE = False  → real thresholds (production)         ║
# ╚══════════════════════════════════════════════════════════════╝
DEMO_MODE = False

from datetime import datetime
from typing import Dict, List, Optional, Callable
from collections import deque
import statistics


class AbnormalityType:
    """All detectable abnormality types"""

    # Priority 1 — High Confidence
    MECHANICAL_TYPING   = "mechanical_typing"
    PASTE_HEAVY_WORK    = "paste_heavy_work"
    SUSPICIOUS_PASTE    = "suspicious_paste"
    RAPID_PASTE         = "rapid_paste"
    LONG_IDLE           = "long_idle"
    SUPERHUMAN_SPEED    = "superhuman_speed"

    # Priority 2 — Suspicious Patterns
    MOUSE_JIGGLER       = "mouse_jiggler"
    MINIMAL_ACTIVITY    = "minimal_activity"
    KEYBOARD_SITTING    = "keyboard_sitting"
    CLOCK_IN_CLOCK_OUT  = "clock_in_clock_out"
    BURST_THEN_IDLE     = "burst_then_idle"

    # Priority 3 — Advanced
    ACTIVITY_BURST      = "activity_burst"
    AUTOMATED_MOUSE     = "automated_mouse"

    # Meta
    MULTIPLE_ABNORMALITIES = "multiple_abnormalities"
    HIGH_RISK_SESSION      = "high_risk_session"


class Abnormality:
    """Single detected abnormality"""

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
    One instance per session, created by main.py after session starts.
    """

    def __init__(
        self,
        on_abnormality_detected: Optional[Callable] = None,
        confidence_threshold: float = 0.7
    ):
        """
        Args:
            on_abnormality_detected: UI callback only — does NOT write to DB.
            confidence_threshold:    Minimum confidence to surface (default 0.7)
        """
        self.on_abnormality_detected = on_abnormality_detected
        self.confidence_threshold    = confidence_threshold

        # In-session history
        self.detected_abnormalities: List[Abnormality] = []
        self.recent_pastes = deque(maxlen=50)

        # Shared buffers — InputCollector populates these via pynput hooks
        self.keystroke_intervals = deque(maxlen=200)
        self.mouse_movements     = deque(maxlen=200)
        self.paste_events        = deque(maxlen=50)
        self.activity_timeline   = deque(maxlen=1000)

        # State for burst_then_idle detection
        self._last_active_keystrokes: int = 0
        self._burst_detected_at: Optional[datetime] = None

        # ── Thresholds ────────────────────────────────────────
        self.MECHANICAL_VARIANCE_THRESHOLD = 0.15
        self.RAPID_PASTE_THRESHOLD         = 2
        self.PASTE_RATIO_THRESHOLD         = 0.3
        self.LARGE_PASTE_RATIO_THRESHOLD   = 0.5
        self.JIGGLER_MOVEMENT_SIZE         = 10     # pixels
        self.SUPERHUMAN_WPM                = 150
        self.MINIMAL_ACTIVITY_THRESHOLD    = 10     # keystrokes per minute

        if DEMO_MODE:
            self.IDLE_THRESHOLD_SECONDS    = 15
            self.MINIMAL_ACTIVITY_GRACE    = 30
            self.LARGE_PASTE_MIN_COUNT     = 2
            self.LARGE_PASTE_SESSION_MIN   = 15
            self.CLOCK_IN_IDLE_THRESHOLD   = 20
            self.BURST_IDLE_THRESHOLD      = 20
            self.BURST_KEYSTROKE_THRESHOLD = 5
        else:
            self.IDLE_THRESHOLD_SECONDS    = 300    # 5 minutes
            self.MINIMAL_ACTIVITY_GRACE    = 300    # 5-minute warmup
            self.LARGE_PASTE_MIN_COUNT     = 10
            self.LARGE_PASTE_SESSION_MIN   = 300    # session must be 5+ min old
            self.CLOCK_IN_IDLE_THRESHOLD   = 120    # 2 minutes
            self.BURST_IDLE_THRESHOLD      = 180    # 3 minutes silence after burst
            self.BURST_KEYSTROKE_THRESHOLD = 30

    # ═══════════════════════════════════════════════════════════
    # PRIORITY 1 — HIGH-CONFIDENCE DETECTIONS
    # ═══════════════════════════════════════════════════════════

    def analyze_keystroke_pattern(self, pattern_data: Dict) -> Optional[Abnormality]:
        """
        Detect mechanical/bot-like keystroke timing.
        Real humans vary their typing rhythm. Bot scripts produce unnaturally
        consistent inter-key intervals — very low variance.
        """
        if not pattern_data or pattern_data.get("status") != "ok":
            return None

        consistency = pattern_data.get("consistency_score", 1.0)
        sample_size = pattern_data.get("sample_size", 0)

        if sample_size < 50:
            return None

        if consistency < self.MECHANICAL_VARIANCE_THRESHOLD:
            confidence = 1.0 - (consistency / self.MECHANICAL_VARIANCE_THRESHOLD)
            if confidence >= self.confidence_threshold:
                return self._make(
                    AbnormalityType.MECHANICAL_TYPING, confidence,
                    {
                        "consistency_score": round(consistency, 4),
                        "avg_interval_ms":   pattern_data.get("avg_interval_ms"),
                        "std_deviation":     pattern_data.get("std_deviation"),
                        "sample_size":       sample_size,
                        "description":       f"Mechanical typing — consistency {consistency:.3f} "
                                             f"(threshold {self.MECHANICAL_VARIANCE_THRESHOLD})"
                    }
                )
        return None

    def analyze_paste_behavior(
        self,
        total_pastes: int,
        total_keystrokes: int,
        session_duration_seconds: float
    ) -> Optional[Abnormality]:
        """
        Detect work that is overwhelmingly copy-paste.
        Catches employees pasting AI-generated content as their own work.
        """
        if session_duration_seconds < 60 or total_keystrokes < 10:
            return None

        paste_ratio = total_pastes / total_keystrokes if total_keystrokes > 0 else 0

        if paste_ratio > self.PASTE_RATIO_THRESHOLD and total_pastes >= 5:
            confidence = min(paste_ratio / 0.5, 1.0)
            if confidence >= self.confidence_threshold:
                return self._make(
                    AbnormalityType.PASTE_HEAVY_WORK, confidence,
                    {
                        "paste_ratio":      round(paste_ratio, 3),
                        "total_pastes":     total_pastes,
                        "total_keystrokes": total_keystrokes,
                        "description":      f"Work is {int(paste_ratio*100)}% paste operations "
                                            f"({total_pastes} pastes vs {total_keystrokes} keystrokes)"
                    }
                )
        return None

    def analyze_large_paste_behavior(
        self,
        total_large_pastes: int,
        total_pastes: int,
        session_duration_seconds: float
    ) -> Optional[Abnormality]:
        """
        Detect repeated very large paste operations (1000+ chars).
        Catches bulk AI/internet content being pasted as work output.
        Thresholds are intentionally high to avoid flagging legitimate
        developer workflows (pasting config files, code templates etc).
        """
        if session_duration_seconds < self.LARGE_PASTE_SESSION_MIN:
            return None
        if total_pastes == 0 or total_large_pastes < self.LARGE_PASTE_MIN_COUNT:
            return None

        large_paste_ratio = total_large_pastes / total_pastes

        if large_paste_ratio > self.LARGE_PASTE_RATIO_THRESHOLD:
            confidence = min(large_paste_ratio, 1.0)
            if confidence >= self.confidence_threshold:
                return self._make(
                    AbnormalityType.SUSPICIOUS_PASTE, confidence,
                    {
                        "large_paste_ratio":  round(large_paste_ratio, 3),
                        "total_large_pastes": total_large_pastes,
                        "total_pastes":       total_pastes,
                        "description":        f"{int(large_paste_ratio*100)}% of pastes are very large "
                                              f"(1000+ chars) — {total_large_pastes} of {total_pastes} total"
                    }
                )
        return None

    def analyze_idle_period(
        self,
        idle_seconds: float,
        is_work_time: bool
    ) -> Optional[Abnormality]:
        """
        Detect extended time away from keyboard during work time.
        Catches employees leaving their desk while clocked in.
        """
        if not is_work_time:
            return None

        if idle_seconds > self.IDLE_THRESHOLD_SECONDS:
            confidence = min(idle_seconds / (self.IDLE_THRESHOLD_SECONDS * 2), 1.0)
            if confidence >= self.confidence_threshold:
                return self._make(
                    AbnormalityType.LONG_IDLE, confidence,
                    {
                        "idle_seconds": round(idle_seconds),
                        "idle_minutes": round(idle_seconds / 60, 1),
                        "threshold_minutes": round(self.IDLE_THRESHOLD_SECONDS / 60, 1),
                        "description":  f"Idle for {idle_seconds/60:.1f} min during work time "
                                        f"(threshold: {self.IDLE_THRESHOLD_SECONDS/60:.0f} min)"
                    }
                )
        return None

    def track_paste_event(self, timestamp: datetime) -> Optional[Abnormality]:
        """
        Detect rapid consecutive paste bursts.
        Multiple pastes in under 30 seconds = suspicious.
        """
        self.recent_pastes.append(timestamp)

        if len(self.recent_pastes) >= self.RAPID_PASTE_THRESHOLD:
            recent    = list(self.recent_pastes)[-self.RAPID_PASTE_THRESHOLD:]
            time_span = (recent[-1] - recent[0]).total_seconds()

            if time_span < 30:
                confidence = min(self.RAPID_PASTE_THRESHOLD / 3, 1.0)
                if confidence >= self.confidence_threshold:
                    return self._make(
                        AbnormalityType.RAPID_PASTE, confidence,
                        {
                            "paste_count":       len(recent),
                            "time_span_seconds": round(time_span, 1),
                            "description":       f"{len(recent)} pastes in {time_span:.1f}s"
                        }
                    )
        return None

    def detect_superhuman_speed(self, wpm: float) -> Optional[Abnormality]:
        """
        Detect typing speed that exceeds human capability.
        Catches macro replay — text is 'typed' by software, not a person.
        World typing record is ~216 WPM. Flag above 150 WPM sustained.
        """
        if wpm > self.SUPERHUMAN_WPM:
            confidence = min((wpm - self.SUPERHUMAN_WPM) / self.SUPERHUMAN_WPM, 1.0)
            if confidence >= self.confidence_threshold:
                return self._make(
                    AbnormalityType.SUPERHUMAN_SPEED, confidence,
                    {
                        "wpm":         round(wpm, 1),
                        "threshold":   self.SUPERHUMAN_WPM,
                        "description": f"Typing speed {wpm:.0f} WPM exceeds human capability "
                                       f"(threshold: {self.SUPERHUMAN_WPM} WPM)"
                    }
                )
        return None

    # ═══════════════════════════════════════════════════════════
    # PRIORITY 2 — SUSPICIOUS PATTERN DETECTION
    # ═══════════════════════════════════════════════════════════

    def detect_mouse_jiggler(self, movements: List[Dict]) -> Optional[Abnormality]:
        """
        Detect mouse jiggler devices or anti-idle software.

        WHAT IT CATCHES:
          - Physical USB mouse jiggler devices (make tiny regular movements)
          - Software jigglers / anti-idle apps (e.g. Caffeine, MouseJiggler)
          - Macro scripts that move the mouse on a fixed timer

        WHY IT MATTERS:
          Many employees use these to keep their status green (active) in
          Teams/Slack/monitoring tools while not actually working.

        TWO STRATEGIES run in parallel:

        Strategy A — distance-based:
          If InputCollector records pixel distance, look for tiny movements
          (< 10px) at suspiciously regular time intervals. Jigglers typically
          move 2–5 pixels every 10–30 seconds.

        Strategy B — interval-based (always runs):
          Real human mouse movement is irregular — people move mice in bursts.
          Jigglers produce extremely consistent millisecond intervals.
          Look for movements where std_dev < 500ms and avg is 1–10 seconds.
        """
        if len(movements) < 20:
            return None

        # ── Strategy A: pixel distance ────────────────────────
        with_distance = [m for m in movements if 'distance' in m]
        if len(with_distance) >= 20:
            small = [m for m in with_distance
                     if m.get('distance', 999) < self.JIGGLER_MOVEMENT_SIZE]

            if len(small) > 10:
                intervals = []
                for i in range(1, len(small)):
                    m_curr, m_prev = small[i], small[i - 1]
                    if 'timestamp' in m_curr and 'timestamp' in m_prev:
                        intervals.append(
                            (m_curr['timestamp'] - m_prev['timestamp']).total_seconds()
                        )

                if intervals:
                    avg   = statistics.mean(intervals)
                    stdev = statistics.stdev(intervals) if len(intervals) > 1 else 0

                    if stdev < 2 and 5 < avg < 60:
                        return self._make(
                            AbnormalityType.MOUSE_JIGGLER, 0.92,
                            {
                                "strategy":             "distance",
                                "small_movements":       len(small),
                                "avg_interval_seconds":  round(avg, 2),
                                "stdev_seconds":         round(stdev, 3),
                                "regularity":            round(1.0 - (stdev / avg), 3) if avg > 0 else 0,
                                "description":           f"Mouse jiggler — tiny movements "
                                                         f"every {avg:.1f}s ±{stdev:.2f}s"
                            }
                        )

        # ── Strategy B: interval_ms timing ───────────────────
        recent       = list(movements)[-20:]
        intervals_ms = [m['interval_ms'] for m in recent if 'interval_ms' in m]

        if len(intervals_ms) >= 10:
            avg_ms  = sum(intervals_ms) / len(intervals_ms)
            var_ms  = sum((x - avg_ms) ** 2 for x in intervals_ms) / len(intervals_ms)
            std_ms  = var_ms ** 0.5

            # Regular 1–10 second intervals with very low variance = jiggler
            if std_ms < 500 and 1000 < avg_ms < 10000:
                regularity = max(0.0, 1.0 - (std_ms / avg_ms)) if avg_ms > 0 else 0
                confidence = max(0.7, regularity)

                if confidence >= self.confidence_threshold:
                    return self._make(
                        AbnormalityType.MOUSE_JIGGLER, round(confidence, 2),
                        {
                            "strategy":         "interval",
                            "avg_interval_ms":  round(avg_ms),
                            "std_dev_ms":       round(std_ms),
                            "regularity":       round(regularity, 2),
                            "description":      f"Mouse jiggler — movement every "
                                                f"{avg_ms/1000:.1f}s ±{std_ms/1000:.2f}s"
                        }
                    )
        return None

    def detect_minimal_activity(
        self,
        keystrokes_per_minute: float,
        is_work_time: bool,
        session_duration_seconds: float = 0
    ) -> Optional[Abnormality]:
        """
        Detect suspiciously low keyboard activity during work time.

        WHAT IT CATCHES:
          - Employee present but barely doing anything
          - Someone who opened the app and walked away
          - Gaming the system with minimal periodic input

        Grace period: first N seconds of session are ignored so the employee
        has time to open their tools and settle in before being judged.
        """
        if not is_work_time:
            return None
        if session_duration_seconds < self.MINIMAL_ACTIVITY_GRACE:
            return None
        if keystrokes_per_minute > self.MINIMAL_ACTIVITY_THRESHOLD:
            return None

        confidence = 1.0 - (keystrokes_per_minute / self.MINIMAL_ACTIVITY_THRESHOLD)

        if confidence >= self.confidence_threshold:
            return self._make(
                AbnormalityType.MINIMAL_ACTIVITY, confidence,
                {
                    "keystrokes_per_minute": round(keystrokes_per_minute, 1),
                    "threshold":             self.MINIMAL_ACTIVITY_THRESHOLD,
                    "description":           f"Very low activity: {keystrokes_per_minute:.1f} keys/min "
                                             f"(threshold: {self.MINIMAL_ACTIVITY_THRESHOLD})"
                }
            )
        return None

    def detect_clock_in_clock_out(
        self,
        session_duration_seconds: float,
        idle_seconds: float,
        total_keystrokes: int,
        is_work_time: bool
    ) -> Optional[Abnormality]:
        """
        Detect 'badge and leave' — employee clocks in then immediately
        goes idle without doing meaningful work.

        WHAT IT CATCHES:
          - Employee starts session then leaves desk immediately
          - Auto-start scripts that clock in on behalf of the employee
          - Sessions where idle fills almost the entire session from the start

        Common in remote work: employee turns on PC, starts session, goes back
        to bed. The app is running but nobody is at the keyboard.
        """
        if not is_work_time:
            return None
        if session_duration_seconds < self.CLOCK_IN_IDLE_THRESHOLD:
            return None
        if total_keystrokes > 20:
            return None

        if idle_seconds > (session_duration_seconds * 0.8):
            confidence = min(idle_seconds / session_duration_seconds, 1.0)
            if confidence >= self.confidence_threshold:
                return self._make(
                    AbnormalityType.CLOCK_IN_CLOCK_OUT, confidence,
                    {
                        "session_duration_seconds": round(session_duration_seconds),
                        "idle_seconds":             round(idle_seconds),
                        "total_keystrokes":         total_keystrokes,
                        "idle_ratio":               round(idle_seconds / session_duration_seconds, 2),
                        "description":              f"Clocked in but idle for "
                                                    f"{idle_seconds/session_duration_seconds*100:.0f}% "
                                                    f"of session with only {total_keystrokes} keystrokes"
                    }
                )
        return None

    def detect_burst_then_idle(
        self,
        total_keystrokes: int,
        idle_seconds: float,
        session_duration_seconds: float,
        is_work_time: bool
    ) -> Optional[Abnormality]:
        """
        Detect 'sprint and disappear' — a flurry of activity followed by
        a long unexplained silence.

        WHAT IT CATCHES:
          - Employee finishes all tasks quickly, submits, then stays clocked in
            while doing nothing (browsing, personal activities)
          - Automated scripts that batch-submit work then go idle
          - Employees who front-load activity to make metrics look good

        The pattern: fast typing → submit → silence for 30+ minutes.
        """
        if not is_work_time:
            return None
        if session_duration_seconds < (self.BURST_IDLE_THRESHOLD * 2):
            return None

        keystroke_delta = total_keystrokes - self._last_active_keystrokes

        if keystroke_delta >= self.BURST_KEYSTROKE_THRESHOLD and self._burst_detected_at is None:
            self._burst_detected_at      = datetime.now()
            self._last_active_keystrokes = total_keystrokes

        elif self._burst_detected_at is not None:
            seconds_since_burst = (datetime.now() - self._burst_detected_at).total_seconds()

            if idle_seconds > self.BURST_IDLE_THRESHOLD and seconds_since_burst > self.BURST_IDLE_THRESHOLD:
                confidence = min(idle_seconds / (self.BURST_IDLE_THRESHOLD * 2), 0.95)

                if confidence >= self.confidence_threshold:
                    self._burst_detected_at      = None
                    self._last_active_keystrokes = total_keystrokes

                    return self._make(
                        AbnormalityType.BURST_THEN_IDLE, confidence,
                        {
                            "burst_keystrokes":   keystroke_delta,
                            "idle_seconds_after": round(idle_seconds),
                            "description":        f"Activity burst ({keystroke_delta} keystrokes) "
                                                  f"followed by {idle_seconds/60:.1f} min silence"
                        }
                    )

        if keystroke_delta < self.BURST_KEYSTROKE_THRESHOLD:
            self._last_active_keystrokes = total_keystrokes

        return None

    def detect_periodic_activity_burst(
        self,
        activity_timeline: List[Dict]
    ) -> Optional[Abnormality]:
        """
        Detect suspiciously clock-like burst/idle cycles.

        WHAT IT CATCHES:
          - Macro scripts that simulate work on a fixed timer
            (e.g. type 10 keys, pause 2 min, type 10 keys, pause 2 min...)
          - Anti-idle software with periodic keypress injection
          - Any automated system that produces activity at regular intervals

        Real work is messy and irregular. Scripts are clocklike.
        Measures regularity of gaps between activity events.
        """
        if len(activity_timeline) < 6:
            return None

        timestamps = [e.get('timestamp') for e in activity_timeline if e.get('timestamp')]
        if len(timestamps) < 6:
            return None

        gaps = []
        for i in range(1, len(timestamps)):
            try:
                t1 = datetime.fromisoformat(timestamps[i]) \
                     if isinstance(timestamps[i], str) else timestamps[i]
                t0 = datetime.fromisoformat(timestamps[i-1]) \
                     if isinstance(timestamps[i-1], str) else timestamps[i-1]
                gaps.append((t1 - t0).total_seconds())
            except Exception:
                continue

        if len(gaps) < 5:
            return None

        avg_gap   = statistics.mean(gaps)
        stdev_gap = statistics.stdev(gaps) if len(gaps) > 1 else 0

        if stdev_gap < 5 and 30 < avg_gap < 300:
            regularity = 1.0 - (stdev_gap / avg_gap) if avg_gap > 0 else 0
            confidence = max(0.7, min(regularity, 0.95))

            if confidence >= self.confidence_threshold:
                return self._make(
                    AbnormalityType.ACTIVITY_BURST, confidence,
                    {
                        "avg_gap_seconds": round(avg_gap, 1),
                        "stdev_seconds":   round(stdev_gap, 2),
                        "regularity":      round(regularity, 2),
                        "event_count":     len(gaps),
                        "description":     f"Activity bursts are suspiciously regular "
                                           f"(every {avg_gap:.0f}s ±{stdev_gap:.1f}s)"
                    }
                )
        return None

    # ═══════════════════════════════════════════════════════════
    # COMPREHENSIVE ANALYSIS — called every 30 seconds by main.py
    # ═══════════════════════════════════════════════════════════

    def run_comprehensive_analysis(
        self,
        keystroke_pattern: Dict,
        activity_summary: Dict,
        is_work_time: bool
    ) -> List[Abnormality]:
        """
        Run every detection algorithm in sequence.
        Returns a list of Abnormality objects found this cycle.
        main.py saves each one via _save_abnormality_to_aggregator().
        No double-counting — this is the only write path.
        """
        detected = []
        dur = activity_summary.get("session_duration_seconds", 0)
        ks  = activity_summary.get("total_keystrokes", 0)

        def _add(result):
            if result:
                detected.append(result)

        # ── Priority 1 ──────────────────────────────────────
        _add(self.analyze_keystroke_pattern(keystroke_pattern))

        _add(self.analyze_paste_behavior(
            total_pastes=activity_summary.get("total_pastes", 0),
            total_keystrokes=ks,
            session_duration_seconds=dur
        ))

        _add(self.analyze_large_paste_behavior(
            total_large_pastes=activity_summary.get("total_large_pastes", 0),
            total_pastes=activity_summary.get("total_pastes", 0),
            session_duration_seconds=dur
        ))

        _add(self.analyze_idle_period(
            idle_seconds=activity_summary.get("idle_seconds", 0),
            is_work_time=is_work_time
        ))

        # WPM from keystroke rate (chars/min ÷ 5 = words/min)
        kpm = (ks / dur) * 60 if dur > 0 else 0
        _add(self.detect_superhuman_speed(kpm / 5))

        # ── Priority 2 ──────────────────────────────────────
        _add(self.detect_minimal_activity(kpm, is_work_time, dur))

        # Mouse jiggler — reads internal buffer populated by InputCollector
        _add(self.detect_mouse_jiggler(list(self.mouse_movements)))

        _add(self.detect_clock_in_clock_out(
            session_duration_seconds=dur,
            idle_seconds=activity_summary.get("idle_seconds", 0),
            total_keystrokes=ks,
            is_work_time=is_work_time
        ))

        _add(self.detect_burst_then_idle(
            total_keystrokes=ks,
            idle_seconds=activity_summary.get("idle_seconds", 0),
            session_duration_seconds=dur,
            is_work_time=is_work_time
        ))

        # ── Priority 3 ──────────────────────────────────────
        _add(self.detect_periodic_activity_burst(list(self.activity_timeline)))

        return detected

    # ═══════════════════════════════════════════════════════════
    # INTERNAL HELPERS
    # ═══════════════════════════════════════════════════════════

    def _make(
        self,
        abnormality_type: str,
        confidence: float,
        metadata: Dict
    ) -> Abnormality:
        """Create, store locally, and surface an Abnormality."""
        abn = Abnormality(
            abnormality_type=abnormality_type,
            confidence_score=round(min(confidence, 1.0), 4),
            detected_at=datetime.now(),
            metadata=metadata
        )
        self._report_abnormality(abn)
        return abn

    def _report_abnormality(self, abnormality: Abnormality):
        """
        Append to in-session list and fire the UI callback.
        Does NOT write to SQLite or Supabase — that is main.py's job via
        _save_abnormality_to_aggregator().
        """
        self.detected_abnormalities.append(abnormality)
        if self.on_abnormality_detected:
            self.on_abnormality_detected(abnormality)

    def get_session_abnormalities(self) -> List[Dict]:
        return [a.to_dict() for a in self.detected_abnormalities]

    def clear_session(self):
        self.detected_abnormalities.clear()
        self.recent_pastes.clear()
        self._burst_detected_at = None
        self._last_active_keystrokes = 0

    def get_risk_score(self) -> float:
        """Weighted risk score 0–100 across all detections this session."""
        if not self.detected_abnormalities:
            return 0.0

        weights = {
            AbnormalityType.MECHANICAL_TYPING:  1.0,
            AbnormalityType.MOUSE_JIGGLER:       1.0,
            AbnormalityType.CLOCK_IN_CLOCK_OUT:  1.0,
            AbnormalityType.SUPERHUMAN_SPEED:    0.95,
            AbnormalityType.SUSPICIOUS_PASTE:    0.9,
            AbnormalityType.BURST_THEN_IDLE:     0.85,
            AbnormalityType.PASTE_HEAVY_WORK:    0.8,
            AbnormalityType.ACTIVITY_BURST:      0.8,
            AbnormalityType.RAPID_PASTE:         0.75,
            AbnormalityType.LONG_IDLE:           0.65,
            AbnormalityType.MINIMAL_ACTIVITY:    0.55,
            AbnormalityType.KEYBOARD_SITTING:    0.55,
            AbnormalityType.AUTOMATED_MOUSE:     0.7,
        }

        total_w, total_s = 0.0, 0.0
        for abn in self.detected_abnormalities:
            w = weights.get(abn.abnormality_type, 0.5)
            total_s += abn.confidence_score * w * 100
            total_w += w

        score = total_s / total_w if total_w > 0 else 0

        if len(self.detected_abnormalities) >= 3:
            score *= 1.2  # 20% boost for multiple simultaneous flags

        return min(score, 100.0)


# Backward-compat alias
EnhancedAbnormalityDetector = AbnormalityDetector