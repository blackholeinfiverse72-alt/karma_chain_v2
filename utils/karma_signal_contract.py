"""
Canonical Karma Signal Contract Implementation - FINAL VERSION
ONLY canonical signal format permitted - no legacy or alternative formats
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum
from .sovereign_bridge import SignalType, emit_karma_signal


class KarmaSignal:
    """Canonical Karma Signal - ONLY this format permitted"""
    
    def __init__(self, subject_id: str, product_context: str, signal: str, 
                 severity: float, ttl: int, opaque_reason_code: str, 
                 requires_core_ack: bool = True):
        """
        Initialize a canonical karma signal - STRICT format enforcement
        
        Args:
            subject_id: UUID of the subject (REQUIRED)
            product_context: Platform context (assistant | game | finance | gurukul | infra | workflow) (REQUIRED)
            signal: Type of signal (allow | nudge | restrict | escalate) (REQUIRED)
            severity: Severity level (0.0 to 1.0) (REQUIRED)
            ttl: Time to live in seconds (REQUIRED)
            opaque_reason_code: Opaque reason code (REQUIRED)
            requires_core_ack: Must be True (default enforced)
        """
        # Validate all required fields
        self._validate_fields(subject_id, product_context, signal, severity, ttl, opaque_reason_code)
        
        # Enforce requires_core_ack = True - no exceptions
        if not requires_core_ack:
            raise ValueError("requires_core_ack MUST be True - all signals require Core authorization")
        
        self.data = {
            "subject_id": subject_id,
            "product_context": product_context,
            "signal": signal,
            "severity": severity,
            "ttl": ttl,
            "requires_core_ack": True,  # ALWAYS True - enforced
            "opaque_reason_code": opaque_reason_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signal_id": str(uuid.uuid4())
        }
    
    def _validate_fields(self, subject_id: str, product_context: str, signal: str, 
                        severity: float, ttl: int, opaque_reason_code: str):
        """Validate all required fields according to canonical contract"""
        # subject_id validation
        if not subject_id or not isinstance(subject_id, str):
            raise ValueError("subject_id is required and must be a string")
        
        # product_context validation
        valid_contexts = ["assistant", "game", "finance", "gurukul", "infra", "workflow"]
        if product_context not in valid_contexts:
            raise ValueError(f"product_context must be one of: {valid_contexts}")
        
        # signal validation
        valid_signals = ["allow", "nudge", "restrict", "escalate"]
        if signal not in valid_signals:
            raise ValueError(f"signal must be one of: {valid_signals}")
        
        # severity validation
        if not isinstance(severity, (int, float)) or severity < 0.0 or severity > 1.0:
            raise ValueError("severity must be a number between 0.0 and 1.0")
        
        # ttl validation
        if not isinstance(ttl, int) or ttl < 1:
            raise ValueError("ttl must be an integer >= 1")
        
        # opaque_reason_code validation
        if not opaque_reason_code or not isinstance(opaque_reason_code, str):
            raise ValueError("opaque_reason_code is required and must be a string")
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the signal as a dictionary - canonical format only"""
        return self.data.copy()
    
    @property
    def subject_id(self) -> str:
        return self.data["subject_id"]
    
    @property
    def product_context(self) -> str:
        return self.data["product_context"]
    
    @property
    def signal(self) -> str:
        return self.data["signal"]
    
    @property
    def severity(self) -> float:
        return self.data["severity"]
    
    @property
    def ttl(self) -> int:
        return self.data["ttl"]
    
    @property
    def requires_core_ack(self) -> bool:
        return self.data["requires_core_ack"]
    
    @property
    def opaque_reason_code(self) -> str:
        return self.data["opaque_reason_code"]
    
    @property
    def timestamp(self) -> str:
        return self.data["timestamp"]
    
    @property
    def signal_id(self) -> str:
        return self.data["signal_id"]
    
    @classmethod
    def create_canonical_signal(cls, subject_id: str, product_context: str, signal: str,
                               severity: float, ttl: int, opaque_reason_code: str) -> 'KarmaSignal':
        """
        Create a canonical karma signal - ONLY approved method
        
        Args:
            subject_id: UUID of the subject
            product_context: Platform context
            signal: Signal type (allow | nudge | restrict | escalate)
            severity: Severity level (0.0 to 1.0)
            ttl: Time to live in seconds
            opaque_reason_code: Opaque reason code
            
        Returns:
            KarmaSignal: New canonical karma signal
        """
        return cls(subject_id, product_context, signal, severity, ttl, opaque_reason_code, True)


def emit_canonical_karma_signal(subject_id: str, product_context: str, signal: str,
                               severity: float, ttl: int, opaque_reason_code: str) -> Dict[str, Any]:
    """
    Emit a canonical karma signal to Sovereign Core - ONLY approved method
    
    Args:
        subject_id: UUID of the subject
        product_context: Platform context
        signal: Signal type (allow | nudge | restrict | escalate)
        severity: Severity level (0.0 to 1.0)
        ttl: Time to live in seconds
        opaque_reason_code: Opaque reason code
        
    Returns:
        Dict: Authorization result from Sovereign Core
    """
    # Create canonical signal - only approved way
    karma_signal = KarmaSignal.create_canonical_signal(
        subject_id=subject_id,
        product_context=product_context,
        signal=signal,
        severity=severity,
        ttl=ttl,
        opaque_reason_code=opaque_reason_code
    )
    
    return emit_karma_signal(
        SignalType.CANONICAL_KARMA_SIGNAL,
        {
            "karma_signal": karma_signal.to_dict(),
            "event_type": "canonical_karma_signal"
        }
    )


# DEPRECATED FUNCTIONS - WILL BE REMOVED
# These functions exist for backward compatibility but should not be used
# All new code MUST use the canonical format above

def enforce_constraint_only_mode(enabled: bool = True) -> Dict[str, Any]:
    """
    DEPRECATED: Enable or disable constraint-only mode globally
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
    DEPRECATED: Check if constraint-only mode is enabled
    """
    from .sovereign_bridge import sovereign_bridge
    return getattr(sovereign_bridge, 'constraint_only_mode', False)


def evaluate_constraint_signal(user_id: str, action: str, context: str) -> Optional[Dict[str, Any]]:
    """
    DEPRECATED: Evaluate constraint signals - use canonical format instead
    """
    # This function is deprecated - use canonical signal creation instead
    raise DeprecationWarning("evaluate_constraint_signal is deprecated - use canonical KarmaSignal creation")