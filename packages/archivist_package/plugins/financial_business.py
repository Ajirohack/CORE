"""
Financial Business Plugin for the Archivist Package.

This plugin provides financial tools and capabilities for business scenarios.
"""
from typing import Dict, List, Any
import os
import sys
import logging

from core.packages.plugin_system.plugin_interface import (
    ServicePlugin, 
    PluginManifest, 
    ServiceEndpoint
)

logger = logging.getLogger(__name__)

class FinancialBusinessPlugin(ServicePlugin):
    """
    Financial Business Plugin implementation for the Archivist Package.
    
    This plugin provides financial tools, document generation, and business
    scenario capabilities.
    """
    
    def __init__(self):
        self.initialized = False
        self.config = {}
        self.document_generator = None
        self.payment_processor = None
    
    def get_manifest(self) -> PluginManifest:
        """Return the Financial Business plugin manifest"""
        return PluginManifest(
            id="financial_business",
            name="Financial Business Tools",
            version="1.0.0",
            description="Financial tools and business capabilities for simulation scenarios",
            
            # API Endpoints
            endpoints=[
                ServiceEndpoint(
                    path="/api/financial/documents/generate",
                    method="POST",
                    description="Generate financial documents",
                    auth_required=True
                ),
                ServiceEndpoint(
                    path="/api/financial/transactions/simulate",
                    method="POST",
                    description="Simulate a financial transaction",
                    auth_required=True
                ),
                ServiceEndpoint(
                    path="/api/financial/statements/generate",
                    method="POST",
                    description="Generate financial statements",
                    auth_required=True
                ),
                ServiceEndpoint(
                    path="/api/financial/templates",
                    method="GET",
                    description="Get available financial document templates",
                    auth_required=True
                ),
            ],
            
            # Dependencies
            dependencies=["file_storage", "document_processor"]
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the Financial Business plugin with the provided configuration"""
        try:
            self.config = config
            
            if not config.get("enabled", True):
                logger.info("Financial Business plugin is disabled in config")
                return True
            
            # Import financial business components
            from .financial import DocumentGenerator, PaymentProcessor, TransactionSimulator
            
            # Initialize document generator
            template_path = config.get("document_templates_path", "./data/financial/templates")
            api_key = config.get("api_keys", {}).get("document_generator")
            
            self.document_generator = DocumentGenerator(
                template_path=template_path,
                api_key=api_key
            )
            
            # Initialize payment processor
            payment_api_key = config.get("api_keys", {}).get("payment_processor")
            self.payment_processor = PaymentProcessor(api_key=payment_api_key)
            
            logger.info("Financial Business plugin successfully initialized")
            self.initialized = True
            return True
            
        except ImportError as e:
            logger.error(f"Failed to import Financial Business components: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Financial Business plugin: {str(e)}")
            return False
    
    def shutdown(self) -> bool:
        """Gracefully shut down the Financial Business plugin"""
        try:
            # Clean up resources
            if self.document_generator:
                self.document_generator.cleanup()
                
            if self.payment_processor:
                self.payment_processor.close_connections()
            
            self.initialized = False
            logger.info("Financial Business plugin successfully shut down")
            return True
            
        except Exception as e:
            logger.error(f"Error shutting down Financial Business plugin: {str(e)}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Return the health status of the Financial Business plugin"""
        status = {
            "status": "healthy" if self.initialized else "unhealthy",
            "initialized": self.initialized,
            "document_generator_active": self.document_generator is not None,
            "payment_processor_active": self.payment_processor is not None
        }
        
        return status
