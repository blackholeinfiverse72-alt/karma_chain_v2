"""
Targeted replay attack test
"""

import uuid
from datetime import datetime, timezone
from utils.security_hardening import security_manager, bucket_communicator


def test_replay_attack():
    print("🎯 TARGETED REPLAY ATTACK TEST")
    print("=" * 40)
    
    # Create original signal
    subject_id = str(uuid.uuid4())
    original_signal = {
        "subject_id": subject_id,
        "product_context": "game",
        "signal": "restrict",
        "severity": 0.8,
        "ttl": 300,
        "requires_core_ack": True,
        "opaque_reason_code": "REPLAY_TEST",
        "signal_id": str(uuid.uuid4())
    }
    
    print(f"Original signal ID: {original_signal['signal_id'][:8]}...")
    
    # Send original signal
    original_result = bucket_communicator.send_to_bucket(original_signal)
    print(f"Original send result: {original_result}")
    
    if not original_result['success']:
        print("❌ Failed to send original signal")
        return
    
    # DON'T clear replay cache - let it work naturally
    print("Keeping replay cache intact for proper detection")
    
    # Wait a moment to ensure different timestamps
    import time
    time.sleep(1)
    
    # Create exact copy for replay (same signal_id)
    replay_signal = original_signal.copy()
    
    print(f"Attempting replay with same signal_id: {replay_signal['signal_id'][:8]}...")
    
    # Try to send replay signal
    replay_result = bucket_communicator.send_to_bucket(replay_signal)
    print(f"Replay send result: {replay_result}")
    
    # Check if replay was detected
    if not replay_result['success']:
        if any('replay' in str(err).lower() for err in replay_result.get('errors', [])):
            print("✅ REPLAY ATTACK SUCCESSFULLY DETECTED AND REJECTED")
            return True
        else:
            print("❌ REPLAY ATTEMPT FAILED BUT NOT DUE TO REPLAY DETECTION")
            print(f"Errors: {replay_result.get('errors', [])}")
    else:
        print("❌ REPLAY ATTACK WAS NOT DETECTED")
        print("This indicates the replay detection is not working properly")
        return False


def test_ttl_expiry():
    print("\n⏰ TARGETED TTL EXPIRY TEST")
    print("=" * 40)
    
    from datetime import timedelta
    
    # Create expired signal
    subject_id = str(uuid.uuid4())
    expired_signal = {
        "subject_id": subject_id,
        "product_context": "finance",
        "signal": "escalate",
        "severity": 0.9,
        "ttl": 300,
        "requires_core_ack": True,
        "opaque_reason_code": "TTL_TEST",
        "signal_id": str(uuid.uuid4())
    }
    
    # Set timestamp to 10 minutes ago
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    expired_signal['timestamp'] = expired_time.isoformat()
    
    print(f"Expired signal timestamp: {expired_signal['timestamp']}")
    print(f"Current time: {datetime.now(timezone.utc).isoformat()}")
    
    # Create secured version
    secured_expired = security_manager.create_secure_karma_signal(expired_signal)
    print(f"Created secured expired signal")
    
    # Validate
    validation_result = security_manager.validate_secure_karma_signal(secured_expired)
    print(f"Validation result: {validation_result}")
    
    # Check if TTL expiry was detected
    if not validation_result['valid']:
        if any('ttl' in str(err).lower() or 'expired' in str(err).lower() for err in validation_result['errors']):
            print("✅ TTL EXPIRY SUCCESSFULLY DETECTED AND REJECTED")
            return True
        else:
            print("❌ TTL VALIDATION FAILED BUT NOT DUE TO EXPIRY")
            print(f"Errors: {validation_result['errors']}")
    else:
        print("❌ TTL EXPIRY WAS NOT DETECTED")
        print("This indicates the TTL validation is not working properly")
        return False


if __name__ == "__main__":
    replay_success = test_replay_attack()
    ttl_success = test_ttl_expiry()
    
    print(f"\n🎯 FINAL RESULTS:")
    print(f"Replay Attack Detection: {'✅ PASS' if replay_success else '❌ FAIL'}")
    print(f"TTL Expiry Detection: {'✅ PASS' if ttl_success else '❌ FAIL'}")
    
    if replay_success and ttl_success:
        print("🎉 ALL TARGETED TESTS PASSED")
    else:
        print("❌ SOME TARGETED TESTS FAILED")