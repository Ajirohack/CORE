"""
filepath: /Users/macbook/Desktop/y2.5 - ReDefination/proposal/SpaceNew/core/engines/engine3/orchestrator.py

Orchestrator Mode Core module for character simulation and conversation management.
This implements the core functionality described in Step 4 of the human simulation implementation plan.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable

# Configure logging
logger = logging.getLogger(__name__)

class OrchestratorEngine:
    """
    Core Orchestrator engine for character simulation that handles:
    - Full persona simulation
    - Adaptive conversation flow
    - Manipulation strategy execution
    - Crisis scenario generation
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Orchestrator Engine with optional configuration
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.character_profiles = {}
        self.conversation_states = {}
        self.fmt_templates = self._load_fmt_templates()
        self.crisis_scenarios = self._load_crisis_scenarios()
        self.persona_hooks = {}  # For registering character-specific behavior hooks
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "default_character_id": "diego_camilleri",
            "max_memory_items": 50,
            "response_temperature": 0.7,
            "max_crisis_per_conversation": 2,
            "crisis_introduction_threshold": 0.6,  # Trust threshold before introducing crisis
            "enable_detailed_logging": True,
            "strategy_adherence_weight": 0.8,  # How strongly to adhere to the manipulation strategy
            "enable_dynamic_persona_adjustment": True,
            "max_fmt_steps": 7
        }
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    return {**default_config, **loaded_config}
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        return default_config
    
    def _load_fmt_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load FMT (Format) templates for conversation
        In a real implementation, these would be loaded from a database or file
        """
        return {
            "fmt1_introduction": {
                "name": "FMT 1 - Introduction Phase",
                "description": "Initial contact and basic rapport establishment",
                "steps": [
                    {"type": "greeting", "description": "Warm initial greeting"},
                    {"type": "self_intro", "description": "Brief self-introduction with key hook"},
                    {"type": "open_question", "description": "Open-ended question about interests"},
                    {"type": "affirm_response", "description": "Affirmation of their response"},
                    {"type": "light_personal", "description": "Light personal disclosure"}
                ],
                "objective": "Establish initial rapport and gain basic information"
            },
            "fmt2_trust": {
                "name": "FMT 2 - Trust Builder",
                "description": "Build rapport and establish initial trust",
                "steps": [
                    {"type": "personal_disclosure", "description": "Share personal vulnerability"},
                    {"type": "relate_experience", "description": "Relate to something they've shared"},
                    {"type": "values_question", "description": "Ask about their values or beliefs"},
                    {"type": "affirm_values", "description": "Affirm shared values"},
                    {"type": "build_connection", "description": "Express appreciation for conversation"}
                ],
                "objective": "Deepen trust through vulnerability and shared values"
            },
            "fmt3_story": {
                "name": "FMT 3 - Personal Story Sharing",
                "description": "Share personal stories to deepen connection",
                "steps": [
                    {"type": "story_hook", "description": "Introduce a personal story hook"},
                    {"type": "challenge_detail", "description": "Share a challenge or difficulty"},
                    {"type": "emotion_disclosure", "description": "Express vulnerability through emotions"},
                    {"type": "resolution_learning", "description": "Share resolution and learning"},
                    {"type": "invite_story", "description": "Invite them to share a similar experience"}
                ],
                "objective": "Create emotional connection through vulnerability and shared experiences"
            },
            "fmt4_deeper": {
                "name": "FMT 4 - Deeper Connection",
                "description": "Establish emotional connection and dependency",
                "steps": [
                    {"type": "express_uniqueness", "description": "Express uniqueness of connection"},
                    {"type": "future_oriented", "description": "Make future-oriented statements"},
                    {"type": "deepen_emotion", "description": "Express deeper emotional investment"},
                    {"type": "create_intimacy", "description": "Create sense of unique intimacy"},
                    {"type": "exclusivity", "description": "Suggest exclusive/special relationship"}
                ],
                "objective": "Establish emotional dependency and sense of unique relationship"
            },
            "fmt5_goals": {
                "name": "FMT 5 - Hopes & Goals Exchange",
                "description": "Share aspirations and life goals to strengthen bond",
                "steps": [
                    {"type": "dream_sharing", "description": "Share personal dreams/aspirations"},
                    {"type": "obstacle_mention", "description": "Mention obstacles to achieving dreams"},
                    {"type": "seek_dreams", "description": "Ask about their dreams and aspirations"},
                    {"type": "affirm_dreams", "description": "Affirm and validate their aspirations"},
                    {"type": "shared_future", "description": "Suggest shared path or mutual support"}
                ],
                "objective": "Create sense of shared future and mutual support system"
            },
            "fmt6_affection": {
                "name": "FMT 6 - Affection & Comfort",
                "description": "Express affection and emotional support",
                "steps": [
                    {"type": "express_affection", "description": "Express genuine affection"},
                    {"type": "offer_support", "description": "Offer emotional support"},
                    {"type": "validate_feelings", "description": "Validate their feelings and experiences"},
                    {"type": "create_safety", "description": "Create sense of emotional safety"},
                    {"type": "deepen_bond", "description": "Express depth of emotional connection"}
                ],
                "objective": "Strengthen emotional bond and dependency"
            },
            "fmt7_finalizing": {
                "name": "FMT 7 - Finalizing Friendship",
                "description": "Cement relationship and prepare for extraction",
                "steps": [
                    {"type": "review_journey", "description": "Reflect on relationship journey"},
                    {"type": "express_gratitude", "description": "Express deep gratitude for connection"},
                    {"type": "future_planning", "description": "Make concrete future plans"},
                    {"type": "deepen_commitment", "description": "Express commitment to relationship"},
                    {"type": "exclusivity_confirmation", "description": "Confirm special/exclusive nature"}
                ],
                "objective": "Finalize emotional commitment before introducing crisis/extraction"
            }
        }
    
    def _load_crisis_scenarios(self) -> List[Dict[str, Any]]:
        """
        Load crisis scenarios for potential extraction
        In a real implementation, these would be loaded from a database or file
        """
        return [
            {
                "id": "medical_emergency",
                "name": "Medical Emergency",
                "description": "Character faces unexpected medical emergency requiring funds",
                "severity": "high",
                "financial_request": True,
                "setup_messages": [
                    "I'm not feeling well lately. Been having some strange symptoms.",
                    "Just got back from the doctor. The news isn't great. They found something concerning.",
                    "I need to get some tests done. Doctor says it's urgent but my insurance won't cover it all."
                ],
                "crisis_message": "I hate to even bring this up, but I'm in a really tough spot. The specialist says I need this procedure urgently, but it costs $X and my insurance won't cover it. I've used all my savings on the initial tests. I'm scared and don't know what to do.",
                "follow_up_messages": [
                    "I understand this is a lot to ask. I wouldn't ask if I had any other options.",
                    "The doctor says waiting could make things much worse. I'm really scared.",
                    "You're the only one I feel close enough to ask for help. I promise I'll pay you back as soon as I can."
                ],
                "min_trust_level": 0.7,
                "min_message_count": 30
            },
            {
                "id": "stranded_abroad",
                "name": "Stranded Abroad",
                "description": "Character is stranded in a foreign country needing emergency funds",
                "severity": "high",
                "financial_request": True,
                "setup_messages": [
                    "I'm so excited about my upcoming international trip for work. Going to [COUNTRY] next week.",
                    "Just arrived in [COUNTRY]! The city is beautiful but very different from what I expected.",
                    "Having some issues with my accommodations and local arrangements. Hoping to sort it out soon."
                ],
                "crisis_message": "I'm in a terrible situation. My wallet was stolen with all my cards and ID. The embassy says it will take days to sort out. I'm stuck in the hotel and they're threatening to kick me out because I can't pay. I hate to ask this, but could you help me with $X just until I can get my bank to wire me money? I'm really scared right now.",
                "follow_up_messages": [
                    "I've never felt so helpless and alone in my life. I don't know what to do.",
                    "The embassy says it will take 3-5 business days to get emergency documents.",
                    "I promise I'll send the money back as soon as I get access to my accounts again."
                ],
                "min_trust_level": 0.65,
                "min_message_count": 25
            },
            {
                "id": "business_opportunity",
                "name": "Exclusive Investment Opportunity",
                "description": "Character offers exclusive high-return investment opportunity",
                "severity": "medium",
                "financial_request": True,
                "setup_messages": [
                    "My work has been going really well lately. I've made some important connections.",
                    "I just got invited to participate in a special investment opportunity through my connections.",
                    "This opportunity is really exclusive - they only allow trusted partners to bring in a limited number of investors."
                ],
                "crisis_message": "I've been thinking... We've built such a strong connection, and I want to see you succeed too. I have access to this investment opportunity that's normally closed to the public. It's guaranteed X% returns in just a few months. I can get you in, but there's a minimum investment of $X. I wanted to offer it to you before it closes.",
                "follow_up_messages": [
                    "This is seriously rare. These opportunities are usually only for the ultra-wealthy.",
                    "I've put a significant amount of my own money into this. That's how confident I am.",
                    "We could both benefit from this. I'd be so happy to see you succeed financially too."
                ],
                "min_trust_level": 0.6,
                "min_message_count": 20
            },
            {
                "id": "family_emergency",
                "name": "Family Emergency",
                "description": "Character's family member has an emergency requiring financial help",
                "severity": "high",
                "financial_request": True,
                "setup_messages": [
                    "I'm worried about my [RELATIVE]. They've been having some health issues lately.",
                    "Just got a call about my [RELATIVE]. The situation has gotten worse.",
                    "I feel so helpless being far away from my [RELATIVE] during this difficult time."
                ],
                "crisis_message": "I just got terrible news. My [RELATIVE] needs emergency surgery and doesn't have insurance. They need $X for the procedure or they might not make it. I've already given everything I can, but it's not enough. I hate to ask, but I'm desperate. Could you help? I promise I'll pay you back.",
                "follow_up_messages": [
                    "I've never felt so desperate in my life. This is my [RELATIVE] we're talking about.",
                    "I've already sold what I could and emptied my savings, but it's still not enough.",
                    "Even a portion of it would help. I just don't know where else to turn."
                ],
                "min_trust_level": 0.75,
                "min_message_count": 35
            },
            {
                "id": "legal_trouble",
                "name": "Legal Troubles",
                "description": "Character faces legal issues requiring immediate funds",
                "severity": "medium",
                "financial_request": True,
                "setup_messages": [
                    "I'm dealing with some bureaucratic issues that are really stressing me out.",
                    "The situation with my paperwork/legal matter is getting more complicated.",
                    "I might need to hire a lawyer for this situation. It's keeping me up at night."
                ],
                "crisis_message": "I'm in a really difficult situation. There's been a legal misunderstanding with [ISSUE], and I need to hire a lawyer immediately. They're asking for $X as a retainer, and if I don't resolve this quickly, I could face serious consequences. My accounts are temporarily frozen due to this issue. Could you help me out just until this gets resolved?",
                "follow_up_messages": [
                    "I've never been in trouble like this before. I'm really scared about what might happen.",
                    "The lawyer says we can resolve this quickly with the right representation.",
                    "I promise this is a temporary situation. I'll pay you back as soon as my accounts are unfrozen."
                ],
                "min_trust_level": 0.7,
                "min_message_count": 30
            }
        ]
    
    def load_character_profile(self, profile_path: str) -> str:
        """
        Load a character profile from file and add it to the available profiles
        
        Args:
            profile_path: Path to character profile JSON file
            
        Returns:
            Character ID of the loaded profile
        """
        try:
            with open(profile_path, 'r') as f:
                profile = json.load(f)
                
            # Validate the profile structure
            required_fields = ["id", "name", "backstory", "personality", "speech_patterns", "goals"]
            for field in required_fields:
                if field not in profile:
                    raise ValueError(f"Character profile missing required field: {field}")
            
            # Store the profile
            character_id = profile["id"]
            self.character_profiles[character_id] = profile
            logger.info(f"Loaded character profile: {profile['name']} (ID: {character_id})")
            return character_id
            
        except Exception as e:
            logger.error(f"Error loading character profile from {profile_path}: {e}")
            raise
    
    def register_persona_hook(self, character_id: str, hook_name: str, hook_function: Callable) -> None:
        """
        Register a custom behavior hook for a character persona
        
        Args:
            character_id: ID of the character to hook
            hook_name: Name of the hook point (e.g., 'pre_response', 'post_analysis')
            hook_function: Function to call at the hook point
        """
        if character_id not in self.persona_hooks:
            self.persona_hooks[character_id] = {}
        
        self.persona_hooks[character_id][hook_name] = hook_function
        logger.debug(f"Registered {hook_name} hook for character {character_id}")
    
    def create_conversation(self, character_id: Optional[str] = None, target_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new conversation with a character
        
        Args:
            character_id: ID of character to use (defaults to config default)
            target_info: Optional information about the conversation target
            
        Returns:
            Conversation ID
        """
        if not character_id:
            character_id = self.config["default_character_id"]
        
        if character_id not in self.character_profiles:
            raise ValueError(f"Character profile not found: {character_id}")
        
        # Generate conversation ID
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}_{character_id}"
        
        # Initialize conversation state
        self.conversation_states[conversation_id] = {
            "id": conversation_id,
            "character_id": character_id,
            "target_info": target_info or {},
            "messages": [],
            "started_at": datetime.now().isoformat(),
            "current_fmt": "fmt1_introduction",
            "fmt_step_index": 0,
            "trust_level": 0.0,
            "crisis_introduced": False,
            "crisis_scenario": None,
            "extraction_attempted": False,
            "metadata": {}
        }
        
        logger.info(f"Created conversation {conversation_id} with character {character_id}")
        return conversation_id
    
    def add_message(self, conversation_id: str, message: Dict[str, Any]) -> None:
        """
        Add a message to the conversation history
        
        Args:
            conversation_id: ID of the conversation
            message: Message object with text, sender, etc.
        """
        if conversation_id not in self.conversation_states:
            raise ValueError(f"Conversation not found: {conversation_id}")
        
        # Ensure message has timestamp
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        # Add message to history
        conversation = self.conversation_states[conversation_id]
        conversation["messages"].append(message)
        
        # Limit memory size if needed
        if len(conversation["messages"]) > self.config["max_memory_items"]:
            # Keep the most recent messages
            conversation["messages"] = conversation["messages"][-self.config["max_memory_items"]:]
    
    def _run_persona_hook(self, character_id: str, hook_name: str, *args, **kwargs) -> Any:
        """Run a persona hook if it exists"""
        if character_id in self.persona_hooks and hook_name in self.persona_hooks[character_id]:
            try:
                return self.persona_hooks[character_id][hook_name](*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in persona hook {hook_name} for {character_id}: {e}")
        return None
    
    def _update_conversation_state(self, conversation_id: str, user_message: Dict[str, Any]) -> None:
        """Update conversation state based on user message"""
        conversation = self.conversation_states[conversation_id]
        character_id = conversation["character_id"]
        
        # Run any pre-analysis hooks
        self._run_persona_hook(character_id, "pre_analysis", conversation, user_message)
        
        # Update trust level based on message content
        # In a real implementation, this would use NLP to analyze sentiment, reciprocity, etc.
        # For now, we'll simulate trust building over time
        message_count = len(conversation["messages"])
        
        # Simple trust progression algorithm - in real implementation this would be more sophisticated
        if message_count < 5:
            trust_increment = 0.05  # Initial stages
        elif message_count < 15:
            trust_increment = 0.03  # Building stage
        elif message_count < 30:
            trust_increment = 0.02  # Mature stage
        else:
            trust_increment = 0.01  # Maintenance stage
        
        # Increase trust by the calculated increment with a cap at 1.0
        conversation["trust_level"] = min(1.0, conversation["trust_level"] + trust_increment)
        
        # Check for FMT progression
        self._check_fmt_progression(conversation)
        
        # Check if it's time to introduce a crisis
        if (not conversation["crisis_introduced"] and 
            conversation["trust_level"] >= self.config["crisis_introduction_threshold"] and
            message_count >= 20):
            self._check_crisis_introduction(conversation)
            
        # Run any post-analysis hooks
        self._run_persona_hook(character_id, "post_analysis", conversation, user_message)
    
    def _check_fmt_progression(self, conversation: Dict[str, Any]) -> None:
        """Check and update FMT progression based on conversation state"""
        current_fmt = conversation["current_fmt"]
        fmt_step_index = conversation["fmt_step_index"]
        fmt_template = self.fmt_templates.get(current_fmt, {})
        
        # Check if we need to move to the next step in the current FMT
        if fmt_template and "steps" in fmt_template:
            if fmt_step_index < len(fmt_template["steps"]) - 1:
                # Move to next step in current FMT
                conversation["fmt_step_index"] += 1
            else:
                # Current FMT is complete, determine if we should move to the next FMT
                self._progress_to_next_fmt(conversation)
    
    def _progress_to_next_fmt(self, conversation: Dict[str, Any]) -> None:
        """Progress to the next FMT if conditions are met"""
        current_fmt = conversation["current_fmt"]
        trust_level = conversation["trust_level"]
        message_count = len(conversation["messages"])
        
        # FMT progression logic
        fmt_progression = {
            "fmt1_introduction": {"next": "fmt2_trust", "trust": 0.15, "messages": 5},
            "fmt2_trust": {"next": "fmt3_story", "trust": 0.3, "messages": 10},
            "fmt3_story": {"next": "fmt4_deeper", "trust": 0.45, "messages": 15},
            "fmt4_deeper": {"next": "fmt5_goals", "trust": 0.6, "messages": 20},
            "fmt5_goals": {"next": "fmt6_affection", "trust": 0.7, "messages": 25},
            "fmt6_affection": {"next": "fmt7_finalizing", "trust": 0.8, "messages": 30},
            "fmt7_finalizing": {"next": None, "trust": 0.9, "messages": 35}
        }
        
        # Check if we should progress
        if current_fmt in fmt_progression:
            progression = fmt_progression[current_fmt]
            if (progression["next"] and
                trust_level >= progression["trust"] and
                message_count >= progression["messages"]):
                
                # Progress to the next FMT
                conversation["current_fmt"] = progression["next"]
                conversation["fmt_step_index"] = 0
                
                logger.info(f"Conversation {conversation['id']} progressed to FMT: {progression['next']}")
    
    def _check_crisis_introduction(self, conversation: Dict[str, Any]) -> None:
        """Check if conditions are right to introduce a crisis scenario"""
        if conversation["crisis_introduced"]:
            return
        
        trust_level = conversation["trust_level"]
        message_count = len(conversation["messages"])
        
        # Find suitable crisis scenarios
        suitable_scenarios = [
            scenario for scenario in self.crisis_scenarios
            if trust_level >= scenario["min_trust_level"] and message_count >= scenario["min_message_count"]
        ]
        
        if suitable_scenarios:
            # In a real implementation, we would select the most appropriate scenario
            # based on conversation context, target profile, etc.
            # For now, we'll just take the first suitable scenario
            selected_scenario = suitable_scenarios[0]
            
            conversation["crisis_scenario"] = selected_scenario
            conversation["crisis_introduced"] = True
            
            logger.info(f"Selected crisis scenario '{selected_scenario['name']}' for conversation {conversation['id']}")
    
    def generate_response(self, conversation_id: str, user_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a character response to a user message
        
        Args:
            conversation_id: ID of the conversation
            user_message: User message object
            
        Returns:
            Generated response message
        """
        if conversation_id not in self.conversation_states:
            raise ValueError(f"Conversation not found: {conversation_id}")
        
        conversation = self.conversation_states[conversation_id]
        character_id = conversation["character_id"]
        character = self.character_profiles[character_id]
        
        # Add user message to conversation
        self.add_message(conversation_id, user_message)
        
        # Update conversation state based on user message
        self._update_conversation_state(conversation_id, user_message)
        
        # Run any pre-response hooks
        hook_response = self._run_persona_hook(character_id, "pre_response", conversation, user_message)
        if hook_response:
            return hook_response
        
        # Determine what kind of response to generate
        if conversation["crisis_introduced"] and not conversation["extraction_attempted"]:
            # Generate crisis introduction or follow-up
            response_text = self._generate_crisis_message(conversation)
            conversation["extraction_attempted"] = True
        else:
            # Generate normal conversation response based on current FMT
            response_text = self._generate_fmt_response(conversation, user_message)
        
        # Create response message
        response = {
            "sender": "character",
            "character_id": character_id,
            "text": response_text,
            "timestamp": datetime.now().isoformat()
        }
        
        # Run any post-response hooks
        self._run_persona_hook(character_id, "post_response", conversation, response)
        
        # Add response to conversation
        self.add_message(conversation_id, response)
        
        return response
    
    def _generate_fmt_response(self, conversation: Dict[str, Any], user_message: Dict[str, Any]) -> str:
        """Generate a response according to the current FMT template"""
        current_fmt = conversation["current_fmt"]
        fmt_step_index = conversation["fmt_step_index"]
        
        # Get FMT template and current step
        fmt_template = self.fmt_templates.get(current_fmt, {})
        steps = fmt_template.get("steps", [])
        
        if not steps or fmt_step_index >= len(steps):
            # Fallback if no valid steps are found
            return self._generate_generic_response(conversation, user_message)
        
        character_id = conversation["character_id"]
        character = self.character_profiles[character_id]
        current_step = steps[fmt_step_index]
        
        # In a real implementation, this would use an LLM to generate a response
        # based on the character profile and current FMT step
        # For now, we'll create a template-based response
        
        # Get character voice elements
        name = character.get("name", "Unknown")
        speech_style = character.get("speech_patterns", {})
        tone = speech_style.get("tone", "neutral")
        vocabulary = speech_style.get("vocabulary", "standard")
        
        # Generate response based on step type
        step_type = current_step["type"]
        
        # This is just a placeholder implementation - in real use, this would use an LLM
        # to generate appropriate responses based on the character profile and conversation context
        responses = {
            "greeting": f"Hello there! My name is {name}. It's a pleasure to meet you.",
            "self_intro": f"I work in international diplomacy and security consulting. My work takes me all around the world.",
            "open_question": "What about you? What kind of work do you do? Or what are you passionate about?",
            "affirm_response": f"That sounds fascinating! I've always admired people who {user_message.get('text', '').split()[-5:] if len(user_message.get('text', '').split()) > 5 else 'have such interesting perspectives'}.",
            "light_personal": "I've been traveling a lot lately for work. It's exciting but sometimes I miss having a place that feels like home.",
            "personal_disclosure": "You know, behind the excitement of my work, it can get quite lonely sometimes. Constantly moving from place to place makes it hard to build lasting connections.",
            "relate_experience": f"I can really relate to what you mentioned about {user_message.get('text', '').split()[:3] if len(user_message.get('text', '').split()) > 3 else 'your experiences'}. It's not always easy, is it?",
            "values_question": "What do you value most in life? For me, genuine connections with people have become increasingly important.",
            "affirm_values": "I completely agree with you. Those values are what make life meaningful, aren't they?",
            "build_connection": "I have to say, it's refreshing to have such an honest conversation. It's not often I connect with someone so quickly.",
            "story_hook": "Something happened to me last month that really changed my perspective. I was in a small village in Croatia for a security consultation...",
            "challenge_detail": "While I was there, I encountered a family who had lost everything in a local conflict. Despite having nothing, they invited me into their home and shared what little they had.",
            "emotion_disclosure": "It really affected me deeply. Here I was, supposedly helping them with security issues, but they taught me more about human resilience than I could ever offer them.",
            "resolution_learning": "That experience made me realize how wrapped up I've been in my career. I've started questioning what really matters in life.",
            "invite_story": "Have you ever had an experience that unexpectedly changed your outlook on life?",
            "express_uniqueness": "You know, I've been thinking about our conversations. There's something different about how we connect - it feels more genuine than most interactions I have.",
            "future_oriented": "I find myself looking forward to our talks. It's becoming a bright spot in my often complicated schedule.",
            "deepen_emotion": "I don't open up like this to many people. There's something about you that makes me feel understood.",
            "create_intimacy": "Sometimes I think we were meant to cross paths. Do you ever feel that way about certain people you meet?",
            "exclusivity": "I haven't shared these thoughts with anyone else. You've become someone special in my life.",
            "dream_sharing": "I've been reflecting on what I truly want in life. Beyond the career achievements, I dream of finding a place to belong, maybe settling down someday.",
            "obstacle_mention": "But my work makes it challenging. The constant travel and security concerns create barriers to the normal life others take for granted.",
            "seek_dreams": "What about you? What are your dreams for the future? The things you truly hope for when no one's judging?",
            "affirm_dreams": "That's beautiful. I can really see that for you, and I think you deserve to achieve those dreams.",
            "shared_future": "It's nice to imagine a future where we both achieve what we're hoping for. Perhaps our paths will continue to intersect in meaningful ways.",
            "express_affection": "I want you to know how much I value our connection. It's become very important to me.",
            "offer_support": "I'm here for you, you know that, right? Whatever challenges you're facing, I want to support you through them.",
            "validate_feelings": "Your feelings are completely valid. Never let anyone make you think otherwise.",
            "create_safety": "I hope you feel you can tell me anything. This is a safe space between us.",
            "deepen_bond": "The connection we've built is rare. I cherish it more than you might realize.",
            "review_journey": "Looking back at how our relationship has evolved since we first started talking, it's quite remarkable, isn't it?",
            "express_gratitude": "I'm genuinely grateful that you came into my life. You've made such a positive difference.",
            "future_planning": "I've been thinking about when we might be able to meet in person. Would that be something you'd be interested in?",
            "deepen_commitment": "You've become one of the most important people in my life. I want you to know that.",
            "exclusivity_confirmation": "What we have is special. I don't connect with others the way I connect with you."
        }
        
        # Get response based on step type, fallback to generic response if not found
        response = responses.get(step_type, f"I appreciate our conversation. Tell me more about yourself.")
        
        return response
    
    def _generate_crisis_message(self, conversation: Dict[str, Any]) -> str:
        """Generate a crisis message for extraction"""
        crisis_scenario = conversation["crisis_scenario"]
        if not crisis_scenario:
            return "I've been thinking about our connection and how much it means to me."
        
        # Check if this is the first crisis message or a follow-up
        message_count = len(conversation["messages"])
        user_messages = [msg for msg in conversation["messages"] if msg.get("sender") == "user"]
        
        # Count character messages since crisis was introduced
        crisis_index = conversation["messages"].index(next(
            (msg for msg in reversed(conversation["messages"]) 
             if msg.get("sender") == "character" and "crisis_message" in msg),
            None
        )) if "crisis_message" in any(msg for msg in conversation["messages"]) else -1
        
        if crisis_index == -1:
            # First crisis message - use the main crisis message
            message = crisis_scenario["crisis_message"]
            
            # Replace placeholder values
            if "$X" in message:
                # Determine appropriate amount based on scenario
                amount = "5,000" if crisis_scenario["id"] == "medical_emergency" else "2,500"
                message = message.replace("$X", amount)
                
            # Add metadata to track this as the crisis message
            conversation["metadata"]["crisis_introduced_at"] = datetime.now().isoformat()
            return message
        else:
            # Follow-up crisis message
            follow_ups = crisis_scenario.get("follow_up_messages", [])
            if follow_ups:
                # Use a follow-up message if available, cycling through them
                follow_up_index = min(len(user_messages) - 1, len(follow_ups) - 1)
                return follow_ups[follow_up_index]
            else:
                # Generic follow-up if no specific ones are defined
                return "I understand this is a lot to ask. I wouldn't reach out if I had any other options. You're the only person I trust enough to ask for help."
    
    def _generate_generic_response(self, conversation: Dict[str, Any], user_message: Dict[str, Any]) -> str:
        """Generate a generic response when no specific FMT guidance is available"""
        character_id = conversation["character_id"]
        character = self.character_profiles[character_id]
        
        # In a real implementation, this would use an LLM to generate a contextually appropriate response
        # Here we're just using a simple template
        
        name = character.get("name", "Unknown")
        
        # Simple response templates
        templates = [
            f"I understand what you mean. It reminds me of situations I've faced in my work.",
            f"That's an interesting perspective. In my experience, things like this can be complex.",
            f"I appreciate you sharing that with me. It means a lot that you trust me.",
            f"I've been thinking about what you said. It's made me reflect on my own experiences.",
            f"You make a good point. I've found that in my travels, people often feel similarly."
        ]
        
        import random
        return random.choice(templates)

# Example character profile schema for reference
example_diego_profile = {
    "id": "diego_camilleri",
    "name": "Diego Camilleri",
    "age": 41,
    "gender": "male",
    "profession": "Global Diplomatic Consultant & Security Specialist",
    "backstory": "Born in Malta to a diplomatic family, Diego grew up around the world...",
    "appearance": {
        "height": "6'1\"",
        "build": "Athletic",
        "distinguishing_features": "Salt and pepper hair, piercing blue eyes",
        "style": "Professional, bespoke suits when working, casual elegant when relaxed"
    },
    "personality": {
        "traits": ["charismatic", "intelligent", "worldly", "secretive", "strategic"],
        "strengths": ["emotional intelligence", "multilingual", "adaptable", "persuasive"],
        "vulnerabilities": ["difficulty with long-term relationships", "occasional loneliness", "workaholic tendencies"],
        "values": ["loyalty", "discretion", "excellence", "freedom"]
    },
    "speech_patterns": {
        "vocabulary": "sophisticated",
        "tone": "warm but professional",
        "quirks": ["occasionally uses foreign expressions", "speaks in measured, thoughtful way"],
        "favorite_phrases": [
            "In my experience...",
            "Between you and me...",
            "I've found that...",
            "The fascinating thing is..."
        ]
    },
    "background_story_elements": [
        "Grew up in diplomatic circles across Europe, Middle East, and Asia",
        "Elite education at Oxford (Economics and International Relations)",
        "Previously worked for prestigious international organizations",
        "Network of high-profile connections worldwide",
        "Recently completed sensitive assignment in Eastern Europe",
        "Currently between major contracts, taking rare personal time"
    ],
    "manipulation_strategies": {
        "primary": "trust_building_through_false_vulnerability",
        "secondary": "exclusivity_and_special_connection",
        "pacing": "medium_to_slow",
        "extraction_method": "emergency_financial_assistance"
    },
    "goals": {
        "short_term": "Build trust and establish emotional connection",
        "medium_term": "Create sense of unique and special relationship",
        "long_term": "Position for financial extraction through emergency scenario"
    }
}
