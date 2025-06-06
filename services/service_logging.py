"""
Structured logging for core services
"""
import logging
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime

class ServiceLogger:
    """Structured logger for core services"""
    
    def __init__(self, service_name: str, log_level: str = "INFO"):
        self.service_name = service_name
        self.logger = logging.getLogger(f"service.{service_name}")
        
        # Set log level
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create custom formatter
        formatter = StructuredFormatter(service_name)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message with context"""
        extra = self._build_extra(context, **kwargs)
        self.logger.info(message, extra=extra)
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None, error: Optional[Exception] = None, **kwargs):
        """Log error message with context"""
        extra = self._build_extra(context, **kwargs)
        if error:
            extra['error'] = str(error)
            extra['error_type'] = type(error).__name__
        self.logger.error(message, extra=extra)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message with context"""
        extra = self._build_extra(context, **kwargs)
        self.logger.warning(message, extra=extra)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message with context"""
        extra = self._build_extra(context, **kwargs)
        self.logger.debug(message, extra=extra)
    
    def _build_extra(self, context: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Build extra context for logging"""
        extra = {
            'service_name': self.service_name,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        if context:
            extra['context'] = context
        
        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in extra:
                extra[key] = value
        
        return extra

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': self.service_name,
            'level': record.levelname,
            'message': record.getMessage(),
        }
        
        # Add extra context if available
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
            
        if hasattr(record, 'error'):
            log_entry['error'] = record.error
            
        if hasattr(record, 'error_type'):
            log_entry['error_type'] = record.error_type
        
        return json.dumps(log_entry)
