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


class DeliberateError(Exception):
    """Custom exception for deliberate error paths"""
    pass


class ErrorCaptureMiddleware:
    """
    Middleware to capture unhandled exceptions and log them in structured format
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
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
    def _get_stack_trace(self, exception: Exception) -> str:
        """Extract formatted stack trace"""
        try:
            return ''.join(traceback.format_exception(
                type(exception), exception, exception.__traceback__
            ))
        except:
            return "Stack trace unavailable"
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
    def _extract_safe_input(self, request: Optional[HttpRequest]) -> Dict[str, Any]:
        
        if not request or not hasattr(request, 'data'):
            return {}
        
        try:
            data = getattr(request, 'data', {})
            if not isinstance(data, dict):
                return {'input_type': type(data).__name__}
            
            safe_input = {}
            
            for field in ['event', 'user_id']:
                if field in data:
                    value = data[field]
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + '...'
                    safe_input[field] = value
            
            if 'metadata' in data and isinstance(data['metadata'], dict):
                safe_input['metadata_size'] = len(str(data['metadata']))
                safe_input['metadata_key_count'] = len(data['metadata'])
            
            safe_input['input_fields'] = list(data.keys())
            
            return safe_input
            
        except Exception:
            return {'error': 'could_not_extract_input'}
    def _get_timestamp(self) -> str:
        """Get ISO timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'


def trigger_explode_error(request: HttpRequest) -> None:
    """
    Trigger an exception if event == "explode"
    This is a deliberately triggered error path for testing
    """
    try:
        data = getattr(request, 'data', {})
        if isinstance(data, dict) and data.get('event') == 'explode':
            logger.warning("Deliberate error triggered: event == 'explode'")
            
            raise DeliberateError(
                f"BOOM! Event 'explode' triggered at {request.path} "
                f"for user {data.get('user_id', 'unknown')}"
            )
    except DeliberateError:
        raise
    except Exception as e:
        pass