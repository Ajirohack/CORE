"""
FMT Processor module for handling Format Templates and processing conversation text

This module implements the core functionality for the Archivist Mode's FMT system
"""
import re
import json
from typing import Dict, Any, List, Optional
import os
import logging

logger = logging.getLogger(__name__)

class FMTProcessor:
    """
    Format Template Processor for handling character communication formats
    Based on the reference system's approach to conversation templates
    """
    
    def __init__(self):
        self.templates = {}
        self.character_templates = {}
        
    def load_template(self, template_id: str, template_data: Dict[str, Any]):
        """
        Load a template into the processor
        """
        self.templates[template_id] = template_data
        
        # If this template is for a specific character, organize by character
        character_id = template_data.get('character_id')
        if character_id:
            if character_id not in self.character_templates:
                self.character_templates[character_id] = {}
                
            self.character_templates[character_id][template_id] = template_data
    
    def process_template(self, template_id: str, variables: Dict[str, Any]) -> str:
        """
        Process a template with the given variables
        """
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
            
        template = self.templates[template_id]
        template_text = template['template_text']
        
        # Process replacements including array indexing: {{variable}}, {{variable.property}}, {{variable.array[0]}}
        def replace_var(match):
            var_path = match.group(1).strip()
            
            # Check if there's array indexing
            array_match = re.search(r'(\w+)\.(\w+)\[(\d+)\]', var_path)
            if array_match:
                obj_name, arr_name, idx = array_match.groups()
                idx = int(idx)
                
                if obj_name in variables and arr_name in variables[obj_name]:
                    arr = variables[obj_name][arr_name]
                    if isinstance(arr, list) and 0 <= idx < len(arr):
                        return str(arr[idx])
                return match.group(0)  # Return original if not found or invalid
                
            # Regular path navigation
            path_parts = var_path.split('.')
            
            # Navigate through nested dictionary
            value = variables
            for part in path_parts:
                if part in value:
                    value = value[part]
                else:
                    # If key not found, return the original placeholder
                    return match.group(0)
            
            return str(value)
        
        # Replace variables in the template
        processed_text = re.sub(r'\{\{(.*?)\}\}', replace_var, template_text)
        return processed_text
        
    def analyze_conversation(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze conversation history to extract key information
        """
        # This would be a sophisticated analysis in the real implementation
        # For now, we'll return a simplified analysis
        
        target_messages = [msg for msg in conversation_history if not msg.get('is_character', False)]
        character_messages = [msg for msg in conversation_history if msg.get('is_character', False)]
        
        total_messages = len(conversation_history)
        target_engagement = len(target_messages) / max(1, total_messages)
        
        avg_target_length = sum(len(msg.get('content', '')) for msg in target_messages) / max(1, len(target_messages))
        avg_character_length = sum(len(msg.get('content', '')) for msg in character_messages) / max(1, len(character_messages))
        
        response_ratio = avg_target_length / max(1, avg_character_length)
        
        sentiment = "neutral"
        if response_ratio > 1.2:
            sentiment = "positive"
        elif response_ratio < 0.8:
            sentiment = "hesitant"
            
        return {
            "message_count": total_messages,
            "target_messages": len(target_messages),
            "character_messages": len(character_messages),
            "target_engagement": target_engagement,
            "avg_target_message_length": avg_target_length,
            "avg_character_message_length": avg_character_length,
            "response_ratio": response_ratio,
            "estimated_sentiment": sentiment,
            "trust_level": min(100, (total_messages / 10) * 100),
            "potential_topics": extract_potential_topics(conversation_history),
            "vulnerability_indicators": identify_vulnerability_indicators(target_messages),
        }
        
    def recommend_template(self, 
                          character_id: str, 
                          conversation_analysis: Dict[str, Any], 
                          target_profile: Dict[str, Any]) -> Optional[str]:
        """
        Recommend the best template to use next based on conversation analysis and target profile
        """
        if character_id not in self.character_templates:
            logger.warning(f"No templates found for character {character_id}")
            return None
            
        character_templates = self.character_templates[character_id]
        
        # In a real implementation, this would use ML/NLP to match templates to context
        # For this proof of concept, we'll use a rule-based approach
        
        trust_level = conversation_analysis.get('trust_level', 0)
        message_count = conversation_analysis.get('message_count', 0)
        sentiment = conversation_analysis.get('estimated_sentiment', 'neutral')
        
        # Initial contact
        if message_count == 0:
            intro_templates = [t_id for t_id, t in character_templates.items() 
                              if 'introduction' in (t.get('tags') or [])]
            if intro_templates:
                return intro_templates[0]
        
        # Re-engagement needed
        if sentiment == 'hesitant' or trust_level < 30:
            reengagement_templates = [t_id for t_id, t in character_templates.items() 
                                    if 'follow-up' in (t.get('tags') or [])]
            if reengagement_templates:
                return reengagement_templates[0]
        
        # Trust building needed
        if trust_level < 50:
            trust_templates = [t_id for t_id, t in character_templates.items() 
                              if 'trust-building' in (t.get('tags') or [])]
            if trust_templates:
                return trust_templates[0]
        
        # Deeper connection
        if trust_level >= 50:
            personal_templates = [t_id for t_id, t in character_templates.items() 
                                if 'personal' in (t.get('tags') or [])]
            if personal_templates:
                return personal_templates[0]
                
        # If no specific recommendation, sort templates by step number and recommend next
        step_templates = {t.get('step_number'): t_id for t_id, t in character_templates.items() 
                         if t.get('step_number') is not None}
                         
        if step_templates:
            current_step = int(message_count / 3) + 1
            next_step = min([s for s in step_templates.keys() if s > current_step], 
                           default=min(step_templates.keys()))
            return step_templates[next_step]
            
        # Fallback to any template
        if character_templates:
            return list(character_templates.keys())[0]
            
        return None
        
# Helper functions

def extract_potential_topics(conversation_history):
    """Extract potential topics from conversation history"""
    # In a real implementation, this would use NLP topic extraction
    # For now, return a simplified version
    all_text = " ".join([msg.get('content', '') for msg in conversation_history])
    
    topics = []
    if "travel" in all_text.lower():
        topics.append("travel")
    if "family" in all_text.lower():
        topics.append("family")
    if "work" in all_text.lower():
        topics.append("work/career")
    if "hobby" in all_text.lower() or "interest" in all_text.lower():
        topics.append("hobbies")
    if "friend" in all_text.lower():
        topics.append("friendships")
    if "relationship" in all_text.lower() or "partner" in all_text.lower():
        topics.append("relationships")
        
    return topics or ["general conversation"]

def identify_vulnerability_indicators(messages):
    """Identify potential vulnerability indicators in messages"""
    # In a real implementation, this would use NLP for sentiment and vulnerability analysis
    # For now, return a simplified version
    all_text = " ".join([msg.get('content', '') for msg in messages])
    
    indicators = []
    if "lonely" in all_text.lower() or "alone" in all_text.lower():
        indicators.append({"type": "loneliness", "confidence": 0.8})
    if "miss" in all_text.lower() and ("someone" in all_text.lower() or "relationship" in all_text.lower()):
        indicators.append({"type": "romantic longing", "confidence": 0.7})
    if "money" in all_text.lower() or "financial" in all_text.lower() or "afford" in all_text.lower():
        indicators.append({"type": "financial concern", "confidence": 0.6})
    if "trust" in all_text.lower() and "issue" in all_text.lower():
        indicators.append({"type": "trust issues", "confidence": 0.75})
        
    return indicators
