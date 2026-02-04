"""
Authorization Logging Module for Core Authorization Gate
Implements comprehensive logging for Core ACK/DENY/TIMEOUT events
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum

# Set up logger
logger = logging.getLogger(__name__)

class AuthorizationEventType(Enum):
    """Types of authorization events"""
    REQUEST = "authorization_request"
    ACK = "core_ack"
    DENY = "core_deny"
    TIMEOUT = "core_timeout"
    EXECUTION = "action_execution"
    AUDIT = "audit_log"

class AuthorizationLogger:
    """Handles comprehensive logging for Core authorization events"""
    
    def __init__(self):
        self.audit_log = []
    
    def log_authorization_request(
        self,
        subject_id: str,
        action_type: str,
        context: str,
        severity: float,
        opaque_reason_code: str
    ) -> str:
        """Log an authorization request"""
        event_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        log_entry = {
            "event_id": event_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": AuthorizationEventType.REQUEST.value,
            "subject_id": subject_id,
            "action_type": action_type,
            "context": context,
            "severity": severity,
            "opaque_reason_code": opaque_reason_code,
            "status": "pending"
        }
        
        logger.info(f"CORE AUTHORIZATION REQUEST: {json.dumps(log_entry)}")
        self.audit_log.append(log_entry)
        
        return event_id
    
    def log_core_ack(
        self,
        event_id: str,
        subject_id: str,
        action_type: str,
        core_response: Dict[str, Any]
    ):
        """Log Core ACK event"""
        log_entry = {
            "event_id": event_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": AuthorizationEventType.ACK.value,
            "subject_id": subject_id,
            "action_type": action_type,
            "core_response": core_response,
            "status": "authorized"
        }
        
        logger.info(f"CORE AUTHORIZATION ACK: {json.dumps(log_entry)}")
        self.audit_log.append(log_entry)
    
    def log_core_deny(
        self,
        event_id: str,
        subject_id: str,
        action_type: str,
        core_response: Dict[str, Any]
    ):
        """Log Core DENY event"""
        log_entry = {
            "event_id": event_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": AuthorizationEventType.DENY.value,
            "subject_id": subject_id,
            "action_type": action_type,
            "core_response": core_response,
            "status": "denied"
        }
        
        logger.warning(f"CORE AUTHORIZATION DENY: {json.dumps(log_entry)}")
        self.audit_log.append(log_entry)
        
        # Also log the audit entry
        self.log_audit_discard(event_id, subject_id, action_type, "Core DENY")
    
    def log_core_timeout(
        self,
        event_id: str,
        subject_id: str,
        action_type: str,
        timeout_duration: int
    ):
        """Log Core TIMEOUT event"""
        log_entry = {
            "event_id": event_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": AuthorizationEventType.TIMEOUT.value,
            "subject_id": subject_id,
            "action_type": action_type,
            "timeout_duration": timeout_duration,
            "status": "timeout"
        }
        
        logger.warning(f"CORE AUTHORIZATION TIMEOUT: {json.dumps(log_entry)}")
        self.audit_log.append(log_entry)
        
        # Also log the audit entry
        self.log_audit_discard(event_id, subject_id, action_type, "Core TIMEOUT")
    
    def log_action_execution(
        self,
        event_id: str,
        subject_id: str,
        action_type: str,
        execution_result: Dict[str, Any]
    ):
        """Log action execution event"""
        log_entry = {
            "event_id": event_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": AuthorizationEventType.EXECUTION.value,
            "subject_id": subject_id,
            "action_type": action_type,
            "execution_result": execution_result,
            "status": "executed"
        }
        
        logger.info(f"ACTION EXECUTION: {json.dumps(log_entry)}")
        self.audit_log.append(log_entry)
    
    def log_audit_discard(
        self,
        event_id: str,
        subject_id: str,
        action_type: str,
        reason: str
    ):
        """Log audit entry for discarded actions"""
        log_entry = {
            "event_id": event_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": AuthorizationEventType.AUDIT.value,
            "subject_id": subject_id,
            "action_type": action_type,
            "reason": reason,
            "status": "discarded"
        }
        
        logger.info(f"AUDIT LOG ENTRY: {json.dumps(log_entry)}")
        self.audit_log.append(log_entry)
    
    def get_audit_summary(self, limit: int = 100) -> Dict[str, Any]:
        """Get audit log summary"""
        recent_entries = self.audit_log[-limit:] if len(self.audit_log) > limit else self.audit_log
        
        # Count events by type
        event_counts = {}
        for entry in recent_entries:
            event_type = entry.get("event_type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            "total_entries": len(self.audit_log),
            "recent_entries": len(recent_entries),
            "event_counts": event_counts,
            "entries": recent_entries
        }
    
    def clear_audit_log(self):
        """Clear the audit log"""
        self.audit_log.clear()
        logger.info("Audit log cleared")

# Global instance
auth_logger = AuthorizationLogger()

# Convenience functions
def log_auth_request(subject_id: str, action_type: str, context: str, severity: float, opaque_reason_code: str) -> str:
    """Log an authorization request"""
    return auth_logger.log_authorization_request(subject_id, action_type, context, severity, opaque_reason_code)

def log_auth_ack(event_id: str, subject_id: str, action_type: str, core_response: Dict[str, Any]):
    """Log Core ACK"""
    auth_logger.log_core_ack(event_id, subject_id, action_type, core_response)

def log_auth_deny(event_id: str, subject_id: str, action_type: str, core_response: Dict[str, Any]):
    """Log Core DENY"""
    auth_logger.log_core_deny(event_id, subject_id, action_type, core_response)

def log_auth_timeout(event_id: str, subject_id: str, action_type: str, timeout_duration: int):
    """Log Core TIMEOUT"""
    auth_logger.log_core_timeout(event_id, subject_id, action_type, timeout_duration)

def log_action_exec(event_id: str, subject_id: str, action_type: str, execution_result: Dict[str, Any]):
    """Log action execution"""
    auth_logger.log_action_execution(event_id, subject_id, action_type, execution_result)

def get_audit_summary(limit: int = 100) -> Dict[str, Any]:
    """Get audit summary"""
    return auth_logger.get_audit_summary(limit)

def log_audit_discard(event_id: str, subject_id: str, action_type: str, reason: str):
    """Log audit discard"""
    auth_logger.log_audit_discard(event_id, subject_id, action_type, reason)

def clear_audit_log():
    """Clear audit log"""
    auth_logger.clear_audit_log()