"""
Perception module: normalizes and preprocesses input events (text, sensor, file, etc.) for Archivist.
"""
import logging

logger = logging.getLogger(__name__)

class PerceptionModule:
    def __init__(self):
        pass

    def normalize_event(self, event):
        """Convert raw input event to normalized format."""
        # Placeholder: just return the event as-is
        logger.debug(f"Normalizing event: {event}")
        return event
