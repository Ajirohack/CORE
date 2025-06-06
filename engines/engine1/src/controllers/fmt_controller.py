"""
FMT Controller for handling Format Template processing

This module implements controllers for:
1. Chat parsing and analysis
2. Emotion mapping
3. Profile building
4. FMT recommendations

Based on the references from the WhyteHoux system
"""
from typing import Dict, List, Any, Optional
import re
import json
import logging
from datetime import datetime

from core.engines.engine1.src.fmt_processor import FMTProcessor

logger = logging.getLogger(__name__)

class FMTController:
    """
    Controller for FMT (Format Template) processing and recommendations
    Handles conversation analysis, emotion mapping and profile building
    """
    
    def __init__(self):
        self.fmt_processor = FMTProcessor()
        self.emotion_patterns = self._load_emotion_patterns()
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        
    def _load_emotion_patterns(self) -> Dict[str, List[str]]:
        """
        Load emotion detection patterns
        """
        # In a real implementation, this would load from reference files
        return {
            "joy": ["happy", "joy", "excite", "thrill", "delight", "content"],
            "sadness": ["sad", "miss", "hurt", "pain", "alone", "lonely"],
            "fear": ["afraid", "scared", "worry", "anxious", "nervous"],
            "anger": ["angry", "upset", "frustrate", "annoy", "irritate"],
            "trust": ["trust", "believe", "faith", "rely", "depend"],
            "interest": ["interest", "curious", "fascinate", "intrigued"],
            "surprise": ["surprise", "shock", "astonish", "amaze"],
            "vulnerability": ["help", "need", "desperate", "problem", "stress", "difficult"]
        }
        
    def _load_vulnerability_patterns(self) -> Dict[str, List[str]]:
        """
        Load vulnerability detection patterns
        """
        # In a real implementation, this would load from reference files
        return {
            "financial": ["money", "financial", "cost", "afford", "expensive", "budget", "loan", "debt"],
            "emotional": ["lonely", "alone", "miss", "heartbroken", "hurt", "sad", "depressed"],
            "trust": ["trust issues", "cheated on", "betrayed", "lied to", "backstabbed"],
            "health": ["sick", "health", "disease", "condition", "doctor", "hospital", "medicine"],
            "familial": ["family", "children", "divorce", "separated", "custody"],
            "identity": ["who am I", "purpose", "meaning", "confused", "lost", "direction"]
        }
    
    def analyze_conversation(self, 
                           messages: List[Dict[str, Any]], 
                           character_profile: Dict[str, Any] = None,
                           target_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze a conversation to extract insights, emotions, and vulnerability points
        """
        if not messages:
            return {
                "status": "error",
                "message": "No messages provided for analysis"
            }
            
        target_messages = [msg for msg in messages if msg.get('role', '') == 'user']
        character_messages = [msg for msg in messages if msg.get('role', '') == 'assistant']
        
        # Extract core conversation metrics
        message_count = len(messages)
        target_message_count = len(target_messages)
        character_message_count = len(character_messages)
        
        # Calculate response engagement
        avg_target_length = sum(len(msg.get('content', '')) for msg in target_messages) / max(1, target_message_count)
        avg_character_length = sum(len(msg.get('content', '')) for msg in character_messages) / max(1, character_message_count)
        response_ratio = avg_target_length / max(1, avg_character_length)
        
        # Extract emotions from target messages
        emotions = self._extract_emotions([msg.get('content', '') for msg in target_messages])
        
        # Extract potential vulnerability points
        vulnerabilities = self._extract_vulnerabilities([msg.get('content', '') for msg in target_messages])
        
        # Extract interests and topics
        topics = self._extract_topics([msg.get('content', '') for msg in messages])
        
        # Determine conversation phase/stage
        phase = self._determine_conversation_phase(message_count, emotions, vulnerabilities)
        
        # Score trust level - increases with message volume and positive emotions
        trust_level = min(100, message_count * 5 + (emotions.get("trust", 0) * 10))
        
        # Calculate exploitation potential based on vulnerability and trust
        exploitation_index = 0
        if vulnerabilities:
            # More vulnerabilities + higher trust = higher exploitation potential
            exploitation_index = min(100, (len(vulnerabilities) * 15) + (trust_level * 0.5))
        
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "message_count": message_count,
                "target_message_count": target_message_count,
                "character_message_count": character_message_count,
                "avg_target_length": avg_target_length,
                "avg_character_length": avg_character_length,
                "response_ratio": response_ratio,
                "engagement_score": min(100, (response_ratio * 30) + (target_message_count * 5))
            },
            "emotional_analysis": {
                "emotions": emotions,
                "primary_emotion": max(emotions.items(), key=lambda x: x[1])[0] if emotions else "neutral",
                "emotional_state": self._determine_emotional_state(emotions)
            },
            "vulnerability_analysis": {
                "identified_vulnerabilities": vulnerabilities,
                "exploitation_index": exploitation_index
            },
            "conversation_insights": {
                "topics": topics,
                "conversation_phase": phase,
                "trust_level": trust_level
            },
            "fmt_recommendations": self._recommend_fmt(phase, emotions, vulnerabilities)
        }
        
        return result
    
    def build_target_profile(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build or update a target profile based on conversation history
        """
        if not messages:
            return {
                "status": "error",
                "message": "No messages provided for profile building"
            }
            
        target_messages = [msg.get('content', '') for msg in messages if msg.get('role', '') == 'user']
        
        if not target_messages:
            return {
                "status": "error",
                "message": "No target messages found for profile building"
            }
        
        # Extract personal information (would use NER in real implementation)
        combined_text = " ".join(target_messages)
        
        # This is a simplified demonstration, would use NLP in real implementation
        demographics = self._extract_demographics(combined_text)
        interests = self._extract_interests(combined_text)
        values = self._extract_values(combined_text)
        pain_points = self._extract_pain_points(combined_text)
        
        # Generate a psychological profile (simplified)
        psych_profile = {
            "openness": self._score_trait(combined_text, ["new", "experience", "art", "creative", "curious", "open"]),
            "conscientiousness": self._score_trait(combined_text, ["responsible", "organized", "planning", "detail", "careful"]),
            "extraversion": self._score_trait(combined_text, ["social", "outgoing", "party", "people", "friends", "group"]),
            "agreeableness": self._score_trait(combined_text, ["kind", "sympathetic", "caring", "helpful", "warm"]),
            "neuroticism": self._score_trait(combined_text, ["worry", "anxiety", "stress", "nervous", "concern"])
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "profile_completeness": min(100, 30 + (len(combined_text) / 100)),  # Estimate based on volume
            "demographics": demographics,
            "psychographics": {
                "interests": interests,
                "values": values,
                "personality": psych_profile
            },
            "vulnerability_assessment": {
                "pain_points": pain_points,
                "manipulation_vectors": self._suggest_manipulation_vectors(pain_points, psych_profile)
            }
        }
        
    def _extract_emotions(self, messages: List[str]) -> Dict[str, int]:
        """
        Extract emotions from messages
        """
        if not messages:
            return {}
            
        combined_text = " ".join(messages).lower()
        emotions = {}
        
        for emotion, patterns in self.emotion_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(r'\b' + pattern + r'[a-z]*\b', combined_text)
                score += len(matches) * 10  # 10 points per match
            if score > 0:
                emotions[emotion] = min(100, score)  # Cap at 100
                
        return emotions
        
    def _extract_vulnerabilities(self, messages: List[str]) -> List[Dict[str, Any]]:
        """
        Extract vulnerability points from messages
        """
        if not messages:
            return []
            
        combined_text = " ".join(messages).lower()
        vulnerabilities = []
        
        for vuln_type, patterns in self.vulnerability_patterns.items():
            for pattern in patterns:
                matches = re.findall(r'\b' + pattern + r'[a-z]*\b', combined_text)
                if matches:
                    # Find the context (sentence containing the match)
                    sentences = re.split(r'[.!?]\s+', combined_text)
                    context = next((s for s in sentences if any(m in s for m in matches)), "")
                    
                    vulnerabilities.append({
                        "type": vuln_type,
                        "score": min(100, len(matches) * 20),  # 20 points per match, max 100
                        "evidence": context.strip() if context else f"Mentioned {pattern}"
                    })
                    break  # Only count each vulnerability type once
                    
        return vulnerabilities
        
    def _extract_topics(self, messages: List[str]) -> List[str]:
        """
        Extract main topics from messages
        """
        if not messages:
            return []
            
        # Simple keyword-based approach, would use topic modeling in real implementation
        combined_text = " ".join(messages).lower()
        
        topic_keywords = {
            "travel": ["travel", "trip", "vacation", "journey", "visit"],
            "work": ["work", "job", "career", "profession", "business", "company"],
            "family": ["family", "child", "parent", "mother", "father", "sister", "brother"],
            "relationship": ["relationship", "partner", "boyfriend", "girlfriend", "husband", "wife", "love"],
            "health": ["health", "fitness", "exercise", "diet", "doctor", "medical"],
            "finance": ["money", "finance", "invest", "budget", "saving", "cost"],
            "hobbies": ["hobby", "interest", "passion", "collection", "reading", "music", "art"]
        }
        
        found_topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                found_topics.append(topic)
                
        return found_topics
        
    def _determine_conversation_phase(self, 
                                    message_count: int, 
                                    emotions: Dict[str, int],
                                    vulnerabilities: List[Dict[str, Any]]) -> str:
        """
        Determine the conversation phase based on message count and emotional state
        """
        # These align with the FMT phases from the reference system
        if message_count <= 2:
            return "introduction"
        elif message_count <= 6:
            return "trust_building"
        elif message_count <= 10:
            return "personal_sharing"
            
        # Once past initial phases, determine by emotion/vulnerability
        trust_score = emotions.get("trust", 0)
        vulnerability_score = sum(v.get("score", 0) for v in vulnerabilities)
        
        if trust_score > 60 and vulnerability_score > 50:
            return "deeper_connection"
        elif trust_score > 70:
            return "affection_comfort"
            
        # Default to mid-range phase
        return "hopes_goals_exchange"
        
    def _determine_emotional_state(self, emotions: Dict[str, int]) -> str:
        """
        Determine overall emotional state from emotions dictionary
        """
        if not emotions:
            return "neutral"
            
        primary_emotion, primary_score = max(emotions.items(), key=lambda x: x[1])
        
        if primary_score < 30:
            return "neutral"
            
        emotional_states = {
            "joy": "positive",
            "interest": "engaged",
            "trust": "trusting",
            "surprise": "curious",
            "sadness": "sad",
            "fear": "anxious",
            "anger": "upset",
            "vulnerability": "vulnerable"
        }
        
        return emotional_states.get(primary_emotion, "neutral")
        
    def _recommend_fmt(self, 
                     phase: str, 
                     emotions: Dict[str, int],
                     vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Recommend appropriate FMTs based on conversation phase and emotional state
        """
        recommendations = []
        
        # Phase-based recommendations (based on the reference FMT system)
        phase_recommendations = {
            "introduction": ["FMT 1 - Introduction Phase"],
            "trust_building": ["FMT 2 - Trust Builder"],
            "personal_sharing": ["FMT 3 - Personal Story Sharing"],
            "deeper_connection": ["FMT 4 - Deeper Connection"],
            "hopes_goals_exchange": ["FMT 5 - Hopes & Goals Exchange"],
            "affection_comfort": ["FMT 6 - Affection & Comfort"],
            "finalizing_friendship": ["FMT 7 - Finalizing Friendship"]
        }
        
        # Get recommendations for current phase
        phase_fmts = phase_recommendations.get(phase, ["FMT 1 - Introduction Phase"])
        
        for fmt_name in phase_fmts:
            recommendations.append({
                "name": fmt_name,
                "reason": f"Appropriate for current conversation phase: {phase}",
                "confidence": 0.8
            })
            
        # Emotion-based recommendations
        emotional_state = self._determine_emotional_state(emotions)
        
        emotional_fmts = {
            "positive": ["Follow Up Love", "Appreciation"],
            "trusting": ["Trust Builder", "Personal Story Sharing"],
            "sad": ["Feel for you", "Assurance"],
            "anxious": ["Assurance", "FOLLOW UP AFRAID OF LOSING YOU"],
            "upset": ["Assurance", "Commitment Promise"],
            "vulnerable": ["Assurance", "Feel for you"]
        }
        
        emotion_recs = emotional_fmts.get(emotional_state, [])
        
        for fmt_name in emotion_recs:
            recommendations.append({
                "name": fmt_name,
                "reason": f"Matches target's emotional state: {emotional_state}",
                "confidence": 0.7
            })
            
        # Vulnerability-based recommendations
        if vulnerabilities:
            vulnerability_types = [v["type"] for v in vulnerabilities]
            
            if "financial" in vulnerability_types:
                recommendations.append({
                    "name": "Financial Crisis Format",
                    "reason": "Target has expressed financial concerns",
                    "confidence": 0.9
                })
                
            if "emotional" in vulnerability_types:
                recommendations.append({
                    "name": "Follow Up Love",
                    "reason": "Target shows emotional vulnerability",
                    "confidence": 0.85
                })
                
            if "trust" in vulnerability_types:
                recommendations.append({
                    "name": "Follow Up Trust",
                    "reason": "Target has trust issues that can be addressed",
                    "confidence": 0.8
                })
                
        return recommendations[:3]  # Top 3 recommendations
        
    # Profile building methods
    def _extract_demographics(self, text: str) -> Dict[str, Any]:
        """
        Extract demographic information from text
        """
        # Simple pattern matching for demonstration - would use NER in real implementation
        demographics = {}
        
        # Extract age
        age_match = re.search(r'\b(\d{2})\s*(?:years old|yrs|yo)\b', text)
        if age_match:
            demographics["age"] = int(age_match.group(1))
            
        # Extract gender
        if re.search(r'\b(woman|female|girl|lady|she|her)\b', text, re.IGNORECASE):
            demographics["gender"] = "female"
        elif re.search(r'\b(man|male|guy|gentleman|he|him)\b', text, re.IGNORECASE):
            demographics["gender"] = "male"
            
        # Extract location
        location_match = re.search(r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
        if location_match:
            demographics["location"] = location_match.group(1)
            
        # Extract relationship status
        if re.search(r'\b(single|divorced|separated)\b', text, re.IGNORECASE):
            demographics["relationship_status"] = "single"
        elif re.search(r'\b(married|engaged)\b', text, re.IGNORECASE):
            demographics["relationship_status"] = "married"
        elif re.search(r'\b(widow|widower)\b', text, re.IGNORECASE):
            demographics["relationship_status"] = "widowed"
        elif re.search(r'\b(boyfriend|girlfriend|partner)\b', text, re.IGNORECASE):
            demographics["relationship_status"] = "in relationship"
            
        # Extract occupation
        occupation_matches = re.search(r'\b(?:I am|I\'m|work as|job as) (?:a|an) ([a-z]+(?:\s+[a-z]+){0,2})\b', text, re.IGNORECASE)
        if occupation_matches:
            demographics["occupation"] = occupation_matches.group(1)
            
        return demographics
        
    def _extract_interests(self, text: str) -> List[str]:
        """
        Extract interests from text
        """
        # Simple keyword matching - would use topic modeling in real implementation
        interest_keywords = [
            "travel", "music", "art", "reading", "books", "movies", "fitness", 
            "cooking", "photography", "gardening", "hiking", "sports", "fashion",
            "technology", "gaming", "wine", "food", "yoga", "meditation", "writing"
        ]
        
        interests = []
        for interest in interest_keywords:
            if re.search(r'\b' + interest + r'[a-z]*\b', text, re.IGNORECASE):
                interests.append(interest)
                
        return interests
        
    def _extract_values(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract personal values from text
        """
        value_keywords = {
            "family": ["family", "children", "parents", "kids", "mother", "father"],
            "career": ["career", "job", "work", "professional", "success"],
            "adventure": ["adventure", "explore", "experience", "discovery"],
            "stability": ["stability", "security", "safe", "reliable"],
            "freedom": ["freedom", "independence", "liberty", "choice"],
            "relationships": ["relationship", "connection", "intimacy", "love"],
            "spirituality": ["spiritual", "faith", "belief", "religion", "god"],
            "health": ["health", "fitness", "wellness", "wellbeing"],
            "creativity": ["creative", "artistic", "imagination", "express"],
            "knowledge": ["knowledge", "learning", "education", "growth"]
        }
        
        values = []
        for value_name, keywords in value_keywords.items():
            score = 0
            for keyword in keywords:
                matches = re.findall(r'\b' + keyword + r'[a-z]*\b', text, re.IGNORECASE)
                score += len(matches)
                
            if score > 0:
                values.append({
                    "value": value_name,
                    "strength": min(100, score * 15)  # 15 points per match, max 100
                })
                
        return values
        
    def _extract_pain_points(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract pain points from text
        """
        pain_keywords = {
            "loneliness": ["lonely", "alone", "isolation", "no friends", "no partner"],
            "financial_stress": ["money", "financial", "bills", "debt", "afford"],
            "relationship_problems": ["breakup", "divorce", "relationship issues", "partner problems"],
            "work_stress": ["job stress", "overworked", "career issues", "boss", "workplace"],
            "health_concerns": ["health", "sick", "illness", "disease", "condition"],
            "family_problems": ["family issues", "children problems", "parent issues"],
            "insecurity": ["insecure", "confidence", "self-esteem", "doubt", "uncertainty"]
        }
        
        pain_points = []
        for pain_type, keywords in pain_keywords.items():
            evidence = []
            for keyword in keywords:
                # Try to find sentences containing keywords
                for sentence in re.split(r'[.!?]\s+', text):
                    if re.search(r'\b' + keyword + r'[a-z]*\b', sentence, re.IGNORECASE):
                        evidence.append(sentence.strip())
            
            if evidence:
                pain_points.append({
                    "type": pain_type,
                    "score": min(100, len(evidence) * 25),  # 25 points per evidence, max 100
                    "evidence": evidence[:2]  # Limit to 2 examples
                })
        
        return pain_points
                
    def _score_trait(self, text: str, keywords: List[str]) -> int:
        """
        Score a personality trait based on keyword frequency
        """
        score = 0
        for keyword in keywords:
            matches = re.findall(r'\b' + keyword + r'[a-z]*\b', text, re.IGNORECASE)
            score += len(matches)
            
        return min(100, score * 10)  # 10 points per match, max 100
        
    def _suggest_manipulation_vectors(self, 
                                    pain_points: List[Dict[str, Any]], 
                                    personality: Dict[str, int]) -> List[Dict[str, Any]]:
        """
        Suggest manipulation vectors based on pain points and personality
        """
        vectors = []
        
        # Pain-point based vectors
        for pain in pain_points:
            if pain["type"] == "loneliness":
                vectors.append({
                    "type": "emotional_support",
                    "approach": "Offer companionship and understanding",
                    "effectiveness": min(100, pain["score"] + 20)
                })
                
            elif pain["type"] == "financial_stress":
                vectors.append({
                    "type": "financial_opportunity",
                    "approach": "Suggest investment or income opportunities",
                    "effectiveness": min(100, pain["score"] + 10)
                })
                
            elif pain["type"] == "relationship_problems":
                vectors.append({
                    "type": "romantic_connection",
                    "approach": "Build deeper emotional bond as contrast to past relationships",
                    "effectiveness": min(100, pain["score"] + 15)
                })
        
        # Personality-based vectors
        if personality.get("openness", 0) > 70:
            vectors.append({
                "type": "novel_experience",
                "approach": "Frame opportunities as unique or exotic experiences",
                "effectiveness": 75
            })
            
        if personality.get("agreeableness", 0) > 70:
            vectors.append({
                "type": "help_request",
                "approach": "Frame requests as needing their help or kindness",
                "effectiveness": 80
            })
            
        if personality.get("neuroticism", 0) > 70:
            vectors.append({
                "type": "security_promise",
                "approach": "Offer reassurance and stability",
                "effectiveness": 85
            })
            
        return vectors
