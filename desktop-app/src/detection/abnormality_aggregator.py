"""
Abnormality Aggregator - DEBUG VERSION WITH DETAILED ERROR LOGGING

This version will tell us EXACTLY why syncs are failing
"""
from datetime import datetime
from typing import Dict, Optional
import uuid
import asyncio
import threading
import time
import traceback


class AbnormalityAggregator:
    """Aggregator with detailed debug logging"""
    
    def __init__(self, session_id: str, local_db, sync_client):
        self.session_id = session_id
        self.local_db = local_db
        self.sync_client = sync_client
        
        self.session_abnormalities: Dict[str, Dict] = {}
        self.backend_session_id = self._get_backend_session_id()
        self.sync_queue = []
        self.background_sync_running = False
        self.background_sync_thread = None
        
        self._load_existing()
        self._start_background_sync()
    
    def _get_backend_session_id(self) -> Optional[str]:
        """Get backend session ID from local DB"""
        try:
            session = self.local_db.get_session(self.session_id)
            if session:
                backend_id = session.get('backend_session_id')
                if backend_id:
                    print(f"  ✓ Backend session ID: {backend_id}")
                    return backend_id
                else:
                    print(f"  ⚠️ No backend session ID (working offline)")
                    return None
            return None
        except Exception as e:
            print(f"  ⚠️ Could not get backend session ID: {e}")
            return None
    
    def _load_existing(self):
        """Load existing abnormalities from DB"""
        try:
            existing = self.local_db.get_session_abnormalities(self.session_id)
            for abn in existing:
                abn_type = abn['abnormality_type']
                metadata = abn.get('metadata', {})
                
                self.session_abnormalities[abn_type] = {
                    'id': abn['id'],
                    'detections': metadata.get('timestamps', []),
                    'confidences': metadata.get('confidences', []),
                    'first_detected': datetime.fromisoformat(abn['detected_at']) if isinstance(abn['detected_at'], str) else abn['detected_at']
                }
            
            if existing:
                print(f"  📂 Loaded {len(existing)} existing abnormality type(s)")
        except Exception as e:
            print(f"  ⚠️ Error loading: {e}")
    
    def add_detection(self, abnormality_type: str, confidence: float, timestamp: datetime, description: str):
        """Add a detection"""
        
        # Initialize if first detection
        if abnormality_type not in self.session_abnormalities:
            self.session_abnormalities[abnormality_type] = {
                'id': str(uuid.uuid4()),
                'detections': [],
                'confidences': [],
                'first_detected': timestamp
            }
        
        # Add detection
        abn = self.session_abnormalities[abnormality_type]
        abn['detections'].append(timestamp.isoformat())
        abn['confidences'].append(confidence)
        
        # Calculate stats
        occurrences = len(abn['detections'])
        avg_conf = sum(abn['confidences']) / occurrences
        max_conf = max(abn['confidences'])
        
        # Calculate severity
        if occurrences >= 10 or max_conf >= 0.95:
            severity = "CRITICAL"
        elif occurrences >= 5 or max_conf >= 0.85:
            severity = "HIGH"
        elif occurrences >= 2 or max_conf >= 0.75:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        
        print(f"  📊 {abnormality_type}: {occurrences}x, {severity}")
        
        # Build metadata
        metadata = {
            'description': f"{abnormality_type.replace('_', ' ').title()} detected {occurrences} times",
            'occurrences': occurrences,
            'avg_confidence': float(avg_conf),
            'max_confidence': float(max_conf),
            'severity': severity,
            'first_detected_at': abn['first_detected'].isoformat(),
            'last_detected_at': timestamp.isoformat(),
            'timestamps': abn['detections'],
            'confidences': abn['confidences']
        }
        
        # Save to local DB
        try:
            existing = self.local_db.get_session_abnormalities(self.session_id)
            exists = any(e['abnormality_type'] == abnormality_type for e in existing)
            
            if exists:
                self.local_db.update_abnormality(
                    abnormality_id=abn['id'],
                    confidence_score=max_conf,
                    metadata=metadata
                )
            else:
                self.local_db.create_abnormality(
                    abnormality_id=abn['id'],
                    session_id=self.session_id,
                    abnormality_type=abnormality_type,
                    confidence_score=max_conf,
                    detected_at=abn['first_detected'],
                    metadata=metadata
                )
            print(f"     💾 Saved locally")
        except Exception as e:
            print(f"     ❌ Local save failed: {e}")
            traceback.print_exc()
            return
        
        # Try sync to backend WITH DETAILED LOGGING
        sync_success = self._try_sync_to_backend_debug(
            abnormality_id=abn['id'],
            abnormality_type=abnormality_type,
            metadata=metadata,
            confidence=max_conf,
            timestamp=timestamp
        )
        
        if not sync_success and self.backend_session_id:
            self.sync_queue.append({
                'abnormality_id': abn['id'],
                'abnormality_type': abnormality_type,
                'metadata': metadata,
                'confidence': max_conf,
                'timestamp': timestamp
            })
            print(f"     🔄 Queued for retry ({len(self.sync_queue)} pending)")
    
    def _try_sync_to_backend_debug(self, abnormality_id: str, abnormality_type: str, metadata: Dict, confidence: float, timestamp: datetime) -> bool:
        """
        🔍 DEBUG VERSION - Try to sync with detailed error reporting
        """
        print(f"\n     🔍 DEBUG: Attempting sync...")
        print(f"        Backend Session ID: {self.backend_session_id}")
        print(f"        Abnormality Type: {abnormality_type}")
        print(f"        Confidence: {confidence}")
        
        # Check if backend session ID exists
        if not self.backend_session_id:
            print(f"        ❌ FAIL: No backend session ID")
            return False
        
        # Check sync_client
        if not self.sync_client:
            print(f"        ❌ FAIL: No sync client")
            return False
        
        # Check if report_abnormality method exists
        if not hasattr(self.sync_client, 'report_abnormality'):
            print(f"        ❌ FAIL: sync_client has no report_abnormality method")
            print(f"        Available methods: {dir(self.sync_client)}")
            return False
        
        try:
            # Check if we're in an async context
            try:
                asyncio.get_running_loop()
                print(f"        ⚠️ FAIL: Already in async loop")
                return False
            except RuntimeError:
                pass
            
            print(f"        🔄 Creating event loop...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                print(f"        🔄 Calling sync_client.report_abnormality...")
                print(f"           session_id={self.backend_session_id}")
                print(f"           abnormality_type={abnormality_type}")
                print(f"           confidence_score={confidence}")
                
                success = loop.run_until_complete(
                    self.sync_client.report_abnormality(
                        session_id=self.backend_session_id,
                        abnormality_type=abnormality_type,
                        confidence_score=confidence,
                        metadata=metadata
                    )
                )
                
                print(f"        📊 Result: {success} (type: {type(success)})")
                
                if success:
                    print(f"        ✅ SUCCESS: Synced to backend")
                    self.local_db.mark_abnormality_synced(abnormality_id)
                    return True
                else:
                    print(f"        ❌ FAIL: report_abnormality returned False")
                    return False
                    
            except Exception as e:
                print(f"        ❌ EXCEPTION in sync call: {e}")
                print(f"        Exception type: {type(e)}")
                traceback.print_exc()
                return False
            finally:
                loop.close()
                
        except Exception as e:
            print(f"        ❌ OUTER EXCEPTION: {e}")
            traceback.print_exc()
            return False
    
    def _start_background_sync(self):
        """Start background sync thread"""
        self.background_sync_running = True
        self.background_sync_thread = threading.Thread(
            target=self._background_sync_loop,
            daemon=True
        )
        self.background_sync_thread.start()
        print(f"  ✓ Background sync started (every 60s)")
    
    def _background_sync_loop(self):
        """Background sync loop"""
        while self.background_sync_running:
            time.sleep(60)
            
            if not self.sync_queue or not self.backend_session_id:
                continue
            
            print(f"\n🔄 Background sync: {len(self.sync_queue)} pending items")
            
            successful = []
            for item in self.sync_queue[:5]:  # Only try first 5 to avoid spam
                success = self._try_sync_to_backend_debug(
                    abnormality_id=item['abnormality_id'],
                    abnormality_type=item['abnormality_type'],
                    metadata=item['metadata'],
                    confidence=item['confidence'],
                    timestamp=item['timestamp']
                )
                
                if success:
                    successful.append(item)
            
            for item in successful:
                self.sync_queue.remove(item)
            
            if successful:
                print(f"  ✅ Synced {len(successful)} items, {len(self.sync_queue)} remaining")
    
    def stop_background_sync(self):
        """Stop background sync thread"""
        self.background_sync_running = False
    
    def get_summary(self) -> Dict:
        """Get session summary"""
        summary = {}
        for abn_type, abn in self.session_abnormalities.items():
            occurrences = len(abn['detections'])
            avg_conf = sum(abn['confidences']) / occurrences
            max_conf = max(abn['confidences'])
            
            if occurrences >= 10 or max_conf >= 0.95:
                severity = "CRITICAL"
            elif occurrences >= 5 or max_conf >= 0.85:
                severity = "HIGH"
            elif occurrences >= 2:
                severity = "MEDIUM"
            else:
                severity = "LOW"
            
            summary[abn_type] = {
                'occurrences': occurrences,
                'avg_confidence': avg_conf,
                'max_confidence': max_conf,
                'severity': severity
            }
        return summary
    
    def flush(self):
        """Final flush"""
        total_detections = sum(len(a['detections']) for a in self.session_abnormalities.values())
        print(f"\n📊 Finalizing: {len(self.session_abnormalities)} types, {total_detections} total detections")
        
        if self.sync_queue:
            print(f"⚠️ {len(self.sync_queue)} items still pending in queue")
        
        self.stop_background_sync()
        print(f"  ✅ All data saved locally")