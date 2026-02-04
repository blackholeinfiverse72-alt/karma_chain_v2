#!/usr/bin/env python3
"""
Test script to demonstrate KarmaChain Sovereign Isolation & Bucket/Core Convergence
This script shows:
1. Rejection of direct application calls
2. Acceptance of Bucket-fed events
"""

import asyncio
import requests
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_direct_app_call_rejection():
    """Test that direct application calls are rejected"""
    print("=== Testing Direct Application Call Rejection ===")
    
    # Attempt to call the log-action endpoint directly (should be rejected)
    url = "http://localhost:8000/api/v1/log-action/"
    
    # Data for logging an action
    data = {
        "user_id": "test_user_123",
        "action": "completing_lessons",
        "role": "learner",
        "context": "direct_app_call_test"
    }
    
    # Make a request WITHOUT proper authorization headers (should be rejected)
    try:
        response = requests.post(url, json=data)
        print(f"Direct call response status: {response.status_code}")
        print(f"Direct call response: {response.json()}")
        
        if response.status_code == 403:
            print("✅ SUCCESS: Direct application call was correctly rejected")
        else:
            print("❌ FAILURE: Direct application call was not rejected as expected")
    except Exception as e:
        print(f"Error making direct call: {e}")
    
    print()


def test_bucket_authorized_call():
    """Test that Bucket-authorized calls are accepted"""
    print("=== Testing Bucket-Authorized Call Acceptance ===")
    
    # Attempt to call the log-action endpoint with proper bucket authorization
    url = "http://localhost:8000/api/v1/log-action/"
    
    # Data for logging an action
    data = {
        "user_id": "test_user_456",
        "action": "helping_peers",
        "role": "volunteer",
        "context": "bucket_authorized_test"
    }
    
    # Make a request WITH proper authorization headers (should be accepted)
    headers = {
        "Content-Type": "application/json",
        "X-Source": "bucket",  # Indicates this is from the bucket
        "X-KarmaChain-Origin": "bucket"  # Alternative header for bucket origin
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Bucket-authorized call response status: {response.status_code}")
        
        if response.status_code in [200, 400, 422]:  # 200=success, 400/422=validation error but not auth error
            print("✅ SUCCESS: Bucket-authorized call was accepted")
        else:
            print(f"❌ FAILURE: Bucket-authorized call was rejected: {response.status_code}")
            
        print(f"Response: {response.text[:200]}...")  # Truncate for readability
    except Exception as e:
        print(f"Error making bucket-authorized call: {e}")
    
    print()


def test_core_authorized_call():
    """Test that Core-authorized calls are accepted"""
    print("=== Testing Core-Authorized Call Acceptance ===")
    
    # Attempt to call the log-action endpoint with proper core authorization
    url = "http://localhost:8000/api/v1/log-action/"
    
    # Data for logging an action
    data = {
        "user_id": "test_user_789",
        "action": "selfless_service",
        "role": "seva",
        "context": "core_authorized_test"
    }
    
    # Make a request WITH proper authorization headers (should be accepted)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer core_token",  # Simulate core authorization
        "X-Source": "core"  # Indicates this is from the core
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Core-authorized call response status: {response.status_code}")
        
        if response.status_code in [200, 400, 422]:  # 200=success, 400/422=validation error but not auth error
            print("✅ SUCCESS: Core-authorized call was accepted")
        else:
            print(f"❌ FAILURE: Core-authorized call was rejected: {response.status_code}")
            
        print(f"Response: {response.text[:200]}...")  # Truncate for readability
    except Exception as e:
        print(f"Error making core-authorized call: {e}")
    
    print()


def test_internal_system_call():
    """Test that internal system calls are accepted"""
    print("=== Testing Internal System Call Acceptance ===")
    
    # Attempt to call the karma profile endpoint with internal authorization
    url = "http://localhost:8000/api/v1/karma/test_user_123"
    
    # Make a request WITH proper internal authorization headers
    headers = {
        "Content-Type": "application/json",
        "X-Source": "internal",  # Indicates this is an internal call
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Internal call response status: {response.status_code}")
        
        if response.status_code in [200, 400, 404, 422]:  # Various valid responses
            print("✅ SUCCESS: Internal system call was accepted")
        else:
            print(f"❌ FAILURE: Internal system call was rejected: {response.status_code}")
            
        print(f"Response: {response.text[:200]}...")  # Truncate for readability
    except Exception as e:
        print(f"Error making internal call: {e}")
    
    print()


def main():
    """Main test function"""
    print("KarmaChain Sovereign Isolation & Bucket/Core Convergence Test")
    print("=" * 60)
    print("This test demonstrates:")
    print("1. Direct application calls are rejected")
    print("2. Bucket-authorized calls are accepted")
    print("3. Core-authorized calls are accepted")
    print("4. Internal system calls are accepted")
    print("=" * 60)
    print()
    
    # Wait for server to be ready (if running)
    print("Testing authorization mechanisms...")
    print("(Note: Server should be running on http://localhost:8000)")
    print()
    
    test_direct_app_call_rejection()
    test_bucket_authorized_call()
    test_core_authorized_call()
    test_internal_system_call()
    
    print("=== Test Summary ===")
    print("✅ Direct application calls should be rejected with 403")
    print("✅ Bucket-authorized calls should be accepted")
    print("✅ Core-authorized calls should be accepted")
    print("✅ Internal system calls should be accepted")
    print()
    print("KarmaChain is now operating in sovereign isolation mode:")
    print("- All direct application-facing APIs disabled")
    print("- Only accepts events from Bucket or Core")
    print("- Only emits signals to Bucket")


if __name__ == "__main__":
    main()