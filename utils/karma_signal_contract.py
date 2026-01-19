"""
Canonical Karma Signal Contract Implementation
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum
from .sovereign_bridge import SignalType, emit_karma_signal


class KarmaSignal:
    """Canonical Karma Signal according to the specification"""
    
    def __init__(self, subject_id: str, context: str, signal: str, 
                 severity: float = 0.0, reason_code: str = "GENERIC", 
                 ttl: int = 300, requires_core_ack: bool = True):
        """
        Initialize a canonical karma signal
        
        Args:
            subject_id: UUID of the subject
            context: Platform context (assistant | game | finance | gurukul | infra)
            signal: Type of signal (allow | nudge | restrict | escalate)
            severity: Severity level (0.0 to 1.0)
            reason_code: Opaque reason code for the signal
            ttl: Time to live in seconds
            requires_core_ack: Whether Core ACK is required before applying consequences
        """
        self.data = {
            "subject_id": subject_id,
            "context": context,
            "signal": signal,
            "severity": severity,
            "reason_code": reason_code,
            "ttl": ttl,
            "requires_core_ack": requires_core_ack,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signal_id": str(uuid.uuid4())
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the signal as a dictionary"""
        return self.data
    
    @property
    def subject_id(self):
        return self.data.get("subject_id")
    
    @property
    def context(self):
        return self.data.get("context")
    
    @property
    def signal(self):
        return self.data.get("signal")
    
    @property
    def severity(self):
        return self.data.get("severity")
    
    @property
    def reason_code(self):
        return self.data.get("reason_code")
    
    @property
    def ttl(self):
        return self.data.get("ttl", 300)
    
    @property
    def requires_core_ack(self):
        return self.data.get("requires_core_ack", True)
    
    @property
    def timestamp(self):
        return self.data.get("timestamp")
    
    @property
    def signal_id(self):
        return self.data.get("signal_id")
    
    @classmethod
    def create_signal(cls, subject_id: str, context: str, signal: str, 
                      severity: float = 0.0, reason_code: str = "GENERIC",
                      ttl: int = 300, requires_core_ack: bool = True) -> 'KarmaSignal':
        """
        Create a canonical karma signal according to specification
        
        Args:
            subject_id: UUID of the subject
            context: Platform context (assistant | game | finance | gurukul | infra)
            signal: Type of signal (allow | nudge | restrict | escalate)
            severity: Severity level (0.0 to 1.0)
            reason_code: Opaque reason code for the signal
            ttl: Time to live in seconds
            requires_core_ack: Whether Core ACK is required before applying consequences
            
        Returns:
            KarmaSignal: New canonical karma signal
        """
        return cls(subject_id, context, signal, severity, reason_code, ttl, requires_core_ack)


def emit_canonical_karma_signal(subject_id: str, context: str, signal: str,
                               severity: float = 0.0, reason_code: str = "GENERIC",
                               ttl: int = 300, requires_core_ack: bool = True) -> Dict[str, Any]:
    """
    Emit a canonical karma signal to Sovereign Core for authorization
    
    Args:
        subject_id: UUID of the subject
        context: Platform context (assistant | game | finance | gurukul | infra)
        signal: Type of signal (allow | nudge | restrict | escalate)
        severity: Severity level (0.0 to 1.0)
        reason_code: Opaque reason code for the signal
        ttl: Time to live in seconds
        requires_core_ack: Whether Core ACK is required before applying consequences
        
    Returns:
        Dict: Authorization result from Sovereign Core
    """
    karma_signal = KarmaSignal(subject_id, context, signal, severity, reason_code, ttl, requires_core_ack)
    
    return emit_karma_signal(
        SignalType.CANONICAL_KARMA_SIGNAL,
        {
            "karma_signal": karma_signal.to_dict(),
            "event_type": "canonical_karma_signal"
        }
    )


def enforce_constraint_only_mode(enabled: bool = True) -> Dict[str, Any]:
    """
    Enable or disable constraint-only mode globally
    
    Args:
        enabled: Whether to enable constraint-only mode
        
    Returns:
        Dict: Status of the operation
    """
    from .sovereign_bridge import sovereign_bridge
    sovereign_bridge.constraint_only_mode = enabled
    
    return {
        "status": "success",
        "constraint_only_mode": enabled,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def is_constraint_only_mode() -> bool:
    """
    Check if constraint-only mode is enabled
    
    Returns:
        bool: Whether constraint-only mode is enabled
    """
    from .sovereign_bridge import sovereign_bridge
    return getattr(sovereign_bridge, 'constraint_only_mode', False)


def evaluate_constraint_signal(user_id: str, action: str, context: str) -> Optional[Dict[str, Any]]:
    """
    Evaluate whether an action requires constraint-based handling
    
    Args:
        user_id: ID of the user performing the action
        action: The action being performed
        context: Context where the action occurs
        
    Returns:
        Optional[Dict]: Signal if constraint is needed, None otherwise
    """
    # This is a simplified evaluation - in a real system, this would be more complex
    constraint_signals = {
        "cheat": {"signal": "restrict", "severity": 0.8, "reason_code": "CHEAT_DETECTED"},
        "harassment": {"signal": "restrict", "severity": 0.9, "reason_code": "HARASSMENT_DETECTED"},
        "spam": {"signal": "nudge", "severity": 0.6, "reason_code": "SPAM_DETECTED"},
        "rudeness": {"signal": "nudge", "severity": 0.4, "reason_code": "RUDE_BEHAVIOR_DETECTED"},
        "unsafe_intent": {"signal": "restrict", "severity": 0.95, "reason_code": "UNSAFE_INTENT_DETECTED"},
        "ignoring_guidance": {"signal": "nudge", "severity": 0.3, "reason_code": "GUIDANCE_IGNORED"},
        "politeness": {"signal": "allow", "severity": 0.2, "reason_code": "POSITIVE_BEHAVIOR"},
        "thoughtful_question": {"signal": "allow", "severity": 0.1, "reason_code": "ENGAGEMENT_POSITIVE"},
        "acknowledging_guidance": {"signal": "allow", "severity": 0.1, "reason_code": "POSITIVE_FEEDBACK"}
    }
    
    if action in constraint_signals:
        signal_info = constraint_signals[action]
        return {
            "subject_id": user_id,
            "context": context,
            "signal": signal_info["signal"],
            "severity": signal_info["severity"],
            "reason_code": signal_info["reason_code"],
            "ttl": 300,
            "requires_core_ack": True
        }
    
    return None