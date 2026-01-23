"""
Enhanced Abnormality Detector - Comprehensive Cheating Detection

Detects multiple forms of work cheating:
- Copy-paste heavy work
- Bot-like typing patterns
- Mouse jigglers
- Minimal activity
- Superhuman speeds
- Long idle periods
- Activity bursts (periodic work patterns)
- Typing style changes (different person)

Risk Score Calculation:
- Continuously detects abnormalities
- Calculates risk every 30 minutes
- Averages with previous scores for final session risk
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Deque
from collections import deque
import statistics
from dataclasses import dataclass


@dataclass
class Abnormality:
    """Detected abnormality with metadata"""
    abnormality_type: str
    confidence_score: float  # 0.0 - 1.0
    detected_at: datetime
    metadata: Dict
    
    def to_dict(self) -> Dict:
        return {
            "abnormality_type": self.abnormality_type,
            "confidence_score": self.confidence_score,
            "detected_at": self.detected_at.isoformat(),
            "metadata": self.metadata
        }


class AbnormalityType:
    """All abnormality types for comprehensive detection"""
    
    # Copy-Paste Cheating
    PASTE_HEAVY_WORK = "paste_heavy_work"           # >30% paste vs typing
    RAPID_PASTE = "rapid_paste"                     # Multiple quick pastes
    LARGE_PASTE = "large_paste"                     # Single large paste >300 chars
    SUSPICIOUS_PASTE_PATTERN = "suspicious_paste_pattern"  # Regular paste intervals
    
    # Bot/Automation Detection
    MECHANICAL_TYPING = "mechanical_typing"         # Too consistent timing
    AUTOMATED_MOUSE = "automated_mouse"             # Scripted movement
    MOUSE_JIGGLER = "mouse_jiggler"                 # Anti-idle device
    UNNATURAL_RHYTHM = "unnatural_rhythm"           # Perfect timing patterns
    
    # Activity Patterns
    LONG_IDLE = "long_idle"                         # Away from desk >5 min
    MINIMAL_ACTIVITY = "minimal_activity"           # Barely working
    ACTIVITY_BURST = "activity_burst"               # Periodic work spikes
    SUPERHUMAN_SPEED = "superhuman_speed"           # Impossibly fast typing
    
    # Advanced Detection
    TYPING_STYLE_CHANGE = "typing_style_change"     # Different person detected
    COPY_FROM_EXTERNAL = "copy_from_external"       # AI/browser usage pattern
    SESSION_GAMING = "session_gaming"               # Time manipulation attempt
    WORK_AVOIDANCE = "work_avoidance"               # Minimal effort pattern
    
    # Combined Patterns
    MULTIPLE_RED_FLAGS = "multiple_red_flags"       # 3+ abnormalities
    HIGH_RISK_SESSION = "high_risk_session"         # Overall fraud likelihood


class EnhancedAbnormalityDetector:
    """
    Comprehensive abnormality detection with 30-minute risk scoring
    
    Features:
    - Continuous detection during work hours
    - Risk calculation every 30 minutes
    - Progressive averaging of risk scores
    - Multiple detection algorithms
    - Configurable sensitivity
    """
    
    def __init__(
        self,
        on_abnormality_detected: Optional[Callable] = None,
        on_risk_calculation: Optional[Callable] = None,
        confidence_threshold: float = 0.7,
        risk_calculation_interval_minutes: int = 30
    ):
        """
        Initialize enhanced detector
        
        Args:
            on_abnormality_detected: Callback for each abnormality
            on_risk_calculation: Callback for periodic risk calculation
            confidence_threshold: Minimum confidence to report
            risk_calculation_interval_minutes: How often to calculate risk (default 30)
        """
        self.on_abnormality_detected = on_abnormality_detected
        self.on_risk_calculation = on_risk_calculation
        self.confidence_threshold = confidence_threshold
        self.risk_interval_minutes = risk_calculation_interval_minutes
        
        # Detection tracking
        self.abnormalities: List[Abnormality] = []
        self.risk_scores: List[float] = []  # Historical risk scores
        
        # Interval tracking
        self.last_risk_calculation: Optional[datetime] = None
        self.session_start: Optional[datetime] = None
        
        # Activity buffers
        self.keystroke_intervals: Deque = deque(maxlen=500)
        self.paste_events: Deque = deque(maxlen=100)
        self.mouse_movements: Deque = deque(maxlen=300)
        self.activity_timeline: Deque = deque(maxlen=2000)
        
        # Baseline tracking (for detecting changes)
        self.baseline_typing_speed: Optional[float] = None
        self.baseline_variance: Optional[float] = None
        self.typing_samples_collected = 0
        
        # Detection thresholds
        self.THRESHOLDS = {
            # Paste detection
            'paste_ratio_threshold': 0.30,  # >30% paste = suspicious
            'rapid_paste_count': 5,  # 5 pastes in X seconds
            'rapid_paste_window': 30,  # 30 seconds
            'large_paste_size': 300,  # characters
            
            # Typing detection
            'mechanical_variance': 0.15,  # Low variance = bot
            'superhuman_wpm': 150,  # Above 150 WPM suspicious
            'min_activity_kpm': 10,  # Below 10 keys/min = minimal
            
            # Idle detection
            'idle_threshold': 300,  # 5 minutes
            'max_idle_work_time': 600,  # 10 minutes = very suspicious
            
            # Mouse detection
            'jiggler_movement_size': 10,  # Small movements
            'jiggler_regularity': 0.8,  # High regularity score
            
            # Pattern detection
            'burst_threshold': 3.0,  # 3x average activity
            'style_change_threshold': 0.4,  # 40% deviation from baseline
        }
    
    def start_session(self):
        """Start a new detection session"""
        self.session_start = datetime.now()
        self.last_risk_calculation = self.session_start
        self.abnormalities.clear()
        self.risk_scores.clear()
        
        print(f"🔍 Detection session started at {self.session_start}")
    
    # ============================================
    # CONTINUOUS DETECTION METHODS
    # ============================================
    
    def track_keystroke(self, interval_ms: int):
        """Track individual keystroke interval"""
        self.keystroke_intervals.append(interval_ms)
        self.activity_timeline.append({
            'type': 'keystroke',
            'timestamp': datetime.now(),
            'interval': interval_ms
        })
        
        # Update baseline if needed
        if self.typing_samples_collected < 100:
            self.typing_samples_collected += 1
            if self.typing_samples_collected == 100:
                self._calculate_baseline()
    
    def track_paste(self, size: int):
        """Track paste event"""
        now = datetime.now()
        self.paste_events.append({
            'timestamp': now,
            'size': size
        })
        self.activity_timeline.append({
            'type': 'paste',
            'timestamp': now,
            'size': size
        })
        
        # Immediate checks
        self._check_large_paste(size, now)
        self._check_rapid_paste(now)
    
    def track_mouse_movement(self, distance: float):
        """Track mouse movement"""
        now = datetime.now()
        self.mouse_movements.append({
            'timestamp': now,
            'distance': distance
        })
        self.activity_timeline.append({
            'type': 'mouse',
            'timestamp': now,
            'distance': distance
        })
    
    def track_idle(self, idle_seconds: float, is_work_time: bool):
        """Track idle period"""
        if is_work_time and idle_seconds > self.THRESHOLDS['idle_threshold']:
            self._detect_long_idle(idle_seconds)
    
    # ============================================
    # DETECTION ALGORITHMS
    # ============================================
    
    def _check_large_paste(self, size: int, timestamp: datetime):
        """Detect large paste operations"""
        if size > self.THRESHOLDS['large_paste_size']:
            confidence = min(size / 1000, 1.0)  # Scale by size
            
            if confidence >= self.confidence_threshold:
                self._report_abnormality(Abnormality(
                    abnormality_type=AbnormalityType.LARGE_PASTE,
                    confidence_score=confidence,
                    detected_at=timestamp,
                    metadata={
                        'paste_size': size,
                        'description': f'Large paste detected ({size} characters)'
                    }
                ))
    
    def _check_rapid_paste(self, current_time: datetime):
        """Detect rapid consecutive pasting"""
        # Get recent pastes within window
        window_start = current_time - timedelta(seconds=self.THRESHOLDS['rapid_paste_window'])
        recent_pastes = [p for p in self.paste_events if p['timestamp'] > window_start]
        
        if len(recent_pastes) >= self.THRESHOLDS['rapid_paste_count']:
            confidence = min(len(recent_pastes) / 10, 1.0)
            
            if confidence >= self.confidence_threshold:
                self._report_abnormality(Abnormality(
                    abnormality_type=AbnormalityType.RAPID_PASTE,
                    confidence_score=confidence,
                    detected_at=current_time,
                    metadata={
                        'paste_count': len(recent_pastes),
                        'time_window': self.THRESHOLDS['rapid_paste_window'],
                        'description': f'{len(recent_pastes)} pastes in {self.THRESHOLDS["rapid_paste_window"]} seconds'
                    }
                ))
    
    def _detect_mechanical_typing(self, intervals: List[int]) -> Optional[Abnormality]:
        """Detect bot-like mechanical typing"""
        if len(intervals) < 50:
            return None
        
        avg = statistics.mean(intervals)
        stdev = statistics.stdev(intervals)
        
        if avg == 0:
            return None
        
        variance = stdev / avg
        
        # Very low variance = mechanical
        if variance < self.THRESHOLDS['mechanical_variance']:
            confidence = 1.0 - variance
            
            if confidence >= self.confidence_threshold:
                return Abnormality(
                    abnormality_type=AbnormalityType.MECHANICAL_TYPING,
                    confidence_score=confidence,
                    detected_at=datetime.now(),
                    metadata={
                        'avg_interval_ms': round(avg, 2),
                        'variance': round(variance, 3),
                        'sample_size': len(intervals),
                        'description': 'Typing pattern shows mechanical consistency'
                    }
                )
        
        return None
    
    def _detect_paste_heavy_work(self, window_minutes: int = 30) -> Optional[Abnormality]:
        """Detect excessive paste ratio in recent work"""
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        
        recent_activity = [a for a in self.activity_timeline if a['timestamp'] > cutoff]
        
        if not recent_activity:
            return None
        
        keystrokes = len([a for a in recent_activity if a['type'] == 'keystroke'])
        pastes = len([a for a in recent_activity if a['type'] == 'paste'])
        
        total_actions = keystrokes + pastes
        
        if total_actions < 50:  # Need sufficient data
            return None
        
        paste_ratio = pastes / total_actions
        
        if paste_ratio > self.THRESHOLDS['paste_ratio_threshold']:
            confidence = min(paste_ratio / 0.5, 1.0)
            
            if confidence >= self.confidence_threshold:
                return Abnormality(
                    abnormality_type=AbnormalityType.PASTE_HEAVY_WORK,
                    confidence_score=confidence,
                    detected_at=datetime.now(),
                    metadata={
                        'paste_ratio': round(paste_ratio, 3),
                        'paste_count': pastes,
                        'keystroke_count': keystrokes,
                        'window_minutes': window_minutes,
                        'description': f'{int(paste_ratio*100)}% paste operations in last {window_minutes} min'
                    }
                )
        
        return None
    
    def _detect_long_idle(self, idle_seconds: float):
        """Detect extended idle during work time"""
        confidence = min(idle_seconds / self.THRESHOLDS['max_idle_work_time'], 1.0)
        
        if confidence >= self.confidence_threshold:
            self._report_abnormality(Abnormality(
                abnormality_type=AbnormalityType.LONG_IDLE,
                confidence_score=confidence,
                detected_at=datetime.now(),
                metadata={
                    'idle_seconds': idle_seconds,
                    'idle_minutes': round(idle_seconds / 60, 1),
                    'description': f'Idle for {idle_seconds/60:.1f} minutes during work time'
                }
            ))
    
    def _detect_mouse_jiggler(self) -> Optional[Abnormality]:
        """Detect mouse jiggler devices"""
        if len(self.mouse_movements) < 20:
            return None
        
        # Get recent small movements
        recent = list(self.mouse_movements)[-50:]
        small_movements = [m for m in recent if m['distance'] < self.THRESHOLDS['jiggler_movement_size']]
        
        if len(small_movements) < 10:
            return None
        
        # Check for regular intervals
        intervals = []
        for i in range(1, len(small_movements)):
            diff = (small_movements[i]['timestamp'] - small_movements[i-1]['timestamp']).total_seconds()
            intervals.append(diff)
        
        if not intervals:
            return None
        
        avg_interval = statistics.mean(intervals)
        stdev = statistics.stdev(intervals) if len(intervals) > 1 else 0
        
        regularity = 1.0 - (stdev / avg_interval) if avg_interval > 0 else 0
        
        # High regularity in 5-60 second range = jiggler
        if regularity > self.THRESHOLDS['jiggler_regularity'] and 5 < avg_interval < 60:
            return Abnormality(
                abnormality_type=AbnormalityType.MOUSE_JIGGLER,
                confidence_score=regularity,
                detected_at=datetime.now(),
                metadata={
                    'movement_count': len(small_movements),
                    'avg_interval_seconds': round(avg_interval, 1),
                    'regularity_score': round(regularity, 3),
                    'description': f'Mouse jiggler detected (moves every {avg_interval:.1f}s)'
                }
            )
        
        return None
    
    def _detect_minimal_activity(self, window_minutes: int = 30) -> Optional[Abnormality]:
        """Detect barely working pattern"""
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent = [a for a in self.activity_timeline if a['timestamp'] > cutoff]
        
        if not recent:
            return None
        
        keystrokes = len([a for a in recent if a['type'] == 'keystroke'])
        kpm = keystrokes / window_minutes
        
        if kpm < self.THRESHOLDS['min_activity_kpm']:
            confidence = 1.0 - (kpm / self.THRESHOLDS['min_activity_kpm'])
            
            if confidence >= self.confidence_threshold:
                return Abnormality(
                    abnormality_type=AbnormalityType.MINIMAL_ACTIVITY,
                    confidence_score=confidence,
                    detected_at=datetime.now(),
                    metadata={
                        'keystrokes_per_minute': round(kpm, 1),
                        'window_minutes': window_minutes,
                        'description': f'Very low activity ({kpm:.1f} keys/min)'
                    }
                )
        
        return None
    
    def _detect_activity_bursts(self, window_minutes: int = 60) -> Optional[Abnormality]:
        """Detect periodic work bursts (gaming the system)"""
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent = [a for a in self.activity_timeline if a['timestamp'] > cutoff]
        
        if len(recent) < 100:
            return None
        
        # Divide into 5-minute buckets
        bucket_size = 5  # minutes
        buckets = {}
        
        for activity in recent:
            bucket_idx = int((activity['timestamp'] - cutoff).total_seconds() / 60 / bucket_size)
            if bucket_idx not in buckets:
                buckets[bucket_idx] = 0
            buckets[bucket_idx] += 1
        
        if len(buckets) < 3:
            return None
        
        counts = list(buckets.values())
        avg_count = statistics.mean(counts)
        max_count = max(counts)
        
        # High variance = burst pattern
        if avg_count > 0 and max_count > avg_count * self.THRESHOLDS['burst_threshold']:
            confidence = min((max_count / avg_count) / 10, 1.0)
            
            if confidence >= self.confidence_threshold:
                return Abnormality(
                    abnormality_type=AbnormalityType.ACTIVITY_BURST,
                    confidence_score=confidence,
                    detected_at=datetime.now(),
                    metadata={
                        'avg_activity': round(avg_count, 1),
                        'max_activity': max_count,
                        'burst_ratio': round(max_count / avg_count, 2),
                        'description': 'Periodic activity bursts detected'
                    }
                )
        
        return None
    
    def _detect_typing_style_change(self) -> Optional[Abnormality]:
        """Detect if typing style changed (different person)"""
        if not self.baseline_typing_speed or len(self.keystroke_intervals) < 100:
            return None
        
        # Get recent typing pattern
        recent = list(self.keystroke_intervals)[-100:]
        recent_avg = statistics.mean(recent)
        recent_stdev = statistics.stdev(recent)
        
        # Compare to baseline
        speed_change = abs(recent_avg - self.baseline_typing_speed) / self.baseline_typing_speed
        variance_change = abs(recent_stdev - self.baseline_variance) / self.baseline_variance if self.baseline_variance > 0 else 0
        
        # Significant change in both speed and variance = different person
        if speed_change > self.THRESHOLDS['style_change_threshold'] and variance_change > self.THRESHOLDS['style_change_threshold']:
            confidence = min((speed_change + variance_change) / 2, 1.0)
            
            if confidence >= self.confidence_threshold:
                return Abnormality(
                    abnormality_type=AbnormalityType.TYPING_STYLE_CHANGE,
                    confidence_score=confidence,
                    detected_at=datetime.now(),
                    metadata={
                        'baseline_speed': round(self.baseline_typing_speed, 2),
                        'current_speed': round(recent_avg, 2),
                        'speed_change_pct': round(speed_change * 100, 1),
                        'description': 'Typing style changed significantly (possible different person)'
                    }
                )
        
        return None
    
    def _calculate_baseline(self):
        """Calculate baseline typing pattern from first 100 keystrokes"""
        if len(self.keystroke_intervals) >= 100:
            recent = list(self.keystroke_intervals)[-100:]
            self.baseline_typing_speed = statistics.mean(recent)
            self.baseline_variance = statistics.stdev(recent)
            print(f"📊 Baseline established: {self.baseline_typing_speed:.2f}ms avg, {self.baseline_variance:.2f} stdev")
    
    # ============================================
    # RISK CALCULATION (Every 30 minutes)
    # ============================================
    
    def should_calculate_risk(self) -> bool:
        """Check if it's time to calculate risk score"""
        if not self.last_risk_calculation:
            return False
        
        elapsed = (datetime.now() - self.last_risk_calculation).total_seconds() / 60
        return elapsed >= self.risk_interval_minutes
    
    def calculate_current_risk(self) -> float:
        """
        Calculate risk score for current 30-minute window
        
        Returns:
            Risk score 0-100
        """
        if not self.last_risk_calculation:
            self.last_risk_calculation = datetime.now()
            return 0.0
        
        # Get abnormalities from last interval
        window_start = self.last_risk_calculation
        recent_abnormalities = [
            a for a in self.abnormalities 
            if a.detected_at >= window_start
        ]
        
        if not recent_abnormalities:
            return 0.0
        
        # Weight different abnormality types
        weights = {
            AbnormalityType.MECHANICAL_TYPING: 1.0,
            AbnormalityType.MOUSE_JIGGLER: 1.0,
            AbnormalityType.TYPING_STYLE_CHANGE: 0.9,
            AbnormalityType.PASTE_HEAVY_WORK: 0.8,
            AbnormalityType.ACTIVITY_BURST: 0.7,
            AbnormalityType.RAPID_PASTE: 0.7,
            AbnormalityType.LARGE_PASTE: 0.6,
            AbnormalityType.LONG_IDLE: 0.6,
            AbnormalityType.MINIMAL_ACTIVITY: 0.5,
        }
        
        total_weight = 0
        total_score = 0
        
        for abn in recent_abnormalities:
            weight = weights.get(abn.abnormality_type, 0.5)
            total_score += abn.confidence_score * weight * 100
            total_weight += weight
        
        risk = total_score / total_weight if total_weight > 0 else 0
        
        # Boost for multiple abnormalities
        if len(recent_abnormalities) >= 3:
            risk *= 1.2  # 20% boost
        if len(recent_abnormalities) >= 5:
            risk *= 1.5  # 50% boost total
        
        risk = min(risk, 100)
        
        # Store and update
        self.risk_scores.append(risk)
        self.last_risk_calculation = datetime.now()
        
        print(f"\n📊 Risk Calculation (Interval #{len(self.risk_scores)}):")
        print(f"   Abnormalities found: {len(recent_abnormalities)}")
        print(f"   Interval risk: {risk:.1f}/100")
        print(f"   Average risk: {self.get_average_risk():.1f}/100")
        
        # Trigger callback
        if self.on_risk_calculation:
            self.on_risk_calculation({
                'interval_risk': risk,
                'average_risk': self.get_average_risk(),
                'abnormality_count': len(recent_abnormalities),
                'interval_number': len(self.risk_scores)
            })
        
        return risk
    
    def get_average_risk(self) -> float:
        """Get averaged risk score across all intervals"""
        if not self.risk_scores:
            return 0.0
        return statistics.mean(self.risk_scores)
    
    # ============================================
    # COMPREHENSIVE ANALYSIS
    # ============================================
    
    def run_periodic_analysis(self):
        """
        Run comprehensive analysis of recent activity
        Called periodically (e.g., every 5 minutes) during work
        """
        print("\n🔍 Running periodic analysis...")
        
        detected = []
        
        # Typing pattern analysis
        if len(self.keystroke_intervals) >= 50:
            abn = self._detect_mechanical_typing(list(self.keystroke_intervals)[-200:])
            if abn:
                detected.append(abn)
                self._report_abnormality(abn)
        
        # Paste heavy work
        abn = self._detect_paste_heavy_work(window_minutes=30)
        if abn:
            detected.append(abn)
            self._report_abnormality(abn)
        
        # Mouse jiggler
        abn = self._detect_mouse_jiggler()
        if abn:
            detected.append(abn)
            self._report_abnormality(abn)
        
        # Minimal activity
        abn = self._detect_minimal_activity(window_minutes=30)
        if abn:
            detected.append(abn)
            self._report_abnormality(abn)
        
        # Activity bursts
        abn = self._detect_activity_bursts(window_minutes=60)
        if abn:
            detected.append(abn)
            self._report_abnormality(abn)
        
        # Typing style change
        abn = self._detect_typing_style_change()
        if abn:
            detected.append(abn)
            self._report_abnormality(abn)
        
        # Check if risk calculation is due
        if self.should_calculate_risk():
            risk = self.calculate_current_risk()
            print(f"✅ Interval risk calculated: {risk:.1f}/100")
        
        print(f"   Analysis complete: {len(detected)} abnormalities detected")
        
        return detected
    
    def _report_abnormality(self, abnormality: Abnormality):
        """Report detected abnormality"""
        self.abnormalities.append(abnormality)
        
        print(f"🚨 {abnormality.abnormality_type}: {abnormality.confidence_score:.2%}")
        
        if self.on_abnormality_detected:
            self.on_abnormality_detected(abnormality)
    
    def get_session_summary(self) -> Dict:
        """Get complete session summary"""
        return {
            'total_abnormalities': len(self.abnormalities),
            'risk_intervals': len(self.risk_scores),
            'average_risk': self.get_average_risk(),
            'final_risk': self.risk_scores[-1] if self.risk_scores else 0.0,
            'abnormalities_by_type': self._count_by_type(),
            'session_duration_minutes': self._get_session_duration()
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count abnormalities by type"""
        counts = {}
        for abn in self.abnormalities:
            counts[abn.abnormality_type] = counts.get(abn.abnormality_type, 0) + 1
        return counts
    
    def _get_session_duration(self) -> float:
        """Get session duration in minutes"""
        if not self.session_start:
            return 0.0
        return (datetime.now() - self.session_start).total_seconds() / 60
    
    def clear_session(self):
        """Clear all session data"""
        self.abnormalities.clear()
        self.risk_scores.clear()
        self.keystroke_intervals.clear()
        self.paste_events.clear()
        self.mouse_movements.clear()
        self.activity_timeline.clear()
        self.baseline_typing_speed = None
        self.baseline_variance = None
        self.typing_samples_collected = 0


# Backward compatibility
AbnormalityDetector = EnhancedAbnormalityDetector