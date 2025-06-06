"""
Structured/context-aware logging for the core system.
"""
import logging
import json

class ContextJsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'level': record.levelname,
            'message': record.getMessage(),
            'user_id': getattr(record, 'user_id', None),
            'session_id': getattr(record, 'session_id', None),
            'request_id': getattr(record, 'request_id', None),
            'context': getattr(record, 'context', None),
        }
        return json.dumps(log_record)

logger = logging.getLogger("core")
handler = logging.StreamHandler()
handler.setFormatter(ContextJsonFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def log_context(message, user_id=None, session_id=None, request_id=None, context=None, level=logging.INFO):
    extra = {'user_id': user_id, 'session_id': session_id, 'request_id': request_id, 'context': context}
    logger.log(level, message, extra=extra)
# ...existing code...
