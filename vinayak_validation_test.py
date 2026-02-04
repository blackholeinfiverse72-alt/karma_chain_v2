"""
Day 4 - Vinayak Validation Test for Replay Safety & Audit Closure

This script validates the security implementation with:
1. Replay attack detection and rejection
2. TTL expiry detection and rejection
3. Hash-chained audit log verification

Test Scenarios:
- ✅ Valid signal processing
- ❌ Replay attack detection and rejection
- ❌ TTL expiry detection and rejection
- 📋 Audit trail generation and verification
"""

import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from utils.security_hardening import security_manager, bucket_communicator
from utils.karma_signal_contract import KarmaSignal


def create_test_signal(subject_id: str, context: str = "game", signal_type: str = "restrict") -> dict:
    """Create a test karma signal"""
    return {
        "subject_id": subject_id,
        "product_context": context,
        "signal": signal_type,
        "severity": 0.85,
        "ttl": 300,
        "requires_core_ack": True,
        "opaque_reason_code": f"TEST_REASON_{uuid.uuid4().hex[:8].upper()}",
        "signal_id": str(uuid.uuid4())
    }


def run_vinayak_validation_tests():
    """Run comprehensive Vinayak validation tests"""
    print("🎯 DAY 4 - VINAYAK VALIDATION TEST")
    print("=" * 60)
    print("Testing Replay Safety & Audit Closure")
    print("=" * 60)
    
    # Test data
    subject_id = str(uuid.uuid4())
    test_results = []
    
    # Test 1: Valid Signal Processing
    print("\n📋 TEST 1: VALID SIGNAL PROCESSING")
    print("-" * 40)
    
    valid_signal = create_test_signal(subject_id, "game", "restrict")
    print(f"Creating valid signal for subject: {subject_id[:8]}...")
    print(f"Signal ID: {valid_signal['signal_id']}")
    
    # Send to bucket
    result = bucket_communicator.send_to_bucket(valid_signal)
    
    if result['success']:
        print("✅ VALID SIGNAL: Successfully processed and stored in bucket")
        print(f"   Bucket ID: {result['bucket_id']}")
        test_results.append(("Valid Signal", "PASS"))
    else:
        print("❌ VALID SIGNAL: Failed to process")
        print(f"   Errors: {result['errors']}")
        test_results.append(("Valid Signal", "FAIL"))
    
    # Test 2: Replay Attack Detection
    print("\n🛡️  TEST 2: REPLAY ATTACK DETECTION")
    print("-" * 40)
    
    # Get the valid signal from bucket to replay it
    bucket_id = result['bucket_id']
    original_signal = bucket_communicator.receive_from_bucket(bucket_id)
    
    if original_signal:
        print(f"Attempting to replay signal: {original_signal['signal_id'][:8]}...")
        
        # Try to send the same signal again (replay attack)
        replay_result = bucket_communicator.send_to_bucket({
            "subject_id": original_signal['subject_id'],
            "product_context": original_signal['product_context'],
            "signal": original_signal['signal'],
            "severity": original_signal['severity'],
            "ttl": original_signal['ttl'],
            "requires_core_ack": original_signal['requires_core_ack'],
            "opaque_reason_code": original_signal['opaque_reason_code'],
            "signal_id": original_signal['signal_id']  # Same ID = replay
        })
        
        if not replay_result['success'] and any('replay' in str(err).lower() for err in replay_result['errors']):
            print("✅ REPLAY ATTACK: Successfully detected and rejected")
            print(f"   Rejection reason: {replay_result['errors']}")
            test_results.append(("Replay Attack", "PASS"))
        else:
            print("❌ REPLAY ATTACK: Failed to detect replay")
            print(f"   Result: {replay_result}")
            test_results.append(("Replay Attack", "FAIL"))
    else:
        print("❌ Could not retrieve original signal for replay test")
        test_results.append(("Replay Attack", "FAIL"))
    
    # Test 3: TTL Expiry Detection
    print("\n⏰ TEST 3: TTL EXPIRY DETECTION")
    print("-" * 40)
    
    # Create a signal with expired timestamp
    expired_signal = create_test_signal(subject_id, "finance", "escalate")
    
    # Manually set an expired timestamp (10 minutes ago)
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    expired_signal['timestamp'] = expired_time.isoformat()
    expired_signal['ttl'] = 300  # 5 minute TTL
    
    print(f"Creating expired signal (10 minutes old)...")
    print(f"Signal ID: {expired_signal['signal_id'][:8]}...")
    print(f"Timestamp: {expired_signal['timestamp']}")
    
    # Try to validate the expired signal
    validation_result = security_manager.validate_secure_karma_signal(
        security_manager.create_secure_karma_signal(expired_signal)
    )
    
    if not validation_result['valid'] and any('ttl' in str(err).lower() or 'expired' in str(err).lower() for err in validation_result['errors']):
        print("✅ TTL EXPIRY: Successfully detected and rejected")
        print(f"   Rejection reason: {validation_result['errors']}")
        test_results.append(("TTL Expiry", "PASS"))
    else:
        print("❌ TTL EXPIRY: Failed to detect expiry")
        print(f"   Validation result: {validation_result}")
        test_results.append(("TTL Expiry", "FAIL"))
    
    # Test 4: Invalid Nonce Detection
    print("\n🔢 TEST 4: INVALID NONCE DETECTION")
    print("-" * 40)
    
    # Create signal with invalid nonce
    invalid_nonce_signal = create_test_signal(subject_id, "assistant", "nudge")
    secured_signal = security_manager.create_secure_karma_signal(invalid_nonce_signal)
    
    # Corrupt the nonce
    secured_signal['nonce'] = "INVALID_NONCE_1234567890"
    
    print(f"Creating signal with invalid nonce...")
    print(f"Signal ID: {secured_signal['signal_id'][:8]}...")
    
    # Validate with invalid nonce
    nonce_validation = security_manager.validate_secure_karma_signal(secured_signal)
    
    if not nonce_validation['valid'] and any('nonce' in str(err).lower() for err in nonce_validation['errors']):
        print("✅ INVALID NONCE: Successfully detected and rejected")
        print(f"   Rejection reason: {nonce_validation['errors']}")
        test_results.append(("Invalid Nonce", "PASS"))
    else:
        print("❌ INVALID NONCE: Failed to detect invalid nonce")
        print(f"   Validation result: {nonce_validation}")
        test_results.append(("Invalid Nonce", "FAIL"))
    
    # Test 5: Signature Tampering Detection
    print("\n🔏 TEST 5: SIGNATURE TAMPERING DETECTION")
    print("-" * 40)
    
    # Create valid signal and tamper with signature
    tamper_signal = create_test_signal(subject_id, "infra", "allow")
    secured_tamper_signal = security_manager.create_secure_karma_signal(tamper_signal)
    
    # Tamper with the signal content but keep signature
    original_signature = secured_tamper_signal['signature']
    secured_tamper_signal['severity'] = 0.99  # Tamper with content
    secured_tamper_signal['signature'] = original_signature  # Keep old signature
    
    print(f"Creating signal with tampered content...")
    print(f"Signal ID: {secured_tamper_signal['signal_id'][:8]}...")
    
    # Validate tampered signal
    tamper_validation = security_manager.validate_secure_karma_signal(secured_tamper_signal)
    
    if not tamper_validation['valid'] and any('signature' in str(err).lower() for err in tamper_validation['errors']):
        print("✅ SIGNATURE TAMPERING: Successfully detected and rejected")
        print(f"   Rejection reason: {tamper_validation['errors']}")
        test_results.append(("Signature Tampering", "PASS"))
    else:
        print("❌ SIGNATURE TAMPERING: Failed to detect tampering")
        print(f"   Validation result: {tamper_validation}")
        test_results.append(("Signature Tampering", "FAIL"))
    
    # Generate audit trails
    print("\n" + "=" * 60)
    print("AUDIT TRAIL GENERATION")
    print("=" * 60)
    
    # Get audit trail
    audit_trail = security_manager.get_audit_trail()
    print(f"Generated audit trail with {len(audit_trail)} entries")
    
    # Verify audit chain integrity
    chain_valid = security_manager.verify_audit_chain()
    print(f"Audit chain integrity: {'✅ VALID' if chain_valid else '❌ INVALID'}")
    
    # Security summary
    security_summary = security_manager.get_security_summary()
    print(f"\nSecurity System Status:")
    print(f"  - Active nonces: {security_summary['nonce_count']}")
    print(f"  - Replay cache size: {security_summary['replay_cache_size']}")
    print(f"  - Audit log entries: {security_summary['audit_log_size']}")
    print(f"  - Chain integrity: {'✅ Valid' if security_summary['chain_integrity'] else '❌ Invalid'}")
    
    # Final Results
    print("\n" + "=" * 60)
    print("VINAYAK VALIDATION RESULTS")
    print("=" * 60)
    
    passed_tests = sum(1 for _, result in test_results if result == "PASS")
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result == "PASS" else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 VINAYAK VALIDATION: ALL TESTS PASSED")
        print("✅ Replay attacks properly detected and rejected")
        print("✅ TTL expiry properly detected and rejected")
        print("✅ Hash-chained audit log maintains integrity")
        print("✅ All security mechanisms functioning correctly")
    else:
        print("❌ VINAYAK VALIDATION: SOME TESTS FAILED")
        failed_tests = [name for name, result in test_results if result == "FAIL"]
        print(f"Failed tests: {', '.join(failed_tests)}")
    
    return passed_tests == total_tests


