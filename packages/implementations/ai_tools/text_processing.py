"""
Text Processing Tool Implementation
Provides various text processing capabilities using AI techniques
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union
import re

logger = logging.getLogger(__name__)

class TextProcessingTool:
    """
    Text processing tool providing AI-powered text analysis and transformation
    capabilities integrated with LLM providers.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize text processing tool with configuration."""
        self.config = config or {}
        
        # Load LLM connector if provided
        self.llm_connector = self.config.get("llm_connector", None)
        if not self.llm_connector:
            logger.warning("No LLM connector provided. Some features will be limited.")
            
    def summarize(self, text: str, max_length: int = 200, format: str = "paragraph") -> str:
        """
        Summarize text to a specified maximum length.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary in characters
            format: Output format (paragraph, bullets, etc.)
            
        Returns:
            Summarized text
        """
        logger.info(f"Summarizing text ({len(text)} chars) to {max_length} chars")
        
        if not text:
            return ""
            
        # Handle short text
        if len(text) <= max_length:
            return text
            
        # Use LLM for summarization if available
        if self.llm_connector:
            prompt = f"""Summarize the following text in a {format} format. Keep your summary under {max_length} characters.
            
Text to summarize: {text}

Summary:"""
            
            try:
                response = self.llm_connector.generate(prompt, max_tokens=max_length // 4)
                summary = response.strip()
                # Ensure the summary is within the length limit
                if len(summary) > max_length:
                    summary = summary[:max_length-3] + "..."
                return summary
            except Exception as e:
                logger.error(f"Error using LLM for summarization: {str(e)}")
                # Fall back to extractive summarization
        
        # Extractive summarization as fallback
        return self._extractive_summarize(text, max_length, format)
            
    def _extractive_summarize(self, text: str, max_length: int, format: str) -> str:
        """Simple extractive summarization as fallback."""
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Score sentences by position and keyword frequency
        word_frequencies = {}
        for sentence in sentences:
            for word in re.findall(r'\w+', sentence.lower()):
                if len(word) > 3:  # Filter out short words
                    word_frequencies[word] = word_frequencies.get(word, 0) + 1
                    
        # Normalize word frequencies
        max_frequency = max(word_frequencies.values(), default=1)
        for word in word_frequencies:
            word_frequencies[word] = word_frequencies[word] / max_frequency
            
        # Score sentences
        sentence_scores = []
        for i, sentence in enumerate(sentences):
            score = 0.0
            # Position score (first and last sentences are important)
            position_weight = 1.0
            if i < len(sentences) * 0.2 or i > len(sentences) * 0.8:
                position_weight = 1.5
                
            # Word frequency score
            for word in re.findall(r'\w+', sentence.lower()):
                if word in word_frequencies:
                    score += word_frequencies[word]
                    
            # Length penalty for very short or very long sentences
            length = len(sentence.split())
            length_factor = 1.0
            if length < 5:
                length_factor = 0.8
            elif length > 30:
                length_factor = 0.7
                
            final_score = score * position_weight * length_factor
            sentence_scores.append((i, final_score, sentence))
            
        # Sort sentences by score
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Select top sentences up to max_length
        summary_sentences = []
        current_length = 0
        for _, _, sentence in sentence_scores:
            sentence_length = len(sentence) + 1  # +1 for space
            if current_length + sentence_length <= max_length:
                summary_sentences.append(sentence)
                current_length += sentence_length
            else:
                break
                
        # Re-order sentences based on original order
        summary_sentences.sort(key=lambda s: sentences.index(s))
        
        # Format output
        if format == "bullets":
            return "\n• " + "\n• ".join(summary_sentences)
        else:
            return " ".join(summary_sentences)
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of extracted entities with type and mentions
        """
        logger.info(f"Extracting entities from text ({len(text)} chars)")
        
        # Use LLM for entity extraction if available
        if self.llm_connector:
            prompt = """Extract all named entities from the following text. Return the result as a JSON array where each item has "text", "type", and "mentions" (array of offsets). 
Entity types to look for: PERSON, ORGANIZATION, LOCATION, DATE, EVENT, PRODUCT.

Text to analyze: 
"""
            prompt += text
            prompt += """

Output format example:
[
  {
    "text": "Apple",
    "type": "ORGANIZATION",
    "mentions": [{"start": 10, "end": 15}]
  }
]

Entities:"""
            
            try:
                response = self.llm_connector.generate(prompt)
                
                # Extract JSON from response
                json_match = re.search(r'\[.*?\]', response.replace('\n', ' '), re.DOTALL)
                if json_match:
                    try:
                        entities = json.loads(json_match.group())
                        return entities
                    except json.JSONDecodeError:
                        logger.error("Could not parse entity JSON from LLM")
                else:
                    logger.error("No entity JSON found in LLM response")
                    
            except Exception as e:
                logger.error(f"Error using LLM for entity extraction: {str(e)}")
        
        # Simple regex-based extraction as fallback
        return self._simple_entity_extraction(text)
            
    def _simple_entity_extraction(self, text: str) -> List[Dict[str, Any]]:
        """Simple pattern-based entity extraction as fallback."""
        entities = []
        
        # Simple patterns for common entity types
        patterns = {
            "DATE": r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b|\b\d{1,2}[-\/]\d{1,2}[-\/]\d{2,4}\b',
            "PERSON": r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b',
            "ORGANIZATION": r'\b[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*\s+(?:Inc|Corp|LLC|Ltd|Co|Group|Foundation)\b',
            "LOCATION": r'\b[A-Z][a-z]+(?:,\s+[A-Z][a-z]+)?\b'
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entity_text = match.group()
                start, end = match.span()
                
                # Check if this entity overlaps with an existing one
                overlapping = False
                for existing in entities:
                    for mention in existing["mentions"]:
                        if (start < mention["end"] and end > mention["start"]):
                            overlapping = True
                            break
                
                if not overlapping:
                    entities.append({
                        "text": entity_text,
                        "type": entity_type,
                        "mentions": [{"start": start, "end": end}]
                    })
                    
        return entities
    
    def classify_text(self, text: str, categories: List[str]) -> Dict[str, float]:
        """
        Classify text into given categories with confidence scores.
        
        Args:
            text: Text to classify
            categories: List of categories to classify into
            
        Returns:
            Dictionary mapping categories to confidence scores
        """
        logger.info(f"Classifying text into {len(categories)} categories")
        
        if not categories:
            return {}
            
        # Use LLM for classification if available
        if self.llm_connector:
            categories_str = ", ".join(categories)
            prompt = f"""Classify the following text into the most relevant categories from this list: {categories_str}. 
For each category, provide a confidence score between 0.0 and 1.0, where 1.0 means complete confidence it belongs to that category.
Return results as a JSON object with categories as keys and confidence scores as values.

Text to classify: 
{text}

Classification (JSON):"""
            
            try:
                response = self.llm_connector.generate(prompt)
                
                # Extract JSON from response
                json_match = re.search(r'\{.*?\}', response.replace('\n', ' '), re.DOTALL)
                if json_match:
                    try:
                        scores = json.loads(json_match.group())
                        # Ensure all scores are floats between 0 and 1
                        sanitized = {}
                        for cat, score in scores.items():
                            if cat in categories:
                                sanitized[cat] = min(1.0, max(0.0, float(score)))
                        return sanitized
                    except json.JSONDecodeError:
                        logger.error("Could not parse classification JSON from LLM")
                        
            except Exception as e:
                logger.error(f"Error using LLM for classification: {str(e)}")
                
        # Simple keyword-based classification as fallback
        return self._keyword_classification(text, categories)
            
    def _keyword_classification(self, text: str, categories: List[str]) -> Dict[str, float]:
        """Simple keyword-based classification as fallback."""
        # Generate word sets for each category
        text = text.lower()
        
        # Count word occurrence
        words = re.findall(r'\b\w+\b', text)
        word_count = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_count[word] = word_count.get(word, 0) + 1
                
        # Calculate scores based on word resemblance to categories
        scores = {}
        for category in categories:
            category_lower = category.lower()
            score = 0.0
            
            # Check direct category mention
            if category_lower in text:
                score += 0.5
                
            # Check word-by-word match
            category_words = re.findall(r'\b\w+\b', category_lower)
            for cat_word in category_words:
                if cat_word in word_count and len(cat_word) > 3:
                    score += 0.2 * word_count[cat_word] / len(words)
                    
            scores[category] = min(1.0, score)
            
        # Normalize scores
        total = sum(scores.values()) or 1.0
        for cat in scores:
            scores[cat] = scores[cat] / total
            
        return scores
