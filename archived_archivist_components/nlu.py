"""
NLU module: parses text to intent/entities using LLM or spaCy, etc.
"""
import logging

logger = logging.getLogger(__name__)

class NLUModule:
    def __init__(self):
        pass

    def parse(self, text):
        """Parse text to intent/entities. Placeholder: returns dummy intent/entity."""
        logger.debug(f"Parsing text: {text}")
        return {"intent": "unknown", "entities": {}}
