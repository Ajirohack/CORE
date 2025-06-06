"""
Tools Integration for the Archivist Package.

This module integrates the Archivist Package with the SpaceNew tools system
and other components like the RAG system and AI Council.
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class ArchivistToolsIntegration:
    """
    Integration between Archivist Package and SpaceNew tools system.
    
    This class provides the integration layer between the Archivist Package
    and other SpaceNew components like RAG, AI Council, and the tools system.
    """
    
    def __init__(self, config: Dict[str, Any], plugin_instance):
        self.config = config
        self.plugin_instance = plugin_instance
        self.rag_connector = None
        self.ai_council_connector = None
    
    def initialize(self):
        """Initialize the tools integration"""
        try:
            # Import integration components
            from core.packages.plugin_system.context_provider import ContextProvider
            from core.ai_council.capability_registry import CapabilityRegistry
            from core.rag_system.rag_connector import RAGConnector
            
            # Initialize RAG connector if enabled
            if self.config.get("rag_integration", {}).get("enabled", True):
                self.rag_connector = RAGConnector(
                    vector_db=self.config.get("rag_integration", {}).get("vector_db", "pinecone"),
                    embeddings_model=self.config.get("rag_integration", {}).get("embeddings_model"),
                    knowledge_base_dirs=self.config.get("rag_integration", {}).get("knowledge_base_directories", [])
                )
                
                # Register capabilities with RAG system
                self._register_rag_capabilities()
            
            # Initialize AI Council connector
            self.ai_council_connector = CapabilityRegistry.get_connector()
            
            # Register capabilities with AI Council
            self._register_ai_council_capabilities()
            
            logger.info("Archivist Tools Integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Archivist Tools Integration: {str(e)}")
            return False
    
    def _register_rag_capabilities(self):
        """Register Archivist Package capabilities with RAG system"""
        if not self.rag_connector:
            return
        
        try:
            # Register knowledge bases
            self.rag_connector.register_knowledge_base(
                name="archivist_personas",
                description="Persona information for human simulation",
                source_path="./data/archivist/personas"
            )
            
            self.rag_connector.register_knowledge_base(
                name="archivist_scenarios",
                description="Scenario templates and definitions",
                source_path="./data/archivist/scenarios"
            )
            
            self.rag_connector.register_knowledge_base(
                name="archivist_stages",
                description="Stage definitions and scoring criteria",
                source_path="./data/archivist/stages"
            )
            
            logger.info("Registered Archivist knowledge bases with RAG system")
            
        except Exception as e:
            logger.error(f"Failed to register RAG capabilities: {str(e)}")
    
    def _register_ai_council_capabilities(self):
        """Register Archivist Package capabilities with AI Council"""
        if not self.ai_council_connector:
            return
        
        try:
            # Register human simulation capabilities
            self.ai_council_connector.register_capability(
                capability_id="human_simulator.generate_response",
                description="Generate a human-like response based on persona and context",
                endpoint="/api/human-simulator/simulate",
                method="POST",
                parameters={
                    "type": "object",
                    "properties": {
                        "persona_id": {"type": "string"},
                        "context": {"type": "string"},
                        "scenario_id": {"type": "string"},
                        "stage": {"type": "string"}
                    },
                    "required": ["persona_id", "context"]
                }
            )
            
            # Register financial document generation
            self.ai_council_connector.register_capability(
                capability_id="financial_business.generate_document",
                description="Generate a financial document based on template",
                endpoint="/api/financial/documents/generate",
                method="POST",
                parameters={
                    "type": "object",
                    "properties": {
                        "template_id": {"type": "string"},
                        "data": {"type": "object"}
                    },
                    "required": ["template_id", "data"]
                }
            )
            
            logger.info("Registered Archivist capabilities with AI Council")
            
        except Exception as e:
            logger.error(f"Failed to register AI Council capabilities: {str(e)}")
    
    def shutdown(self):
        """Shut down the tools integration"""
        try:
            # Unregister AI Council capabilities
            if self.ai_council_connector:
                self.ai_council_connector.unregister_capability("human_simulator.generate_response")
                self.ai_council_connector.unregister_capability("financial_business.generate_document")
            
            # Close RAG connector
            if self.rag_connector:
                self.rag_connector.close()
            
            logger.info("Archivist Tools Integration shutdown successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to shut down Archivist Tools Integration: {str(e)}")
            return False
