"""
Debug script to fix Day 4 validation issues
"""

import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from utils.security_hardening import security_manager, bucket_communicator


def debug_issues():
    print("🔍 DEBUGGING DAY 4 ISSUES")
    print("=" * 40)
    
    # Test 1: Basic signal creation and storage
    print("\n1. Testing basic signal flow...")
    subject_id = str(uuid.uuid4())
    signal = {
        "subject_id": subject_id,
        "product_context": "game",
        "signal": "restrict",
        "severity": 0.8,
        "ttl": 300,
        "requires_core_ack": True,
        "opaque_reason_code": "DEBUG_TEST",
        "signal_id": str(uuid.uuid4())
    }
    
    print(f"Original signal: {signal['signal_id'][:8]}...")
    
    # Send to bucket
    result = bucket_communicator.send_to_bucket(signal)
    print(f"Send result: {result}")
    
    if not result['success']:
        print("❌ Failed to send to bucket")
        return
    
    # Check what's stored
    bucket_id = result['bucket_id']
    stored_signal = bucket_communicator.bucket_store.get(bucket_id)
    print(f"Stored signal keys: {list(stored_signal.keys()) if stored_signal else 'None'}")
    
    # Test 2: Check why retrieval fails
    print("\n2. Testing signal retrieval...")
    retrieved = bucket_communicator.receive_from_bucket(bucket_id)
    print(f"Retrieved signal: {retrieved is not None}")
    
    if not retrieved:
        # Check validation details
        validation_result = security_manager.validate_secure_karma_signal(stored_signal)
        print(f"Validation errors: {validation_result['errors']}")
        
        # Check individual validation components
        print("\n3. Checking individual validation components...")
        
        # Check nonce
        nonce_valid = security_manager.validate_nonce(stored_signal.get('nonce', ''))
        print(f"Nonce valid: {nonce_valid}")
        
        # Check TTL
        ttl_valid = security_manager.is_valid_ttl(stored_signal.get('timestamp', ''), stored_signal.get('ttl', 300))
        print(f"TTL valid: {ttl_valid}")
        print(f"Signal timestamp: {stored_signal.get('timestamp', 'missing')}")
        print(f"Current time: {datetime.now(timezone.utc).isoformat()}")
        
        # Check replay
        replay_detected = security_manager.detect_replay_attack(stored_signal)
        print(f"Replay detected: {replay_detected}")
        
        # Check signature
        signal_copy = stored_signal.copy()
        expected_sig = signal_copy.pop('signature', None)
        if expected_sig:
            sig_valid = security_manager.verify_signature(signal_copy, expected_sig)
            print(f"Signature valid: {sig_valid}")
    
    # Test 3: TTL expiry detection
    print("\n4. Testing TTL expiry detection...")
    expired_signal = signal.copy()
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    expired_signal['timestamp'] = expired_time.isoformat()
    expired_signal['ttl'] = 300
    
    print(f"Expired timestamp: {expired_signal['timestamp']}")
    print(f"Current time: {datetime.now(timezone.utc).isoformat()}")
    
    ttl_check = security_manager.is_valid_ttl(expired_signal['timestamp'], 300)
    print(f"TTL check result: {ttl_check}")
    
    # Test 4: Audit chain
    print("\n5. Testing audit chain...")
    audit_trail = security_manager.get_audit_trail()
    print(f"Audit trail length: {len(audit_trail)}")
    
    if audit_trail:
        chain_valid = security_manager.verify_audit_chain()
        print(f"Chain valid: {chain_valid}")
        
        if not chain_valid:
            print("First few audit entries:")
            for i, entry in enumerate(audit_trail[:3]):
                print(f"  {i}: {entry.get('event_type', 'unknown')} - {entry.get('event_id', 'no-id')}")


if __name__ == "__main__":
    debug_issues()