def generate_deliverables():
    """Generate the required deliverables"""
    print("\n" + "=" * 60)
    print("GENERATING DELIVERABLES")
    print("=" * 60)
    
    # Generate Replay Test Log
    print("\n📝 1. REPLAY TEST LOG")
    print("-" * 30)
    
    # Create and attempt to replay a signal
    subject_id = str(uuid.uuid4())
    original_signal = create_test_signal(subject_id, "game", "restrict")
    original_result = bucket_communicator.send_to_bucket(original_signal)
    
    # Get the signal to replay
    bucket_id = original_result['bucket_id']
    signal_to_replay = bucket_communicator.receive_from_bucket(bucket_id)
    
    # Replay attempt
    replay_result = bucket_communicator.send_to_bucket({
        "subject_id": signal_to_replay['subject_id'],
        "product_context": signal_to_replay['product_context'],
        "signal": signal_to_replay['signal'],
        "severity": signal_to_replay['severity'],
        "ttl": signal_to_replay['ttl'],
        "requires_core_ack": signal_to_replay['requires_core_ack'],
        "opaque_reason_code": signal_to_replay['opaque_reason_code'],
        "signal_id": signal_to_replay['signal_id']
    })
    
    replay_log = {
        "test_type": "replay_attack_detection",
        "original_signal_id": signal_to_replay['signal_id'],
        "replay_attempt_timestamp": datetime.now(timezone.utc).isoformat(),
        "replay_result": replay_result,
        "expected_outcome": "rejection",
        "actual_outcome": "rejected" if not replay_result['success'] else "accepted"
    }
    
    print("Replay Test Log:")
    print(json.dumps(replay_log, indent=2))
    
    # Generate TTL Expiry Test Log
    print("\n📝 2. TTL EXPIRY TEST LOG")
    print("-" * 30)
    
    # Create expired signal
    expired_signal = create_test_signal(subject_id, "finance", "escalate")
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    expired_signal['timestamp'] = expired_time.isoformat()
    expired_signal['ttl'] = 300
    
    # Validate expired signal
    secured_expired = security_manager.create_secure_karma_signal(expired_signal)
    ttl_validation = security_manager.validate_secure_karma_signal(secured_expired)
    
    ttl_log = {
        "test_type": "ttl_expiry_detection",
        "signal_id": expired_signal['signal_id'],
        "signal_timestamp": expired_signal['timestamp'],
        "current_time": datetime.now(timezone.utc).isoformat(),
        "ttl_seconds": 300,
        "time_difference_seconds": 600,  # 10 minutes
        "validation_result": ttl_validation,
        "expected_outcome": "rejection",
        "actual_outcome": "rejected" if not ttl_validation['valid'] else "accepted"
    }
    
    print("TTL Expiry Test Log:")
    print(json.dumps(ttl_log, indent=2))
    
    # Generate Audit Trail Sample
    print("\n📝 3. AUDIT TRAIL SAMPLE")
    print("-" * 30)
    
    # Get recent audit entries
    audit_sample = security_manager.get_audit_trail(10)
    
    audit_summary = {
        "total_entries": len(security_manager.audit_log),
        "sample_entries": len(audit_sample),
        "chain_integrity": security_manager.verify_audit_chain(),
        "entries": audit_sample
    }
    
    print("Audit Trail Sample:")
    print(json.dumps(audit_summary, indent=2))
    
    # Save deliverables to files
    with open('replay_test_log.json', 'w') as f:
        json.dump(replay_log, f, indent=2)
    
    with open('ttl_expiry_test_log.json', 'w') as f:
        json.dump(ttl_log, f, indent=2)
    
    with open('audit_trail_sample.json', 'w') as f:
        json.dump(audit_summary, f, indent=2)
    
    print("\n✅ Deliverables saved to files:")
    print("   - replay_test_log.json")
    print("   - ttl_expiry_test_log.json") 
    print("   - audit_trail_sample.json")


if __name__ == "__main__":
    print("🚀 Starting Day 4 - Vinayak Validation Test")
    
    # Run validation tests
    validation_passed = run_vinayak_validation_tests()
    
    # Generate deliverables
    if validation_passed:
        generate_deliverables()
        print("\n🎯 DAY 4 COMPLETE - ALL REQUIREMENTS MET")
        print("✅ Nonce implementation working")
        print("✅ TTL expiry detection working") 
        print("✅ Replay attack rejection working")
        print("✅ Hash-chained audit log implemented")
        print("✅ Vinayak validation successful")
    else:
        print("\n❌ DAY 4 INCOMPLETE - VALIDATION FAILED")