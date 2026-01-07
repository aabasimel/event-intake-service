"""
Error capture seam for unhandled exceptions with structured logging
"""
import json
import logging
import traceback
import sys
from typing import Dict, Any, Optional
from django.http import HttpRequest

logger = logging.getLogger(__name__)


class ErrorCaptureMiddleware:
    """
    Middleware to capture unhandled exceptions and log them in structured format
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process the request
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """
        Called when a view raises an exception
        """
        self._log_exception(exception, request)
        return None
    
    def _log_exception(self, exception: Exception, request: Optional[HttpRequest] = None) -> None:
        """
        Log exception in structured JSON format with FANCYLOG: prefix
        """
        try:
            request_info = {}
            if request:
                request_info = {
                    'endpoint': request.path,
                    'method': request.method,
                    'request_id': request.headers.get('X-Request-Id') or getattr(request, 'request_id', 'unknown'),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'client_ip': self._get_client_ip(request),
                }
            
            safe_input = self._extract_safe_input(request)
            
            log_entry = {
                'type': 'unhandled_exception',
                'error': {
                    'message': str(exception),
                    'exception_type': type(exception).__name__,
                    'module': exception.__class__.__module__,
                },
                'stack_trace': self._get_stack_trace(exception),
                'request': request_info,
                'input': safe_input,
                'timestamp': self._get_timestamp(),
            }
            
            # Log with FANCYLOG: prefix
            logger.error(f"FANCYLOG:{json.dumps(log_entry, default=str)}")
            
        except Exception as log_error:
            logger.error(f"Failed to log exception: {log_error}", exc_info=True)
            logger.error(f"Original exception: {exception}", exc_info=True)

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP safely"""
        try:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR', 'unknown')
            return ip
        except:
            return 'unknown'
    
    def _get_timestamp(self) -> str:
        """Get ISO timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'