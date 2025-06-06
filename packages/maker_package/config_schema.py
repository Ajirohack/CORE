"""
Configuration schema for the Maker Package
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator


class PlatformCredentials(BaseModel):
    """Credentials for external platform access"""
    platform_id: str = Field(..., description="Unique identifier for the platform")
    api_key: Optional[str] = Field(None, description="API key for the platform")
    api_secret: Optional[str] = Field(None, description="API secret for the platform")
    username: Optional[str] = Field(None, description="Username for the platform")
    password: Optional[str] = Field(None, description="Password for the platform")
    token: Optional[str] = Field(None, description="Authentication token")
    cookies: Optional[Dict[str, str]] = Field(None, description="Session cookies")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers")
    extra: Optional[Dict[str, Any]] = Field(None, description="Additional platform-specific credentials")


class PersonaTraits(BaseModel):
    """Personality traits for a simulated persona"""
    openness: float = Field(0.5, ge=0.0, le=1.0, description="Openness to experience")
    conscientiousness: float = Field(0.5, ge=0.0, le=1.0, description="Conscientiousness")
    extraversion: float = Field(0.5, ge=0.0, le=1.0, description="Extraversion")
    agreeableness: float = Field(0.5, ge=0.0, le=1.0, description="Agreeableness")
    neuroticism: float = Field(0.5, ge=0.0, le=1.0, description="Neuroticism")
    additional_traits: Optional[Dict[str, float]] = Field(None, description="Additional personality traits")


class PersonaProfile(BaseModel):
    """Profile configuration for a simulated persona"""
    name: str = Field(..., description="Name of the persona")
    age: int = Field(..., description="Age of the persona")
    gender: str = Field(..., description="Gender of the persona")
    location: str = Field(..., description="Location of the persona")
    occupation: str = Field(..., description="Occupation of the persona")
    background: str = Field(..., description="Background story of the persona")
    interests: List[str] = Field(default_factory=list, description="Interests of the persona")
    traits: PersonaTraits = Field(default_factory=PersonaTraits, description="Personality traits")
    speech_style: Dict[str, Any] = Field(default_factory=dict, description="Speech style parameters")
    avatar: Optional[str] = Field(None, description="Path to avatar image")
    documents: Optional[List[str]] = Field(None, description="List of associated documents")
    relationship_goals: Optional[List[str]] = Field(None, description="Relationship goals for dating scenarios")
    financial_profile: Optional[Dict[str, Any]] = Field(None, description="Financial profile for financial scenarios")


class ScenarioConfig(BaseModel):
    """Configuration for a simulation scenario"""
    scenario_id: str = Field(..., description="Unique identifier for the scenario")
    title: str = Field(..., description="Title of the scenario")
    description: str = Field(..., description="Description of the scenario")
    type: str = Field(..., description="Type of scenario (dating, investment, etc.)")
    primary_persona: str = Field(..., description="ID of the primary persona")
    target_platforms: List[str] = Field(default_factory=list, description="Target platforms for the scenario")
    goals: List[str] = Field(default_factory=list, description="Goals of the scenario")
    success_metrics: Dict[str, Any] = Field(default_factory=dict, description="Success metrics for the scenario")
    duration: Optional[str] = Field(None, description="Expected duration of the scenario")
    stages: Optional[List[Dict[str, Any]]] = Field(None, description="Stages of the scenario")
    fallback_strategies: Optional[Dict[str, Any]] = Field(None, description="Fallback strategies")


class MakerPackageConfig(BaseModel):
    """Main configuration for the Maker Package"""
    # Core settings
    package_enabled: bool = Field(True, description="Enable or disable the package")
    default_mode: str = Field("archivist", description="Default operation mode")
    allowed_modes: List[str] = Field(default_factory=lambda: ["archivist", "orchestrator", "godfather"], 
                                    description="Allowed operation modes")
    
    # Component settings
    enable_human_simulator: bool = Field(True, description="Enable human simulator component")
    enable_financial_platform: bool = Field(True, description="Enable financial business platform component")
    
    # External integrations
    platform_credentials: Dict[str, PlatformCredentials] = Field(
        default_factory=dict, 
        description="Credentials for external platforms"
    )
    
    # Simulation settings
    personas: Dict[str, PersonaProfile] = Field(default_factory=dict, description="Persona profiles")
    scenarios: Dict[str, ScenarioConfig] = Field(default_factory=dict, description="Scenario configurations")
    
    # Advanced settings
    llm_settings: Dict[str, Any] = Field(default_factory=dict, description="LLM settings")
    memory_settings: Dict[str, Any] = Field(default_factory=dict, description="Memory settings")
    logging_level: str = Field("info", description="Logging level")
    advanced_features: Dict[str, bool] = Field(default_factory=dict, description="Toggle advanced features")
    
    # Security settings
    security_settings: Dict[str, Any] = Field(default_factory=dict, description="Security settings")
    
    class Config:
        """Config for the model"""
        extra = "forbid"  # Prohibit extra fields
