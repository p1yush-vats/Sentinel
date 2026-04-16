"""
test_jiggler_detection.py
Run this from desktop-app/src/ to test if mouse jiggler detection fires.

Usage:
    cd desktop-app/src
    python test_jiggler_detection.py

No real mouse movement needed — feeds fake data directly into the detectors.
"""

import sys
import time
from datetime import datetime, timedelta
from collections import deque

# ─────────────────────────────────────────────────────────────
# Minimal stubs so the script runs without the full app
# ─────────────────────────────────────────────────────────────

print("=" * 60)
print("SENTINEL — Mouse Jiggler Detection Test")
print("=" * 60)


# ─────────────────────────────────────────────────────────────
# TEST 1: AbnormalityDetector.detect_mouse_jiggler()
# ─────────────────────────────────────────────────────────────

print("\n[TEST 1] AbnormalityDetector.detect_mouse_jiggler()")
print("-" * 60)

try:
    from detection.abnormality_detector import AbnormalityDetector, AbnormalityType

    detector = AbnormalityDetector(confidence_threshold=0.7)

    # ── Case A: JIGGLER movements (small, regular intervals) ──
    base_time = datetime.now() - timedelta(minutes=5)
    jiggler_movements = []
    for i in range(25):
        jiggler_movements.append({
            "timestamp": base_time + timedelta(seconds=i * 10),  # every 10s
            "distance": 4,          # tiny movement (< JIGGLER_MOVEMENT_SIZE=10)
            "interval_ms": 10000,   # 10 second interval
        })

    result = detector.detect_mouse_jiggler(jiggler_movements)
    if result:
        print(f"  ✅ JIGGLER DETECTED")
        print(f"     Type       : {result.abnormality_type}")
        print(f"     Confidence : {result.confidence_score:.2f}")
        print(f"     Metadata   : {result.metadata}")
    else:
        print(f"  ❌ NOT detected (check distance/interval logic in abnormality_detector.py)")

    # ── Case B: NORMAL movements (large, irregular) ──
    normal_movements = []
    import random
    random.seed(42)
    for i in range(25):
        normal_movements.append({
            "timestamp": base_time + timedelta(seconds=i * random.uniform(1, 30)),
            "distance": random.randint(50, 400),   # big natural movements
            "interval_ms": random.randint(500, 15000),
        })

    result_normal = detector.detect_mouse_jiggler(normal_movements)
    if result_normal:
        print(f"  ⚠️  False positive on normal movements (confidence: {result_normal.confidence_score:.2f})")
    else:
        print(f"  ✅ Normal movement correctly NOT flagged")

except ImportError as e:
    print(f"  ⚠️  Could not import AbnormalityDetector: {e}")
    print(f"     Make sure you run from desktop-app/src/")


# ─────────────────────────────────────────────────────────────
# TEST 2: InputCollector._check_mouse_jiggler() (real-time layer)
# ─────────────────────────────────────────────────────────────

print("\n[TEST 2] InputCollector._check_mouse_jiggler() (real-time)")
print("-" * 60)

detected_patterns = []

def capture_pattern(pattern):
    detected_patterns.append(pattern)

try:
    from detection.input_collector import InputCollector

    collector = InputCollector(on_pattern_detected=capture_pattern)

    # Inject fake regular mouse movements directly into the buffer
    base_time = datetime.now() - timedelta(seconds=60)
    for i in range(15):
        collector.mouse_movements.append({
            "timestamp": base_time + timedelta(milliseconds=i * 5000),  # every 5s
            "interval_ms": 5000,  # very regular
        })

    # Trigger the check manually
    collector._check_mouse_jiggler()

    if detected_patterns:
        p = detected_patterns[-1]
        print(f"  ✅ JIGGLER PATTERN FIRED")
        print(f"     Type       : {p['type']}")
        print(f"     Confidence : {p['confidence']:.2f}")
        print(f"     Details    : {p['details']}")
    else:
        print(f"  ❌ Pattern NOT fired")
        print(f"     Check _check_mouse_jiggler() in input_collector.py")
        print(f"     Condition: std_dev < 50 and 1000 < avg_interval < 10000")

        # Debug the actual values
        movements = list(collector.mouse_movements)[-10:]
        intervals = [m["interval_ms"] for m in movements]
        if intervals:
            avg = sum(intervals) / len(intervals)
            variance = sum((x - avg) ** 2 for x in intervals) / len(intervals)
            std_dev = variance ** 0.5
            print(f"\n     DEBUG values with your injected data:")
            print(f"       avg_interval : {avg:.1f} ms")
            print(f"       std_dev      : {std_dev:.1f} ms")
            print(f"       condition    : std_dev({std_dev:.1f}) < 50 = {std_dev < 50}")
            print(f"       condition    : 1000 < avg({avg:.1f}) < 10000 = {1000 < avg < 10000}")

except ImportError as e:
    print(f"  ⚠️  Could not import InputCollector: {e}")
    print(f"     Make sure you run from desktop-app/src/")


# ─────────────────────────────────────────────────────────────
# TEST 3: run_comprehensive_analysis (full pipeline)
# ─────────────────────────────────────────────────────────────

print("\n[TEST 3] Full pipeline via run_comprehensive_analysis()")
print("-" * 60)

try:
    from detection.abnormality_detector import AbnormalityDetector

    fired = []
    detector2 = AbnormalityDetector(
        on_abnormality_detected=lambda a: fired.append(a),
        confidence_threshold=0.7
    )

    # Inject jiggler movements into detector's internal buffer
    base_time = datetime.now() - timedelta(minutes=3)
    for i in range(30):
        detector2.mouse_movements.append({
            "timestamp": base_time + timedelta(seconds=i * 10),
            "distance": 3,
            "interval_ms": 10000,
        })

    # Simulate a normal keystroke pattern summary
    fake_pattern = {
        "status": "ok",
        "wpm": 45,
        "variance": 0.4,
        "keystrokes_per_minute": 40,
    }
    fake_activity = {
        "total_keystrokes": 800,
        "total_pastes": 2,
        "total_large_pastes": 0,
        "idle_seconds": 30,
        "total_mouse_movements": 30,
    }

    results = detector2.run_comprehensive_analysis(
        keystroke_pattern=fake_pattern,
        activity_summary=fake_activity,
        is_work_time=True
    )

    if results:
        print(f"  ✅ {len(results)} abnormality(ies) detected in full pipeline:")
        for r in results:
            print(f"     • {r.abnormality_type} (confidence: {r.confidence_score:.2f})")
    else:
        print(f"  ❌ No abnormalities detected in full pipeline")
        print(f"     Check run_comprehensive_analysis() calls detect_mouse_jiggler()")

except ImportError as e:
    print(f"  ⚠️  Could not import: {e}")
except AttributeError as e:
    print(f"  ⚠️  Method missing: {e}")


# ─────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("HOW TO READ RESULTS")
print("=" * 60)
print("""
  ✅ All 3 pass  → Detection is working end-to-end
  ✅ Test 2 only → Real-time layer works, 30s analysis broken
                   (fix: update detect_mouse_jiggler to use interval_ms)
  ❌ All fail    → ImportError — wrong working directory

KNOWN ISSUE TO WATCH FOR:
  Test 1 may fail because detect_mouse_jiggler() checks
  m.get('distance', 0) but InputCollector never sets 'distance'.
  If Test 1 fails but Test 2 passes, that confirms the bug.
""")