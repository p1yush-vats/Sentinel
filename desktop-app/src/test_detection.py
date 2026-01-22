"""
Test Abnormality Detection

Run this to verify detection is working without starting full app
"""
import time
from datetime import datetime
from detection.input_collector import InputCollector
from detection.abnormality_detector import AbnormalityDetector, Abnormality


def test_mechanical_typing():
    """Test mechanical typing detection"""
    print("\n" + "="*60)
    print("TEST 1: Mechanical Typing Detection")
    print("="*60)
    
    def on_abnormality(abn: Abnormality):
        print(f"\n🚨 ABNORMALITY DETECTED!")
        print(f"   Type: {abn.abnormality_type}")
        print(f"   Confidence: {abn.confidence_score:.2%}")
        print(f"   Details: {abn.metadata.get('description')}")
    
    detector = AbnormalityDetector(
        on_abnormality_detected=on_abnormality,
        confidence_threshold=0.7
    )
    
    # Simulate mechanical typing pattern
    print("\n📝 Testing with mechanical typing pattern...")
    pattern = {
        "avg_interval_ms": 100,
        "consistency_score": 0.05,  # Very consistent = mechanical
        "std_deviation": 5,
        "sample_size": 100
    }
    
    result = detector.analyze_keystroke_pattern(pattern)
    
    if result:
        print("✅ Mechanical typing DETECTED correctly")
    else:
        print("❌ Mechanical typing NOT detected (should have been)")
    
    # Test normal typing (should NOT detect)
    print("\n📝 Testing with normal typing pattern...")
    normal_pattern = {
        "avg_interval_ms": 120,
        "consistency_score": 0.35,  # Normal variance
        "std_deviation": 42,
        "sample_size": 100
    }
    
    result = detector.analyze_keystroke_pattern(normal_pattern)
    
    if result:
        print("❌ Normal typing INCORRECTLY flagged as abnormal")
    else:
        print("✅ Normal typing correctly passed")


def test_paste_detection():
    """Test paste behavior detection"""
    print("\n" + "="*60)
    print("TEST 2: Paste Behavior Detection")
    print("="*60)
    
    def on_abnormality(abn: Abnormality):
        print(f"\n🚨 ABNORMALITY DETECTED!")
        print(f"   Type: {abn.abnormality_type}")
        print(f"   Confidence: {abn.confidence_score:.2%}")
        print(f"   Details: {abn.metadata.get('description')}")
    
    detector = AbnormalityDetector(
        on_abnormality_detected=on_abnormality,
        confidence_threshold=0.7
    )
    
    # Test excessive paste ratio
    print("\n📋 Testing paste-heavy work (50 pastes, 50 keystrokes)...")
    result = detector.analyze_paste_behavior(
        total_pastes=50,
        total_keystrokes=50,
        session_duration_seconds=300  # 5 minutes
    )
    
    if result:
        print("✅ Paste-heavy work DETECTED correctly")
    else:
        print("❌ Paste-heavy work NOT detected (should have been)")
    
    # Test normal paste ratio
    print("\n📋 Testing normal paste ratio (5 pastes, 95 keystrokes)...")
    result = detector.analyze_paste_behavior(
        total_pastes=5,
        total_keystrokes=95,
        session_duration_seconds=300
    )
    
    if result:
        print("❌ Normal paste ratio INCORRECTLY flagged")
    else:
        print("✅ Normal paste ratio correctly passed")


def test_rapid_paste():
    """Test rapid paste detection"""
    print("\n" + "="*60)
    print("TEST 3: Rapid Paste Detection")
    print("="*60)
    
    def on_abnormality(abn: Abnormality):
        print(f"\n🚨 ABNORMALITY DETECTED!")
        print(f"   Type: {abn.abnormality_type}")
        print(f"   Confidence: {abn.confidence_score:.2%}")
        print(f"   Details: {abn.metadata.get('description')}")
    
    detector = AbnormalityDetector(
        on_abnormality_detected=on_abnormality,
        confidence_threshold=0.7
    )
    
    print("\n⚡ Simulating 5 rapid pastes in 20 seconds...")
    
    # Simulate rapid pasting
    now = datetime.now()
    for i in range(5):
        from datetime import timedelta
        paste_time = now + timedelta(seconds=i * 4)  # Every 4 seconds
        detector.track_paste_event(paste_time)
    
    print("✅ Rapid paste test completed")


def test_idle_detection():
    """Test idle period detection"""
    print("\n" + "="*60)
    print("TEST 4: Idle Period Detection")
    print("="*60)
    
    def on_abnormality(abn: Abnormality):
        print(f"\n🚨 ABNORMALITY DETECTED!")
        print(f"   Type: {abn.abnormality_type}")
        print(f"   Confidence: {abn.confidence_score:.2%}")
        print(f"   Details: {abn.metadata.get('description')}")
    
    detector = AbnormalityDetector(
        on_abnormality_detected=on_abnormality,
        confidence_threshold=0.7
    )
    
    # Test long idle during work
    print("\n😴 Testing 10 minute idle during work time...")
    result = detector.analyze_idle_period(
        idle_seconds=600,  # 10 minutes
        is_work_time=True
    )
    
    if result:
        print("✅ Long idle DETECTED correctly")
    else:
        print("❌ Long idle NOT detected (should have been)")
    
    # Test idle during break (should not flag)
    print("\n😴 Testing 10 minute idle during break...")
    result = detector.analyze_idle_period(
        idle_seconds=600,
        is_work_time=False
    )
    
    if result:
        print("❌ Idle during break INCORRECTLY flagged")
    else:
        print("✅ Idle during break correctly ignored")


