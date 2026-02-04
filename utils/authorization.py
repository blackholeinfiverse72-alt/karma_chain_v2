"""
Authorization utilities for KarmaChain Sovereign Isolation
Implements Bucket/Core authorization checks
"""

import logging
from fastapi import Request, HTTPException
from typing import List

logger = logging.getLogger(__name__)

# Authorized sources for direct API access
AUTHORIZED_SOURCES = [
    "bucket",      # BHIV Bucket
    "core",        # Sovereign Core
    "internal"     # Internal system calls
]

# Define endpoints that should only accept calls from authorized sources
RESTRICTED_ENDPOINTS = [
    "/api/v1/log-action",
    "/api/v1/karma",
    "/api/v1/feedback_signal",
    "/api/v1/analytics",
    "/api/v1/karma/lifecycle",
    "/api/v1/karma/simulate",
    "/v1/karma/event"
]


def check_authorized_source(request: Request) -> bool:
    """
    Check if the request comes from an authorized source (Bucket or Core)
    
    Args:
        request: FastAPI request object
        
    Returns:
        bool: True if authorized, raises HTTPException if not
    """
    path = request.url.path
    
    # Check if this is a restricted endpoint that requires bucket/core authorization
    if path in RESTRICTED_ENDPOINTS:
        # Check if the request is coming from an authorized source
        source_header = request.headers.get('x-source', '').lower()
        auth_header = request.headers.get('authorization', '').lower()
        
        # Check if it's from authorized sources
        is_authorized = (
            source_header in AUTHORIZED_SOURCES or
            'bucket' in source_header or 
            'core' in source_header or
            'bucket' in auth_header or
            'core' in auth_header
        )
        
        # Also check for specific header that indicates bucket/core origin
        x_origin = request.headers.get('x-karmachain-origin', '').lower()
        is_authorized = is_authorized or 'bucket' in x_origin or 'core' in x_origin
        
        # Log the access attempt for monitoring
        if not is_authorized:
            logger.warning(f"Direct application call rejected to restricted endpoint {path} from source: {source_header}")
            
            raise HTTPException(
                status_code=403,
                detail={
                    'error': f'Access denied: {path} is restricted to authorized sources only (Bucket or Core)',
                    'type': 'authorization_error',
                    'field': 'access_control'
                }
            )
        else:
            logger.info(f"Authorized call to restricted endpoint {path} from source: {x_origin or source_header}")
    
    return True