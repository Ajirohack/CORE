"""
Cognitive System scaffold for The Archivist
- Working memory, attention, knowledge, pattern detection, insight generation
- Event-driven processing model (Samantha-OS/AutoGPT/OLMo patterns)

References:
- AutoGPT: https://github.com/Significant-Gravitas/AutoGPT
- Samantha-OS: https://github.com/jesuscopado/samantha-os1
- OLMo: https://github.com/allenai/OLMo

This module is designed to be extended with direct integration of the above frameworks.
- For advanced memory, planning, and reasoning, see AutoGPT's memory and agent modules.
- For event-driven cognitive cycles, see Samantha-OS's event bus and cognitive loop.
- For LLM-based reasoning, see OLMo's API and inference engine.

TODO:
- Add adapters/wrappers for AutoGPT memory and task planning
- Add event loop hooks for Samantha-OS style event processing
- Add OLMo-based reasoning and insight generation
"""
import time
from typing import Any, Dict, List, Optional
from core.enhanced_event_bus import EventBus
from core.unified_storage import UnifiedStorageLayer
from core.llm_council.crewai_council import CrewAICouncil
from datetime import datetime

class WorkingMemory:
    def __init__(self):
        self.data = {}
    def set(self, key, value):
        self.data[key] = value
    def get(self, key):
        return self.data.get(key)

class AttentionManager:
    def __init__(self):
        self.focus = None
    def set_focus(self, focus):
        self.focus = focus
    def get_focus(self):
        return self.focus

class KnowledgeBase:
    def __init__(self):
        self.knowledge = {}
    def add(self, key, value):
        self.knowledge[key] = value
    def query(self, key):
        return self.knowledge.get(key)

# Import our implemented adapters
from core.cognitive.autogpt_adapter import AutoGPTAdapter
from core.cognitive.olmo_adapter import OLMoAdapter

# --- Samantha-OS Event Loop Integration (stub) ---
try:
    from samantha.event_bus import SamanthaEventBus
except ImportError:
    class SamanthaEventBus:
        def __init__(self):
            self.events = []
        def publish(self, event):
            self.events.append(event)
            return True
        def poll(self):
            events = self.events
            self.events = []
            return events

