"""
Character Archivist Profiling Pipeline

Implements the step-by-step AI process flow for character profiling and FMT recommendation.
"""
from typing import Dict, Any, List
import logging
import re
from textblob import TextBlob

logger = logging.getLogger(__name__)

def parse_chat_log(chat_log: str) -> List[Dict[str, Any]]:
    """
    Parse chat log into timestamped, role-tagged messages.
    Supports WhatsApp-style and plain text logs.
    """
    messages = []
    # WhatsApp-style: [date, time] sender: message
    pattern = re.compile(r"\[(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}:\d{2} [APM]{2})\] ([^:]+): (.*)")
    for line in chat_log.splitlines():
        match = pattern.match(line)
        if match:
            date, time, sender, content = match.groups()
            messages.append({
                "timestamp": f"{date} {time}",
                "sender": sender.strip(),
                "content": content.strip(),
            })
        else:
            # Try fallback: sender: message
            if ':' in line:
                sender, content = line.split(':', 1)
                messages.append({
                    "timestamp": None,
                    "sender": sender.strip(),
                    "content": content.strip(),
                })
    return messages

def emotion_mapping(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Score each message for sentiment and emotional signals using TextBlob.
    Adds 'sentiment' and 'emotion' fields to each message.
    """
    for msg in messages:
        blob = TextBlob(msg["content"])
        polarity = blob.sentiment.polarity
        if polarity > 0.2:
            sentiment = "positive"
        elif polarity < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        msg["sentiment"] = sentiment
        # Simple emotion mapping (expandable)
        if any(word in msg["content"].lower() for word in ["love", "miss", "dear", "happy", "smile"]):
            msg["emotion"] = "affection"
        elif any(word in msg["content"].lower() for word in ["sorry", "sad", "hurt", "cry"]):
            msg["emotion"] = "sadness"
        elif any(word in msg["content"].lower() for word in ["angry", "mad", "upset"]):
            msg["emotion"] = "anger"
        else:
            msg["emotion"] = "neutral"
    return messages

def build_profile(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a dynamic psychological profile from messages.
    Extracts core identity, traits, habits, relationship context, and vulnerability.
    """
    profile = {
        "core_identity": {},
        "traits": {},
        "habits": {},
        "relationships": {},
        "backstory": {},
        "conflicts": {},
        "vulnerability": {},
    }
    # Core identity extraction (simple heuristics)
    for msg in messages:
        if "originally from" in msg["content"].lower():
            profile["core_identity"]["location"] = msg["content"]
        if "work" in msg["content"].lower() or "job" in msg["content"].lower():
            profile["core_identity"]["occupation"] = msg["content"]
        if "name is" in msg["content"].lower():
            profile["core_identity"]["name"] = msg["content"]
    # Trait extraction (sentiment/emotion stats)
    sentiments = [m["sentiment"] for m in messages]
    profile["traits"]["positivity_ratio"] = sentiments.count("positive") / max(1, len(sentiments))
    profile["traits"]["negativity_ratio"] = sentiments.count("negative") / max(1, len(sentiments))
    # Habits (time of day, routines)
    times = [m["timestamp"] for m in messages if m["timestamp"]]
    profile["habits"]["active_times"] = list(set([t.split()[1][:2] for t in times if t]))
    # Relationships (mentions of family, friends)
    for msg in messages:
        if any(word in msg["content"].lower() for word in ["son", "daughter", "family", "friend", "partner"]):
            profile["relationships"].setdefault("mentions", []).append(msg["content"])
    # Vulnerability (trust, scam, openness)
    for msg in messages:
        if any(word in msg["content"].lower() for word in ["trust", "scam", "honest", "openness"]):
            profile["vulnerability"].setdefault("signals", []).append(msg["content"])
    return profile

def recommend_fmt(profile: Dict[str, Any], stage: str) -> Dict[str, Any]:
    """
    Recommend the next Format (FMT) based on profile and stage.
    Uses FMT templates and Filtering Process logic.
    """
    # Example: Use stage and vulnerability to pick FMT
    if stage.lower() in ["initial", "acquaintance"]:
        return {"recommended_fmt": "1st FMT", "reason": "Initial rapport and info gathering."}
    if profile["vulnerability"].get("signals"):
        return {"recommended_fmt": "Trust Builder FMT", "reason": "Detected trust/scam topics."}
    if profile["traits"].get("negativity_ratio", 0) > 0.3:
        return {"recommended_fmt": "Affection FMT", "reason": "Increase positivity and emotional connection."}
    return {"recommended_fmt": "General Follow-Up FMT", "reason": "Maintain engagement."}

def generate_report(profile: Dict[str, Any], history: List[Dict[str, Any]]) -> str:
    """
    Generate a review report for the character's relationship path.
    Summarizes key findings, vulnerabilities, and next steps.
    """
    report = ["Character Review Report\n====================\n"]
    report.append(f"Core Identity: {profile.get('core_identity', {})}")
    report.append(f"Traits: {profile.get('traits', {})}")
    report.append(f"Habits: {profile.get('habits', {})}")
    report.append(f"Relationships: {profile.get('relationships', {})}")
    report.append(f"Vulnerability Signals: {profile.get('vulnerability', {})}")
    report.append("\nConversation Highlights:")
    for msg in history[-5:]:
        report.append(f"[{msg.get('timestamp', '')}] {msg.get('sender', '')}: {msg.get('content', '')} (Sentiment: {msg.get('sentiment', '')}, Emotion: {msg.get('emotion', '')})")
    report.append("\nRecommended Next FMT: " + recommend_fmt(profile, stage='')["recommended_fmt"])
    return "\n".join(report)
