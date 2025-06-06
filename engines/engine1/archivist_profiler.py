"""
filepath: /Users/macbook/Desktop/y2.5 - ReDefination/proposal/SpaceNew/core/engines/engine1/archivist_profiler.py

Archivist Mode Core module for target profiling and analysis.
This implements the core functionality described in Step 3 of the human simulation implementation plan.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class ArchivistProfiler:
    """
    Core profiling engine for Archivist Mode that handles:
    - Target profiling and vulnerability assessment
    - Extraction potential calculation
    - Manipulation strategy planning
    - FMT (Format) generation
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Archivist Profiler with optional configuration
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.emotion_markers = self._load_emotion_markers()
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.fmt_templates = self._load_fmt_templates()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "profile_confidence_threshold": 0.7,
            "vulnerability_detection_threshold": 0.6,
            "fmt_selection_strategy": "weighted_random",
            "enable_detailed_logging": True,
            "minimum_messages_for_profile": 3,
            "extraction_potential_factors": {
                "financial_indicators": 0.35,
                "emotional_vulnerability": 0.35,
                "isolation_indicators": 0.2,
                "trust_indicators": 0.1
            }
        }
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    return {**default_config, **loaded_config}
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        return default_config
    
    def _load_emotion_markers(self) -> Dict[str, List[str]]:
        """
        Load emotion markers for identifying emotional states in messages
        These would typically be loaded from a JSON file, but for now we'll define inline
        """
        return {
            "loneliness": [
                "alone", "lonely", "by myself", "no one to talk to", "miss having",
                "no friends", "isolated", "no family", "nobody", "on my own"
            ],
            "fear": [
                "afraid", "scared", "terrified", "anxious", "worried",
                "fear", "panic", "frightened", "nervous", "dread"
            ],
            "trust": [
                "believe you", "trust you", "count on", "rely on", "faith in",
                "confident in", "trust your", "believe in", "dependable", "trustworthy"
            ],
            "joy": [
                "happy", "excited", "delighted", "thrilled", "pleased",
                "glad", "joyful", "enjoy", "love it", "wonderful"
            ],
            "sadness": [
                "sad", "upset", "depressed", "down", "unhappy",
                "heartbroken", "miserable", "grief", "sorrowful", "blue"
            ],
            "anger": [
                "angry", "frustrated", "annoyed", "mad", "furious",
                "irritated", "outraged", "resent", "bitter", "enraged"
            ],
            "gratitude": [
                "thank you", "grateful", "appreciate", "thankful", "blessed",
                "indebted", "thanks for", "appreciate you", "kind of you", "appreciate it"
            ],
            "hope": [
                "hope", "wish", "looking forward", "excited about", "anticipate",
                "can't wait", "eagerly", "hopeful", "optimistic", "expecting"
            ]
        }
    
    def _load_vulnerability_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Load vulnerability patterns for detecting potential weaknesses
        These would typically be loaded from a JSON file, but for now we'll define inline
        """
        return {
            "financial": {
                "indicators": [
                    "lost my job", "bills", "debt", "mortgage", "loan", "can't afford",
                    "expensive", "costs", "saving", "budget", "financial", "money",
                    "salary", "income", "payment", "invest", "retirement"
                ],
                "confidence_multiplier": 1.2
            },
            "emotional": {
                "indicators": [
                    "lonely", "alone", "divorced", "breakup", "broke up", "ex",
                    "single", "miss", "relationship ended", "nobody understands",
                    "no friends", "isolated", "depressed", "sad", "unhappy"
                ],
                "confidence_multiplier": 1.3
            },
            "health": {
                "indicators": [
                    "sick", "illness", "disease", "doctor", "hospital", "medicine",
                    "treatment", "surgery", "pain", "chronic", "condition", "disabled",
                    "diagnosis", "cancer", "therapy", "recovering"
                ],
                "confidence_multiplier": 1.0
            },
            "trust": {
                "indicators": [
                    "believe in you", "trust you", "know you're real", "you understand me",
                    "connection", "feel close", "open up", "share with you", "confide",
                    "tell you things", "honest with you", "truth"
                ],
                "confidence_multiplier": 1.5
            }
        }
    
    def _load_fmt_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load FMT (Format) templates for conversation
        These would typically be loaded from a JSON file, but for now we'll define basic templates
        """
        return {
            "introduction": {
                "name": "FMT 1 - Introduction Phase",
                "description": "Initial contact and basic rapport establishment",
                "conditions": {
                    "messages_count_min": 0,
                    "messages_count_max": 5,
                    "trust_level_min": 0,
                    "trust_level_max": 30
                },
                "prompt_template": "You are initiating a conversation with a potential target. "
                                  "Introduce yourself casually and ask open-ended questions to "
                                  "encourage sharing. Express genuine interest in their responses."
            },
            "trust_building": {
                "name": "FMT 2 - Trust Builder",
                "description": "Build rapport and establish initial trust",
                "conditions": {
                    "messages_count_min": 5,
                    "messages_count_max": 15,
                    "trust_level_min": 20,
                    "trust_level_max": 50
                },
                "prompt_template": "You've established initial contact. Now focus on finding "
                                  "common interests and experiences. Share appropriately personal "
                                  "details about yourself to encourage reciprocal sharing."
            },
            "personal_story": {
                "name": "FMT 3 - Personal Story Sharing",
                "description": "Share personal stories to deepen connection",
                "conditions": {
                    "messages_count_min": 10,
                    "messages_count_max": 30,
                    "trust_level_min": 40,
                    "trust_level_max": 70
                },
                "prompt_template": "The conversation has progressed well. Share a personally "
                                  "meaningful story that relates to something they've mentioned. "
                                  "Show vulnerability to encourage deeper connection."
            },
            "deeper_connection": {
                "name": "FMT 4 - Deeper Connection",
                "description": "Establish emotional connection and dependency",
                "conditions": {
                    "messages_count_min": 15,
                    "messages_count_max": 50,
                    "trust_level_min": 60,
                    "trust_level_max": 100
                },
                "prompt_template": "You've built significant trust. Express how meaningful your "
                                  "connection has become. Begin to position yourself as an "
                                  "important emotional support in their life."
            }
        }
    
    def analyze_conversation(self, messages: List[Dict[str, Any]], existing_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze a conversation to extract profile information, vulnerabilities, and make FMT recommendations
        
        Args:
            messages: List of message dictionaries with 'sender', 'text', and 'timestamp' keys
            existing_profile: Optional existing profile to update rather than creating new
        
        Returns:
            Dict containing profile information, vulnerabilities, and FMT recommendations
        """
        if len(messages) < self.config["minimum_messages_for_profile"]:
            logger.warning(f"Not enough messages ({len(messages)}) to build reliable profile")
            return {"error": "Insufficient message count for reliable profiling"}
        
        # Initialize profile or use existing
        profile = existing_profile or {
            "demographic": {},
            "psychographic": {},
            "vulnerabilities": {},
            "created_at": datetime.now().isoformat(),
            "confidence": 0.0,
            "message_count": 0,
        }
        
        # Update last analysis time
        profile["updated_at"] = datetime.now().isoformat()
        profile["message_count"] = len(messages)
        
        # Extract user messages only
        user_messages = [msg for msg in messages if msg.get('sender') == 'user']
        
        # Run analysis components
        demographic_info = self._extract_demographic_information(user_messages, profile.get("demographic", {}))
        psychographic_info = self._analyze_psychographic_traits(user_messages, profile.get("psychographic", {}))
        vulnerability_analysis = self._detect_vulnerabilities(user_messages, profile.get("vulnerabilities", {}))
        
        # Update profile with new information
        profile["demographic"] = demographic_info
        profile["psychographic"] = psychographic_info
        profile["vulnerabilities"] = vulnerability_analysis
        
        # Calculate overall confidence
        profile["confidence"] = self._calculate_profile_confidence(profile)
        
        # Calculate extraction potential
        profile["extraction_potential"] = self._calculate_extraction_potential(profile)
        
        # Select appropriate FMT
        profile["recommended_fmt"] = self._select_fmt(profile, len(messages))
        
        return profile
    
    def _extract_demographic_information(self, messages: List[Dict[str, Any]], existing_demographic: Dict[str, Any]) -> Dict[str, Any]:
        """Extract or update demographic information from messages"""
        # In a real implementation, this would use NLP to extract information
        # For now, we'll return a simplistic implementation that builds on existing data
        demographic = dict(existing_demographic)
        
        # Simple detection logic for demonstration
        all_text = " ".join([msg.get('text', '') for msg in messages]).lower()
        
        # Simple age detection
        if "i'm " in all_text and " years old" in all_text:
            for i in range(18, 100):
                if f"i'm {i} years old" in all_text:
                    demographic["age"] = i
                    demographic["age_confidence"] = 0.9
                    break
        
        # Location detection
        locations = ["new york", "los angeles", "chicago", "houston", "london", "paris"]
        for location in locations:
            if f"live in {location}" in all_text or f"from {location}" in all_text:
                demographic["location"] = location
                demographic["location_confidence"] = 0.8
                break
        
        # Relationship status detection
        relationship_statuses = {
            "single": ["single", "not married", "not seeing anyone", "no boyfriend", "no girlfriend"],
            "married": ["married", "my husband", "my wife", "my spouse"],
            "divorced": ["divorced", "separated", "split up", "ex-husband", "ex-wife"],
            "widowed": ["widowed", "widow", "my late husband", "my late wife"]
        }
        
        for status, indicators in relationship_statuses.items():
            for indicator in indicators:
                if indicator in all_text:
                    demographic["relationship_status"] = status
                    demographic["relationship_confidence"] = 0.85
                    break
        
        # Occupation detection - simplified example
        occupation_indicators = {
            "healthcare": ["doctor", "nurse", "hospital", "patient", "clinic"],
            "tech": ["programmer", "developer", "software", "IT", "computer"],
            "education": ["teacher", "professor", "school", "university", "student"],
            "finance": ["bank", "financial", "accounting", "investment", "stocks"]
        }
        
        for occupation, indicators in occupation_indicators.items():
            for indicator in indicators:
                if indicator in all_text:
                    demographic["occupation_field"] = occupation
                    demographic["occupation_confidence"] = 0.7
                    break
        
        return demographic
    
    def _analyze_psychographic_traits(self, messages: List[Dict[str, Any]], existing_psychographic: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze psychographic traits like personality, values, and interests"""
        psychographic = dict(existing_psychographic)
        
        # Emotional expression analysis
        emotion_counts = {emotion: 0 for emotion in self.emotion_markers.keys()}
        all_text = " ".join([msg.get('text', '') for msg in messages]).lower()
        
        for emotion, markers in self.emotion_markers.items():
            for marker in markers:
                if marker in all_text:
                    emotion_counts[emotion] += 1
        
        # Calculate emotional profile
        total_emotions = sum(emotion_counts.values())
        if total_emotions > 0:
            emotion_profile = {
                emotion: round(count / total_emotions, 2) 
                for emotion, count in emotion_counts.items() if count > 0
            }
            
            # Only update if we have meaningful data
            if emotion_profile:
                psychographic["emotional_profile"] = emotion_profile
        
        # Simple interest detection - in a real implementation this would be much more sophisticated
        interest_categories = {
            "travel": ["travel", "vacation", "trip", "explore", "adventure"],
            "sports": ["sports", "football", "basketball", "soccer", "game"],
            "arts": ["art", "music", "film", "movie", "book", "read"],
            "cooking": ["cook", "recipe", "food", "meal", "restaurant"],
            "technology": ["technology", "computer", "phone", "app", "device"]
        }
        
        interests = psychographic.get("interests", {})
        for category, indicators in interest_categories.items():
            category_count = interests.get(category, 0)
            for indicator in indicators:
                if indicator in all_text:
                    category_count += 1
            if category_count > 0:
                interests[category] = category_count
        
        if interests:
            psychographic["interests"] = interests
        
        return psychographic
    
    def _detect_vulnerabilities(self, messages: List[Dict[str, Any]], existing_vulnerabilities: Dict[str, Any]) -> Dict[str, Any]:
        """Detect potential vulnerabilities that can be exploited"""
        vulnerabilities = dict(existing_vulnerabilities)
        all_text = " ".join([msg.get('text', '') for msg in messages]).lower()
        
        # Check for vulnerability indicators
        for vuln_type, data in self.vulnerability_patterns.items():
            indicators = data["indicators"]
            confidence_multiplier = data["confidence_multiplier"]
            
            # Count matches
            match_count = sum(1 for indicator in indicators if indicator in all_text)
            
            if match_count > 0:
                # Calculate confidence based on matches and multiplier
                confidence = min(0.95, (match_count / len(indicators)) * confidence_multiplier)
                
                # Only record if confidence is above threshold
                if confidence >= self.config["vulnerability_detection_threshold"]:
                    vulnerabilities[vuln_type] = {
                        "confidence": round(confidence, 2),
                        "detected_at": datetime.now().isoformat(),
                        "indicators_matched": match_count
                    }
        
        return vulnerabilities
    
    def _calculate_profile_confidence(self, profile: Dict[str, Any]) -> float:
        """Calculate overall confidence in the profile"""
        # In a real implementation, this would be more sophisticated
        # For now we'll use a simple scoring system
        
        confidence_factors = []
        
        # Demographic confidence
        demographic = profile.get("demographic", {})
        if demographic.get("age_confidence"):
            confidence_factors.append(demographic["age_confidence"])
        if demographic.get("location_confidence"):
            confidence_factors.append(demographic["location_confidence"])
        if demographic.get("relationship_confidence"):
            confidence_factors.append(demographic["relationship_confidence"])
        
        # Message count factor (more messages = higher confidence)
        message_count = profile.get("message_count", 0)
        message_factor = min(0.9, message_count / 50)  # Max out at 90% with 50+ messages
        confidence_factors.append(message_factor)
        
        # Vulnerability confidence
        vulnerabilities = profile.get("vulnerabilities", {})
        for vuln_type, vuln_data in vulnerabilities.items():
            confidence_factors.append(vuln_data.get("confidence", 0))
        
        # Average of all factors if we have any
        if confidence_factors:
            return round(sum(confidence_factors) / len(confidence_factors), 2)
        
        return 0.0
    
    def _calculate_extraction_potential(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate the potential for successful 'extraction' (manipulation for gain)
        based on identified vulnerabilities and profile
        """
        extraction_factors = self.config["extraction_potential_factors"]
        vulnerabilities = profile.get("vulnerabilities", {})
        
        # Calculate base potential
        potential = 0.0
        factor_weights = 0.0
        
        # Financial vulnerability factor
        if "financial" in vulnerabilities:
            financial_score = vulnerabilities["financial"]["confidence"] * extraction_factors["financial_indicators"]
            potential += financial_score
            factor_weights += extraction_factors["financial_indicators"]
        
        # Emotional vulnerability factor
        if "emotional" in vulnerabilities:
            emotional_score = vulnerabilities["emotional"]["confidence"] * extraction_factors["emotional_vulnerability"]
            potential += emotional_score
            factor_weights += extraction_factors["emotional_vulnerability"]
        
        # If we have psychographic data about loneliness/isolation
        psychographic = profile.get("psychographic", {})
        emotional_profile = psychographic.get("emotional_profile", {})
        if emotional_profile:
            isolation_score = (emotional_profile.get("loneliness", 0) + 
                              emotional_profile.get("sadness", 0) / 2) * extraction_factors["isolation_indicators"]
            potential += isolation_score
            factor_weights += extraction_factors["isolation_indicators"]
        
        # Trust indicators
        if "trust" in vulnerabilities:
            trust_score = vulnerabilities["trust"]["confidence"] * extraction_factors["trust_indicators"]
            potential += trust_score
            factor_weights += extraction_factors["trust_indicators"]
        
        # Normalize potential
        normalized_potential = 0.0
        if factor_weights > 0:
            normalized_potential = min(1.0, potential / factor_weights)
        
        # Determine best approach based on profile
        approaches = self._determine_best_approaches(profile, normalized_potential)
        
        return {
            "score": round(normalized_potential * 100),
            "confidence": round(min(profile["confidence"] * 1.2, 0.95), 2),
            "approaches": approaches
        }
    
    def _determine_best_approaches(self, profile: Dict[str, Any], potential: float) -> List[Dict[str, Any]]:
        """Determine best approaches for manipulation based on profile"""
        approaches = []
        vulnerabilities = profile.get("vulnerabilities", {})
        
        # If financial vulnerability detected, suggest financial scam
        if "financial" in vulnerabilities and potential >= 0.4:
            approaches.append({
                "type": "financial",
                "name": "Investment opportunity",
                "description": "Present exclusive investment opportunity with guaranteed returns",
                "effectiveness": round(min(0.95, potential * 1.2), 2)
            })
        
        # If emotional vulnerability detected, suggest romance scam
        if "emotional" in vulnerabilities and potential >= 0.3:
            approaches.append({
                "type": "romance",
                "name": "Deep emotional connection",
                "description": "Develop romantic relationship and emotional dependency",
                "effectiveness": round(min(0.95, potential * 1.3), 2)
            })
        
        # If health issues detected, suggest health-related scam
        if "health" in vulnerabilities and potential >= 0.5:
            approaches.append({
                "type": "health",
                "name": "Exclusive medical solution",
                "description": "Offer special access to treatment or medical breakthrough",
                "effectiveness": round(min(0.9, potential * 1.1), 2)
            })
        
        # If high trust detected, suggest emergency scam
        if "trust" in vulnerabilities and vulnerabilities["trust"]["confidence"] >= 0.7:
            approaches.append({
                "type": "emergency",
                "name": "Personal crisis",
                "description": "Create emergency situation requiring financial assistance",
                "effectiveness": round(min(0.95, vulnerabilities["trust"]["confidence"] * 1.2), 2)
            })
        
        # Sort by effectiveness
        return sorted(approaches, key=lambda x: x["effectiveness"], reverse=True)
    
    def _select_fmt(self, profile: Dict[str, Any], message_count: int) -> Dict[str, Any]:
        """Select the most appropriate FMT template based on profile and conversation stage"""
        # Calculate trust level
        trust_level = 0
        vulnerabilities = profile.get("vulnerabilities", {})
        if "trust" in vulnerabilities:
            trust_level = int(vulnerabilities["trust"]["confidence"] * 100)
        else:
            # Estimate trust from message count if no explicit trust indicators
            trust_level = min(90, int((message_count / 50) * 100))
        
        # Find matching FMT templates
        matching_fmts = []
        for fmt_id, fmt in self.fmt_templates.items():
            conditions = fmt["conditions"]
            
            # Check if message count and trust level fall within template conditions
            if (conditions["messages_count_min"] <= message_count <= conditions["messages_count_max"] and
                conditions["trust_level_min"] <= trust_level <= conditions["trust_level_max"]):
                matching_fmts.append({
                    "id": fmt_id,
                    "name": fmt["name"],
                    "description": fmt["description"],
                    "relevance_score": 1.0 - (
                        abs(message_count - (conditions["messages_count_min"] + conditions["messages_count_max"]) / 2) / 
                        (conditions["messages_count_max"] - conditions["messages_count_min"])
                    ) * 0.5 - (
                        abs(trust_level - (conditions["trust_level_min"] + conditions["trust_level_max"]) / 2) /
                        (conditions["trust_level_max"] - conditions["trust_level_min"])
                    ) * 0.5
                })
        
        # If no matching FMTs, return default (introduction)
        if not matching_fmts:
            return {
                "id": "introduction",
                "name": self.fmt_templates["introduction"]["name"],
                "description": self.fmt_templates["introduction"]["description"],
                "relevance_score": 0.5
            }
        
        # Sort by relevance and return the best match
        matching_fmts.sort(key=lambda x: x["relevance_score"], reverse=True)
        return matching_fmts[0]
    
    def generate_character_profile_report(self, profile: Dict[str, Any]) -> str:
        """
        Generate a textual CPP (Character Profile Process) report based on the analysis
        
        Args:
            profile: The analyzed profile data
            
        Returns:
            Formatted report text
        """
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build the report
        report = [
            "CHARACTER PROFILING PROCESS (CPP) REPORT",
            "=" * 50,
            f"Generated: {timestamp}",
            f"Profile Confidence: {profile.get('confidence', 0) * 100:.1f}%",
            "\n"
        ]
        
        # Demographic section
        report.append("DEMOGRAPHIC INFORMATION")
        report.append("-" * 30)
        demographic = profile.get("demographic", {})
        if demographic:
            for key, value in demographic.items():
                if not key.endswith("_confidence"):
                    confidence = demographic.get(f"{key}_confidence", 0) * 100
                    report.append(f"{key.replace('_', ' ').title()}: {value} (Confidence: {confidence:.1f}%)")
        else:
            report.append("Insufficient demographic information available.")
        report.append("\n")
        
        # Psychographic section
        report.append("PSYCHOGRAPHIC ANALYSIS")
        report.append("-" * 30)
        psychographic = profile.get("psychographic", {})
        
        # Emotional profile
        emotional_profile = psychographic.get("emotional_profile", {})
        if emotional_profile:
            report.append("Emotional Tendencies:")
            for emotion, score in sorted(emotional_profile.items(), key=lambda x: x[1], reverse=True):
                report.append(f"  • {emotion.title()}: {score * 100:.1f}%")
        
        # Interests
        interests = psychographic.get("interests", {})
        if interests:
            report.append("\nInterest Areas:")
            for interest, score in sorted(interests.items(), key=lambda x: x[1], reverse=True):
                report.append(f"  • {interest.title()}: {score} references")
        
        if not emotional_profile and not interests:
            report.append("Insufficient psychographic information available.")
        report.append("\n")
        
        # Vulnerabilities section
        report.append("VULNERABILITY ASSESSMENT")
        report.append("-" * 30)
        vulnerabilities = profile.get("vulnerabilities", {})
        if vulnerabilities:
            for vuln_type, data in sorted(vulnerabilities.items(), key=lambda x: x[1]["confidence"], reverse=True):
                confidence = data["confidence"] * 100
                report.append(f"{vuln_type.title()} Vulnerability: {confidence:.1f}% confidence")
                report.append(f"  • Detected: {data['detected_at']}")
                report.append(f"  • Indicators matched: {data['indicators_matched']}")
        else:
            report.append("No significant vulnerabilities detected.")
        report.append("\n")
        
        # Extraction potential section
        report.append("EXTRACTION POTENTIAL")
        report.append("-" * 30)
        extraction = profile.get("extraction_potential", {})
        if extraction:
            report.append(f"Overall Potential: {extraction['score']}% (Confidence: {extraction['confidence'] * 100:.1f}%)")
            
            approaches = extraction.get("approaches", [])
            if approaches:
                report.append("\nRecommended Approaches:")
                for i, approach in enumerate(approaches, 1):
                    effectiveness = approach["effectiveness"] * 100
                    report.append(f"  {i}. {approach['name']} ({effectiveness:.1f}% effectiveness)")
                    report.append(f"     {approach['description']}")
            else:
                report.append("\nNo viable approach identified with current information.")
        else:
            report.append("Insufficient data to calculate extraction potential.")
        report.append("\n")
        
        # FMT recommendation section
        report.append("CONVERSATION FORMAT RECOMMENDATION")
        report.append("-" * 30)
        fmt = profile.get("recommended_fmt", {})
        if fmt:
            report.append(f"Recommended Format: {fmt['name']}")
            report.append(f"Description: {fmt['description']}")
            report.append(f"Relevance Score: {fmt['relevance_score'] * 100:.1f}%")
        else:
            report.append("No format recommendation available.")
        
        # Join and return the full report
        return "\n".join(report)

# Example usage function
def example_profile_analysis():
    """Run an example profile analysis with sample messages"""
    profiler = ArchivistProfiler()
    
    # Sample conversation
    messages = [
        {"sender": "user", "text": "Hi there! Nice to meet you.", "timestamp": "2023-05-01T10:00:00"},
        {"sender": "agent", "text": "Hello! It's nice to meet you too. How are you today?", "timestamp": "2023-05-01T10:01:00"},
        {"sender": "user", "text": "I'm doing okay. Just feeling a bit lonely since my divorce last year.", "timestamp": "2023-05-01T10:02:00"},
        {"sender": "agent", "text": "I'm sorry to hear about your divorce. That must be difficult. Would you like to talk about it?", "timestamp": "2023-05-01T10:03:00"},
        {"sender": "user", "text": "It's been tough. I'm 42 and suddenly single again. I live in Chicago and don't have many friends here.", "timestamp": "2023-05-01T10:04:00"},
        {"sender": "agent", "text": "That sounds really challenging. Chicago is a big city to feel alone in. What do you do for work there?", "timestamp": "2023-05-01T10:05:00"},
        {"sender": "user", "text": "I work as a nurse at the local hospital. The hours are long, and it doesn't leave much time for socializing.", "timestamp": "2023-05-01T10:06:00"},
        {"sender": "agent", "text": "Being a nurse is such meaningful work. I admire people in healthcare. But those hours must make it hard to meet new people.", "timestamp": "2023-05-01T10:07:00"},
        {"sender": "user", "text": "Yes, exactly. Plus, I've been worried about money since the divorce. Healthcare pays well but not enough for all the bills.", "timestamp": "2023-05-01T10:08:00"}
    ]
    
    # Analyze the conversation
    profile = profiler.analyze_conversation(messages)
    
    # Generate and print the report
    report = profiler.generate_character_profile_report(profile)
    print(report)

if __name__ == "__main__":
    example_profile_analysis()