class PatternDetector:
    def __init__(self):
        self.known_patterns = set()
        self.pattern_history = {}
        self.pattern_counts = {}
        self.temporal_spans = {}
        self.last_analysis_time = time.time()
    
    def detect(self, data: Any) -> List[str]:
        """
        Advanced pattern detection across multiple dimensions:
        - Structural patterns: repeating data structures
        - Temporal patterns: timing and sequences
        - Behavioral patterns: recurring user actions
        - Content patterns: topics and themes
        - Anomalies: deviations from established patterns
        """
        current_time = time.time()
        patterns = []
        
        # Track pattern analysis timing
        self.last_analysis_time = current_time
        
        if isinstance(data, dict):
            # Structural patterns in dict data
            struct_patterns = self._detect_structural_patterns(data)
            patterns.extend(struct_patterns)
            
            # Value patterns 
            value_patterns = self._detect_value_patterns(data)
            patterns.extend(value_patterns)
            
            # User behavior patterns if this is user data
            if any(k in str(data.keys()).lower() for k in ["user", "action", "behavior", "interaction"]):
                behavior_patterns = self._detect_behavioral_patterns(data)
                patterns.extend(behavior_patterns)
                
        elif isinstance(data, list):
            # Sequence patterns
            sequence_patterns = self._detect_sequence_patterns(data)
            patterns.extend(sequence_patterns)
            
        elif isinstance(data, str):
            # Text patterns
            text_patterns = self._detect_text_patterns(data)
            patterns.extend(text_patterns)
            
        # Update pattern history and frequency
        for pattern in patterns:
            if pattern not in self.pattern_history:
                self.pattern_history[pattern] = []
            self.pattern_history[pattern].append(current_time)
            self.pattern_counts[pattern] = self.pattern_counts.get(pattern, 0) + 1
        
        # Detect temporal patterns across all patterns
        temporal_patterns = self._detect_temporal_patterns()
        patterns.extend(temporal_patterns)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(data)
        patterns.extend(anomalies)
        
        # Track known patterns
        self.known_patterns.update(patterns)
        
        return patterns
    
    def _detect_structural_patterns(self, data: Dict) -> List[str]:
        """Detect patterns in data structure"""
        patterns = []
        
        # Check for nested structures
        nested_count = 0
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                nested_count += 1
        
        if nested_count > 3:
            patterns.append("pattern:complex_nested_structure")
        elif nested_count > 0:
            patterns.append("pattern:simple_nested_structure")
        
        # Check for typical data patterns
        keys = set(data.keys())
        if {"id", "name", "type"}.issubset(keys):
            patterns.append("pattern:entity_definition")
        if {"source", "destination", "type"}.issubset(keys):
            patterns.append("pattern:connection_definition")
        if {"timestamp", "action", "user"}.issubset(keys):
            patterns.append("pattern:event_log")
        if {"error", "message", "stack"}.issubset(keys):
            patterns.append("pattern:error_report")
            
        return patterns
    
    def _detect_value_patterns(self, data: Dict) -> List[str]:
        """Detect patterns in data values"""
        patterns = []
        
        # Track value types
        value_types = {}
        for k, v in data.items():
            t = type(v).__name__
            value_types[t] = value_types.get(t, 0) + 1
            
            # Check for empty values
            if v is None or (isinstance(v, (list, dict)) and not v) or (isinstance(v, str) and not v.strip()):
                patterns.append(f"pattern:empty_value:{k}")
            
        # Check for homogeneous data (mostly same type)
        if len(value_types) == 1 or (max(value_types.values()) / sum(value_types.values()) > 0.8):
            main_type = max(value_types.items(), key=lambda x: x[1])[0]
            patterns.append(f"pattern:homogeneous_data:{main_type}")
            
        return patterns
        
    def _detect_behavioral_patterns(self, data: Dict) -> List[str]:
        """Detect user behavior patterns"""
        patterns = []
        
        # Extract potential user action data
        action = None
        user = None
        timestamp = None
        
        for k, v in data.items():
            if k.lower() in ["action", "activity", "operation", "command"]:
                action = v
            elif k.lower() in ["user", "user_id", "username", "actor"]:
                user = v
            elif k.lower() in ["time", "timestamp", "created_at", "date"]:
                timestamp = v
        
        if action:
            patterns.append(f"pattern:user_action:{action}")
            
        return patterns
        
    def _detect_sequence_patterns(self, data: List) -> List[str]:
        """Detect patterns in sequences/lists"""
        patterns = []
        
        if not data:
            return patterns
            
        # Check for repeating elements
        element_counts = {}
        for item in data:
            element_key = str(item)
            element_counts[element_key] = element_counts.get(element_key, 0) + 1
            
        # If any element repeats significantly
        total = len(data)
        for item, count in element_counts.items():
            if count > 1 and count/total > 0.3:  # Repeats more than 30% of the time
                patterns.append(f"pattern:repeating_element:{item[:20]}")
                
        # Check for ascending/descending sequences with numbers
        if all(isinstance(x, (int, float)) for x in data):
            ascending = all(data[i] <= data[i+1] for i in range(len(data)-1))
            descending = all(data[i] >= data[i+1] for i in range(len(data)-1))
            
            if ascending:
                patterns.append("pattern:ascending_sequence")
            elif descending:
                patterns.append("pattern:descending_sequence")
                
        return patterns
        
    def _detect_text_patterns(self, data: str) -> List[str]:
        """Detect patterns in text content"""
        patterns = []
        
        # Simple length-based patterns
        if len(data) > 1000:
            patterns.append("pattern:long_text")
        elif len(data) < 10:
            patterns.append("pattern:short_text")
            
        # Check for JSON-like content
        if (data.strip().startswith('{') and data.strip().endswith('}')) or \
           (data.strip().startswith('[') and data.strip().endswith(']')):
            patterns.append("pattern:json_like_text")
            
        # Check for URL-like content
        if data.startswith(('http://', 'https://')):
            patterns.append("pattern:url_text")
            
        # Detect languages and topics (simplified)
        # In a real implementation, use NLP libraries
        
        return patterns
        
    def _detect_temporal_patterns(self) -> List[str]:
        """Detect timing patterns across all tracked patterns"""
        patterns = []
        current_time = time.time()
        
        # Analyze patterns with multiple occurrences
        for pattern, timestamps in self.pattern_history.items():
            if len(timestamps) < 2:
                continue
                
            # Calculate intervals between occurrences
            intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
            avg_interval = sum(intervals) / len(intervals)
            
            # Check if regular interval (low standard deviation)
            if len(intervals) > 2:
                std_dev = (sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)) ** 0.5
                if std_dev / avg_interval < 0.2:  # Low variation in intervals
                    patterns.append(f"pattern:periodic:{pattern}:{avg_interval:.1f}s")
                    self.temporal_spans[pattern] = avg_interval
                    
            # Check for recent activity spike
            recent_count = sum(1 for t in timestamps if current_time - t < 300)  # Within last 5 minutes
            if recent_count >= 3 and recent_count / len(timestamps) > 0.5:
                patterns.append(f"pattern:activity_spike:{pattern}")
                
            # Check for time-of-day patterns
            tod_buckets = {}
            for ts in timestamps:
                hour = datetime.fromtimestamp(ts).hour
                bucket = hour // 4  # 6 four-hour buckets in a day
                tod_buckets[bucket] = tod_buckets.get(bucket, 0) + 1
                
            # If more than 70% of occurrences happen in the same time bucket
            if tod_buckets and max(tod_buckets.values()) / sum(tod_buckets.values()) > 0.7:
                max_bucket = max(tod_buckets.items(), key=lambda x: x[1])[0]
                bucket_start = max_bucket * 4
                patterns.append(f"pattern:time_of_day:{pattern}:{bucket_start}-{bucket_start+4}h")
                
            # Check for day-of-week patterns
            if len(timestamps) >= 5:  # Need enough data points
                dow_buckets = {}
                for ts in timestamps:
                    day = datetime.fromtimestamp(ts).weekday()
                    dow_buckets[day] = dow_buckets.get(day, 0) + 1
                    
                # If more than 50% of occurrences happen on the same day
                if dow_buckets and max(dow_buckets.values()) / sum(dow_buckets.values()) > 0.5:
                    max_day = max(dow_buckets.items(), key=lambda x: x[1])[0]
                    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    patterns.append(f"pattern:day_of_week:{pattern}:{day_names[max_day]}")
                    
        return patterns
        
    def _detect_anomalies(self, data: Any) -> List[str]:
        """Detect anomalies and pattern deviations"""
        anomalies = []
        
        # Not enough history to detect anomalies yet
        if len(self.pattern_history) < 5:
            return anomalies
            
        if isinstance(data, dict):
            # Check for unexpected keys based on historical patterns
            common_keys = set()
            entity_patterns = [p for p in self.known_patterns if p.startswith("pattern:entity")]
            if entity_patterns:
                common_keys = {"id", "name", "type"}
            
            connection_patterns = [p for p in self.known_patterns if p.startswith("pattern:connection")]
            if connection_patterns:
                common_keys.update({"source", "destination"})
                
            if common_keys:
                missing_keys = common_keys - set(data.keys())
                if missing_keys:
                    anomalies.append(f"anomaly:missing_expected_keys:{','.join(missing_keys)}")
                    
            # Check for values outside expected ranges
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    # Check for extreme outliers (simple z-score approach)
                    history_key = f"value_history:{key}"
                    if history_key not in self.pattern_history:
                        self.pattern_history[history_key] = []
                    
                    history = self.pattern_history[history_key]
                    history.append(value)
                    
                    # Keep history at reasonable size
                    if len(history) > 100:
                        history.pop(0)
                    
                    # Need enough values to detect anomalies
                    if len(history) >= 5:
                        mean = sum(history) / len(history)
                        std_dev = (sum((x - mean) ** 2 for x in history) / len(history)) ** 0.5
                        
                        # Only flag if std_dev is significant
                        if std_dev > 0.001:
                            z_score = abs(value - mean) / std_dev
                            if z_score > 3:  # More than 3 standard deviations
                                anomalies.append(f"anomaly:outlier_value:{key}:{value}")
            
        # Check for temporal anomalies
        for pattern, avg_interval in self.temporal_spans.items():
            if pattern in self.pattern_history and len(self.pattern_history[pattern]) >= 2:
                timestamps = self.pattern_history[pattern]
                expected_time = timestamps[-2] + avg_interval
                actual_time = timestamps[-1]
                
                # If the timing is off by more than 30%
                if abs(actual_time - expected_time) / avg_interval > 0.3:
                    anomalies.append(f"anomaly:irregular_timing:{pattern}")
                    
        # Check for new patterns that haven't been seen before
        if isinstance(data, dict) and len(data) > 3:
            keys_set = frozenset(data.keys())
            
            # If this exact key combination is new
            if all(keys_set != frozenset(p.split(":")[2].split(",")) for p in self.known_patterns 
                  if p.startswith("pattern:keys:")):
                anomalies.append(f"anomaly:new_structure:{','.join(sorted(keys_set))}")
                    
        return anomalies