def test_comprehensive_analysis():
    """Test full analysis pipeline"""
    print("\n" + "="*60)
    print("TEST 5: Comprehensive Analysis")
    print("="*60)
    
    detected_count = 0
    
    def on_abnormality(abn: Abnormality):
        nonlocal detected_count
        detected_count += 1
        print(f"\n🚨 Abnormality #{detected_count}")
        print(f"   Type: {abn.abnormality_type}")
        print(f"   Confidence: {abn.confidence_score:.2%}")
    
    detector = AbnormalityDetector(
        on_abnormality_detected=on_abnormality,
        confidence_threshold=0.7
    )
    
    # Simulate suspicious session
    print("\n🔍 Running comprehensive analysis on suspicious session...")
    
    keystroke_pattern = {
        "avg_interval_ms": 100,
        "consistency_score": 0.08,  # Mechanical
        "std_deviation": 8,
        "sample_size": 150
    }
    
    activity_summary = {
        "session_duration_seconds": 600,  # 10 minutes
        "total_keystrokes": 100,
        "total_pastes": 60,  # Excessive
        "idle_seconds": 400,  # 6.7 minutes idle
    }
    
    abnormalities = detector.run_comprehensive_analysis(
        keystroke_pattern=keystroke_pattern,
        activity_summary=activity_summary,
        is_work_time=True
    )
    
    print(f"\n📊 Analysis Complete:")
    print(f"   Total abnormalities: {len(abnormalities)}")
    print(f"   Risk score: {detector.get_risk_score():.1f}/100")
    
    if len(abnormalities) >= 2:  # Should detect at least mechanical + paste
        print("✅ Comprehensive analysis working correctly")
    else:
        print("❌ Some detections missing")


def test_input_collector():
    """Test input collector (LIVE TEST - requires user input)"""
    print("\n" + "="*60)
    print("TEST 6: Live Input Collection (10 seconds)")
    print("="*60)
    print("\n⚠️  This test requires keyboard/mouse input!")
    print("    Please type and move your mouse for 10 seconds...")
    print("    Starting in 3 seconds...\n")
    
    time.sleep(3)
    
    pattern_count = 0
    
    def on_pattern(pattern):
        nonlocal pattern_count
        pattern_count += 1
        print(f"🔍 Pattern #{pattern_count}: {pattern['type']}")
    
    collector = InputCollector(on_pattern_detected=on_pattern)
    collector.start_collecting()
    
    print("▶️  Input collection started - TYPE AND MOVE MOUSE NOW!\n")
    
    for i in range(10, 0, -1):
        print(f"   {i} seconds remaining...")
        time.sleep(1)
    
    collector.stop_collecting()
    
    # Get results
    summary = collector.get_activity_summary()
    pattern = collector.get_keystroke_pattern()
    
    print(f"\n📊 Collection Results:")
    print(f"   Total keystrokes: {summary.get('total_keystrokes', 0)}")
    print(f"   Total mouse movements: {summary.get('total_mouse_movements', 0)}")
    print(f"   Total pastes: {summary.get('total_pastes', 0)}")
    print(f"   Keystroke rate: {summary.get('keystroke_rate_per_minute', 0):.1f}/min")
    
    if pattern.get('status') != 'insufficient_data':
        print(f"   Avg keystroke interval: {pattern.get('avg_interval_ms', 0)}ms")
        print(f"   Consistency score: {pattern.get('consistency_score', 0):.3f}")
        print(f"   Mechanical suspected: {pattern.get('mechanical_suspected', False)}")
    else:
        print(f"   Pattern analysis: {pattern.get('status')}")
    
    if summary.get('total_keystrokes', 0) > 0:
        print("\n✅ Input collector working correctly")
    else:
        print("\n⚠️  No input detected - did you type anything?")


def run_all_tests():
    """Run all detection tests"""
    print("\n")
    print("🧪 SENTINEL Detection System Test Suite")
    print("=" * 60)
    
    try:
        # Unit tests (don't require user input)
        test_mechanical_typing()
        test_paste_detection()
        test_rapid_paste()
        test_idle_detection()
        test_comprehensive_analysis()
        
        # Live test (requires user input)
        response = input("\n\nRun live input collection test? (requires typing) [y/N]: ")
        if response.lower() == 'y':
            test_input_collector()
        else:
            print("⏭️  Skipping live input test")
        
        print("\n" + "="*60)
        print("✅ All automated tests completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()