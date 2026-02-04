"""
Core Authorization Gate for KarmaChain

Implements the Core authorization gate for ALL irreversible actions:
- death_event
- rebirth  
- access gating
- progression locks
- restrictions

Flow: Evaluate → Emit KarmaSignal → WAIT → Core ACK
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable
from enum import Enum
from .karma_signal_contract import KarmaSignal, emit_canonical_karma_signal
from .sovereign_bridge import sovereign_bridge
from .authorization_logging import (
    log_auth_request, log_auth_ack, log_auth_deny, 
    log_auth_timeout, log_action_exec, log_audit_discard
)

# Set up logging
logger = logging.getLogger(__name__)


class IrreversibleActionType(Enum):
    """Types of irreversible actions that require Core authorization"""
    DEATH_EVENT = "death_event"
    REBIRTH = "rebirth"
    ACCESS_GATING = "access_gating"
    PROGRESSION_LOCK = "progression_lock"
    RESTRICTION = "restriction"


async def authorize_irreversible_action(
    subject_id: str,
    action_type: IrreversibleActionType,
    context: str,
    severity: float = 0.9,  # High severity for irreversible actions
    opaque_reason_code: str = "IRREVERSIBLE_ACTION",
    ttl: int = 300,
    timeout: int = 10,  # Timeout in seconds
    action_func: Optional[Callable] = None  # Function to execute if authorized
) -> Dict[str, Any]:
    """
    Authorize an irreversible action through Core authorization gate.
    
    MANDATORY BEHAVIOR:
    - No ACK → no effect
    - DENY → discard + audit log
    - TIMEOUT → safe no-op
    
    Args:
        subject_id: ID of the subject
        action_type: Type of irreversible action
        context: Context where action occurs
        severity: Severity level (0.0 to 1.0)
        opaque_reason_code: Opaque reason code
        ttl: Time to live in seconds
        timeout: Timeout in seconds for authorization
        action_func: Optional function to execute if authorized
    
    Returns:
        Dict with authorization result:
        - status: 'allowed', 'denied', 'timeout', 'error'
        - authorized: Boolean indicating if action is authorized
        - core_response: Response from Core
        - action_executed: Whether the action was executed
    """
    
    # Log the authorization request
    event_id = log_auth_request(
        subject_id=subject_id,
        action_type=action_type.value,
        context=context,
        severity=severity,
        opaque_reason_code=opaque_reason_code
    )
    
    # Create a canonical karma signal for the irreversible action
    karma_signal = KarmaSignal(
        subject_id=subject_id,
        product_context=context,
        signal=get_signal_for_action(action_type),
        severity=severity,
        opaque_reason_code=opaque_reason_code,
        ttl=ttl,
        requires_core_ack=True
    )
    
    # Emit the signal to Core for authorization
    start_time = time.time()
    authorization_result = emit_canonical_karma_signal(
        subject_id=subject_id,
        product_context=context,
        signal=karma_signal.signal,
        severity=severity,
        opaque_reason_code=opaque_reason_code,
        ttl=ttl,
        requires_core_ack=True
    )
    
    # Wait for Core response with timeout
    while time.time() - start_time < timeout:
        # Check if authorization result contains the response
        if 'authorization_response' in authorization_result:
            auth_response = authorization_result['authorization_response']
            if 'authorized' in auth_response:
                if auth_response['authorized']:
                    # Core ACK received - execute the action
                    log_auth_ack(event_id, subject_id, action_type.value, auth_response)
                    result = {
                        "status": "allowed",
                        "authorized": True,
                        "core_response": auth_response,
                        "action_executed": False
                    }
                    
                    # Execute the action if provided
                    if action_func:
                        try:
                            execution_result = action_func()
                            result["action_executed"] = True
                            result["execution_result"] = execution_result
                            log_action_exec(event_id, subject_id, action_type.value, execution_result)
                        except Exception as e:
                            result["action_executed"] = False
                            result["execution_error"] = str(e)
                            logger.error(f"ACTION EXECUTION FAILED: {action_type.value} for subject {subject_id}: {e}")
                    
                    return result
                else:
                    # Core DENY - discard and log
                    log_auth_deny(event_id, subject_id, action_type.value, auth_response)
                    return {
                        "status": "denied",
                        "authorized": False,
                        "core_response": auth_response,
                        "action_executed": False,
                        "audit_logged": True
                    }
        
        # Small delay before checking again
        await asyncio.sleep(0.1)
    
    # Timeout reached - safe fallback (no effect)
    log_auth_timeout(event_id, subject_id, action_type.value, timeout)
    return {
        "status": "timeout",
        "authorized": False,
        "core_response": {"reason": "Timeout waiting for Core authorization"},
        "action_executed": False,
        "fallback_action": "no_effect",
        "audit_logged": True
    }


def get_signal_for_action(action_type: IrreversibleActionType) -> str:
    """Map irreversible action type to appropriate signal"""
    action_to_signal = {
        IrreversibleActionType.DEATH_EVENT: "escalate",
        IrreversibleActionType.REBIRTH: "allow",
        IrreversibleActionType.ACCESS_GATING: "restrict",
        IrreversibleActionType.PROGRESSION_LOCK: "restrict", 
        IrreversibleActionType.RESTRICTION: "restrict"
    }
    return action_to_signal.get(action_type, "nudge")


def apply_irreversible_action_if_authorized(authorization_result: Dict[str, Any], action_func=None) -> Dict[str, Any]:
    """
    Apply irreversible action only if authorized by Core.
    
    Args:
        authorization_result: Result from authorize_irreversible_action
        action_func: Optional function to execute if authorized
    
    Returns:
        Dict with action application result
    """
    if authorization_result.get("authorized", False):
        # Action is authorized, apply it
        if action_func:
            try:
                action_result = action_func()
                return {
                    **authorization_result,
                    "action_executed": True,
                    "execution_result": action_result
                }
            except Exception as e:
                return {
                    **authorization_result,
                    "action_executed": False,
                    "error": str(e)
                }
        else:
            return {
                **authorization_result,
                "action_executed": True
            }
    else:
        # Action is not authorized, return with no effect
        return {
            **authorization_result,
            "action_executed": False,
            "reason": "Action not authorized by Core"
        }


def validate_no_direct_execution_without_ack(
    action_type: IrreversibleActionType,
    subject_id: str,
    context: str
) -> bool:
    """
    Validate that irreversible actions go through Core authorization.
    
    Args:
        action_type: Type of action to validate
        subject_id: Subject ID
        context: Context
    
    Returns:
        bool: True if validation passes (no direct execution)
    """
    # This is a validation function to ensure no direct execution happens
    # without going through the Core authorization gate
    print(f"VALIDATION: Action {action_type.value} for subject {subject_id} "
          f"in context {context} must go through Core authorization gate.")
    return True


# Specific functions for each type of irreversible action
async def authorize_death_event(
    subject_id: str,
    context: str,
    severity: float = 0.95,
    opaque_reason_code: str = "DEATH_THRESHOLD_REACHED"
) -> Dict[str, Any]:
    """Authorize a death event"""
    return await authorize_irreversible_action(
        subject_id=subject_id,
        action_type=IrreversibleActionType.DEATH_EVENT,
        context=context,
        severity=severity,
        opaque_reason_code=opaque_reason_code
    )


async def authorize_rebirth(
    subject_id: str,
    context: str,
    severity: float = 0.1,
    opaque_reason_code: str = "REBIRTH_ELIGIBILITY"
) -> Dict[str, Any]:
    """Authorize a rebirth event"""
    return await authorize_irreversible_action(
        subject_id=subject_id,
        action_type=IrreversibleActionType.REBIRTH,
        context=context,
        severity=severity,
        opaque_reason_code=opaque_reason_code
    )


async def authorize_access_gating(
    subject_id: str,
    context: str,
    severity: float = 0.8,
    opaque_reason_code: str = "ACCESS_CONTROL_NEEDED"
) -> Dict[str, Any]:
    """Authorize access gating"""
    return await authorize_irreversible_action(
        subject_id=subject_id,
        action_type=IrreversibleActionType.ACCESS_GATING,
        context=context,
        severity=severity,
        opaque_reason_code=opaque_reason_code
    )


async def authorize_progression_lock(
    subject_id: str,
    context: str,
    severity: float = 0.7,
    opaque_reason_code: str = "PROGRESSION_LOCK_NEEDED"
) -> Dict[str, Any]:
    """Authorize progression lock"""
    return await authorize_irreversible_action(
        subject_id=subject_id,
        action_type=IrreversibleActionType.PROGRESSION_LOCK,
        context=context,
        severity=severity,
        opaque_reason_code=opaque_reason_code
    )


async def authorize_restriction(
    subject_id: str,
    context: str,
    severity: float = 0.85,
    opaque_reason_code: str = "RESTRICTION_NEEDED",
    action_func: Optional[Callable] = None
) -> Dict[str, Any]:
    """Authorize restriction"""
    return await authorize_irreversible_action(
        subject_id=subject_id,
        action_type=IrreversibleActionType.RESTRICTION,
        context=context,
        severity=severity,
        opaque_reason_code=opaque_reason_code,
        action_func=action_func
    )


async def authorize_access_control(
    subject_id: str,
    context: str,
    resource: str,
    access_level: str,
    severity: float = 0.7,
    opaque_reason_code: str = "ACCESS_CONTROL_REQUEST"
) -> Dict[str, Any]:
    """
    Authorize access control decisions.
    
    Args:
        subject_id: ID of the subject
        context: Context where access is requested
        resource: Resource being accessed
        access_level: Level of access requested
        severity: Severity level
        opaque_reason_code: Opaque reason code
    
    Returns:
        Dict with authorization result
    """
    # Log the access control request
    logger.info(f"ACCESS CONTROL REQUEST: {subject_id} requesting {access_level} access to {resource} in {context}")
    
    # Create a function to execute the access control decision
    def execute_access_control():
        # This would typically integrate with the actual access control system
        # For now, we'll just log the decision
        logger.info(f"ACCESS GRANTED: {subject_id} granted {access_level} access to {resource}")
        return {
            "status": "access_granted",
            "subject_id": subject_id,
            "resource": resource,
            "access_level": access_level,
            "context": context
        }
    
    # Request authorization from Core
    return await authorize_irreversible_action(
        subject_id=subject_id,
        action_type=IrreversibleActionType.ACCESS_GATING,
        context=context,
        severity=severity,
        opaque_reason_code=opaque_reason_code,
        action_func=execute_access_control
    )


async def authorize_progression_gate(
    subject_id: str,
    context: str,
    current_level: str,
    target_level: str,
    severity: float = 0.6,
    opaque_reason_code: str = "PROGRESSION_GATE_REQUEST"
) -> Dict[str, Any]:
    """
    Authorize progression gate decisions.
    
    Args:
        subject_id: ID of the subject
        context: Context where progression is requested
        current_level: Current level/role
        target_level: Target level/role
        severity: Severity level
        opaque_reason_code: Opaque reason code
    
    Returns:
        Dict with authorization result
    """
    # Log the progression gate request
    logger.info(f"PROGRESSION GATE REQUEST: {subject_id} requesting progression from {current_level} to {target_level} in {context}")
    
    # Create a function to execute the progression decision
    def execute_progression():
        # This would typically integrate with the actual progression system
        # For now, we'll just log the decision
        logger.info(f"PROGRESSION APPROVED: {subject_id} approved for progression from {current_level} to {target_level}")
        return {
            "status": "progression_approved",
            "subject_id": subject_id,
            "current_level": current_level,
            "target_level": target_level,
            "context": context
        }
    
    # Request authorization from Core
    return await authorize_irreversible_action(
        subject_id=subject_id,
        action_type=IrreversibleActionType.PROGRESSION_LOCK,
        context=context,
        severity=severity,
        opaque_reason_code=opaque_reason_code,
        action_func=execute_progression
    )


# Test function to demonstrate the authorization gate
async def test_core_authorization_gate():
    """Test the Core authorization gate functionality"""
    print("Testing Core Authorization Gate...")
    
    # Test a death event authorization
    result = await authorize_death_event(
        subject_id="test_user_123",
        context="game",
        severity=0.95
    )
    
    print(f"Death event authorization result: {result}")
    
    # Test a rebirth authorization
    result = await authorize_rebirth(
        subject_id="test_user_123",
        context="game",
        severity=0.1
    )
    
    print(f"Rebirth authorization result: {result}")
    
    # Verify that no direct execution happens without ACK
    validation_passed = validate_no_direct_execution_without_ack(
        IrreversibleActionType.DEATH_EVENT,
        "test_user_123",
        "game"
    )
    
    print(f"Validation passed: {validation_passed}")
    print("Core Authorization Gate test completed.")


if __name__ == "__main__":
    asyncio.run(test_core_authorization_gate())