class InsightGenerator:
    def __init__(self):
        self.insight_history = []
        self.max_history = 100
        self.last_insights = []
        
    def generate(self, patterns: List[str]) -> List[str]:
        """
        Generate insights from detected patterns using:
        - Pattern correlation
        - Temporal analysis
        - Causal inference
        - Anomaly interpretation
        """
        if not patterns:
            return []
            
        insights = []
        
        # Group patterns by type
        pattern_groups = self._group_patterns(patterns)
        
        # Generate insights for each pattern type
        for group_name, group_patterns in pattern_groups.items():
            group_insights = self._generate_group_insights(group_name, group_patterns)
            insights.extend(group_insights)
            
        # Generate cross-group insights
        if len(pattern_groups) > 1:
            cross_insights = self._generate_cross_group_insights(pattern_groups)
            insights.extend(cross_insights)
            
        # Store new insights in history
        self.insight_history.extend(insights)
        if len(self.insight_history) > self.max_history:
            self.insight_history = self.insight_history[-self.max_history:]
            
        self.last_insights = insights
        return insights
        
    def _group_patterns(self, patterns: List[str]) -> Dict[str, List[str]]:
        """Group patterns by their types"""
        groups = {}
        
        for pattern in patterns:
            if not pattern.startswith("pattern:"):
                continue
                
            parts = pattern.split(":", 2)
            if len(parts) < 2:
                continue
                
            group_name = parts[1]
            if group_name not in groups:
                groups[group_name] = []
                
            groups[group_name].append(pattern)
            
        return groups
        
    def _generate_group_insights(self, group_name: str, patterns: List[str]) -> List[str]:
        """Generate insights for a specific pattern group"""
        insights = []
        
        if group_name == "empty_value":
            # Insights for empty values
            insights.append(f"insight:data_quality:Found {len(patterns)} empty fields that may need attention")
            
        elif group_name == "entity_definition":
            # Insights for entity patterns
            insights.append("insight:structure:Data follows standard entity definition pattern")
            
        elif group_name == "complex_nested_structure":
            insights.append("insight:complexity:Data has complex nested structure which may benefit from flattening")
            
        elif group_name == "user_action":
            # Extract specific actions from patterns
            actions = [p.split(":", 2)[2] for p in patterns if len(p.split(":", 2)) > 2]
            insights.append(f"insight:behavior:User performed {len(actions)} tracked actions: {', '.join(actions[:3])}")
            
        elif group_name == "repeating_element":
            insights.append("insight:redundancy:Contains repeating elements which may indicate redundancy")
            
        elif group_name == "periodic":
            insights.append("insight:timing:Detected regular periodic pattern in event timing")
            
        elif group_name == "activity_spike":
            insights.append("insight:activity:Recent spike in activity detected")
            
        elif group_name.startswith("anomaly"):
            insights.append(f"insight:anomaly:Detected anomaly that requires investigation: {group_name}")
            
        # General insight for any pattern group with multiple patterns
        if len(patterns) > 3:
            insights.append(f"insight:frequency:{group_name} patterns appear with high frequency ({len(patterns)} occurrences)")
            
        return insights
        
    def _generate_cross_group_insights(self, pattern_groups: Dict[str, List[str]]) -> List[str]:
        """Generate insights by looking at relationships between pattern groups"""
        insights = []
        
        # Check for structural + behavioral patterns
        if "entity_definition" in pattern_groups and "user_action" in pattern_groups:
            insights.append("insight:interaction:User actions are affecting entity data")
            
        # Check for complex structure + empty values
        if "complex_nested_structure" in pattern_groups and "empty_value" in pattern_groups:
            insights.append("insight:data_quality:Complex data structure contains empty values that may cause issues")
            
        # Check for timing patterns + behavioral patterns
        if any(g.startswith("periodic") for g in pattern_groups.keys()) and "user_action" in pattern_groups:
            insights.append("insight:routine:Detected regular patterns in user behavior")
            
        # Check for anomalies + any other pattern type
        anomalies = [g for g in pattern_groups.keys() if g.startswith("anomaly")]
        if anomalies and len(pattern_groups) > len(anomalies):
            insights.append("insight:investigation:Anomalies detected alongside normal patterns - investigate correlation")
            
        return insights

class CognitiveSystem:
    def __init__(self):
        self.memory = WorkingMemory()
        self.attention = AttentionManager()
        self.knowledge = KnowledgeBase()
        self.pattern_detector = PatternDetector()
        self.insight_generator = InsightGenerator()
        self.event_bus = EventBus()
        self.storage = UnifiedStorageLayer()
        self.llm_council = CrewAICouncil()
        self.running = False
        
        # Initialize our enhanced adapters
        self.autogpt_adapter = AutoGPTAdapter()
        self.olmo_adapter = OLMoAdapter()
        self.samantha_event_bus = SamanthaEventBus()

    def process_event(self, event: Dict[str, Any]):
        # Event-driven processing logic (Samantha-OS style)
        event_type = event.get('type')
        payload = event.get('payload', {})
        if event_type == 'memory.update':
            self.memory.set(payload['key'], payload['value'])
            self.storage.set('cognitive_memory', payload['key'], payload['value'])
            self.llm_council.share_memory(payload['key'], payload['value'])
        elif event_type == 'attention.set':
            self.attention.set_focus(payload['focus'])
            self.storage.set('cognitive_attention', 'focus', payload['focus'])
        elif event_type == 'knowledge.add':
            self.knowledge.add(payload['key'], payload['value'])
            self.storage.set('cognitive_knowledge', payload['key'], payload['value'])
        elif event_type == 'pattern.detect':
            patterns = self.pattern_detector.detect(payload['data'])
            self.event_bus.publish('pattern.detected', {'patterns': patterns})
        elif event_type == 'insight.generate':
            insights = self.insight_generator.generate(payload['patterns'])
            self.event_bus.publish('insight.generated', {'insights': insights})
            # Share insights with LLM council
            self.llm_council.share_memory('insights', insights)
        elif event_type == 'reasoning.infer':
            query = payload.get('query', '')
            context = payload.get('context')
            result = self.olmo_adapter.answer_question(query, context)
            self.event_bus.publish('reasoning.result', {'result': result})
            
        elif event_type == 'reasoning.analyze':
            text = payload.get('text', '')
            result = self.olmo_adapter.analyze_text(text)
            self.event_bus.publish('reasoning.analysis.result', {'result': result})
            
        elif event_type == 'reasoning.generate_code':
            spec = payload.get('specification', '')
            lang = payload.get('language', 'python')
            result = self.olmo_adapter.generate_code(spec, lang)
            self.event_bus.publish('reasoning.code.result', {'result': result})
            
        elif event_type == 'council.plan':
            # Forward plan execution to LLM council
            plan = payload.get('plan')
            context = payload.get('context')
            result = self.llm_council.execute_plan(plan, context)
            self.event_bus.publish('council.plan.result', {'result': result})
            
        # Handle AutoGPT-related events with our adapter
        elif event_type == 'autogpt.memory.update':
            key = payload.get('key')
            value = payload.get('value')
            if key and value:
                self.autogpt_adapter.create_memory(key, value)
                
        elif event_type == 'autogpt.memory.retrieve':
            key = payload.get('key')
            if key:
                memory = self.autogpt_adapter.retrieve_memory(key)
                self.event_bus.publish('autogpt.memory.result', {'key': key, 'value': memory})
                
        elif event_type == 'autogpt.plan':
            goal = payload.get('goal')
            if goal:
                plan = self.autogpt_adapter.create_plan_for_goal(goal)
                self.event_bus.publish('autogpt.plan.result', {'plan': plan})
                
        elif event_type == 'autogpt.execute':
            plan_id = payload.get('plan_id')
            if plan_id:
                result = self.autogpt_adapter.execute_plan_step(plan_id)
                self.event_bus.publish('autogpt.execution.result', {'result': result})
                
        # Handle Samantha-OS event propagation
        elif event_type == 'samantha.event':
            self.samantha_event_bus.publish(payload)

    def run_autonomous_cycle(self, poll_interval: float = 5.0):
        """Run the autonomous cognitive cycle in the background (AutoGPT/Samantha-OS style)"""
        import threading, time
        def loop():
            self.running = True
            while self.running:
                # Poll for new events
                events = self.event_bus.poll('cognitive.event_queue')
                for event in events:
                    self.process_event(event)
                # Autonomous pattern detection/insight generation
                patterns = self.pattern_detector.detect(self.memory.data)
                if patterns:
                    insights = self.insight_generator.generate(patterns)
                    self.event_bus.publish('insight.generated', {'insights': insights})
                    self.llm_council.share_memory('insights', insights)
                # AutoGPT background planning and execution
                if time.time() % 300 < 10:  # Run approximately every 5 minutes
                    # Create an autonomous goal based on current patterns
                    patterns = [p for p in self.pattern_detector.known_patterns][:5]
                    autonomous_goal = f"Analyze and recommend actions for patterns: {', '.join(patterns)}"
                    
                    # Create plan with AutoGPT adapter
                    plan = self.autogpt_adapter.create_plan_for_goal(autonomous_goal)
                    self.event_bus.publish('autogpt.plan.result', {'plan': plan})
                    
                    # Execute a step from the plan
                    if plan and "id" in plan:
                        result = self.autogpt_adapter.execute_plan_step(plan["id"])
                        self.event_bus.publish('autogpt.execution.result', {'result': result})
                
                # Samantha-OS event bus polling
                samantha_events = self.samantha_event_bus.poll()
                for sevt in samantha_events:
                    self.process_event(sevt)
                time.sleep(poll_interval)
        t = threading.Thread(target=loop, daemon=True)
        t.start()

    def stop_autonomous_cycle(self):
        self.running = False
