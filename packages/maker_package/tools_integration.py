"""
Maker Package Integration with SpaceNew Tools System

This module provides the integration between the Maker Package and the
SpaceNew Tools System, enabling the package to expose its functionality
as tools that can be used by the platform.
"""

import logging
import os
import time
from typing import Dict, List, Any, Optional, Callable, Type, Union
import functools

from core.packages.src.tools_system import ToolsSystem, ToolAccessLevel, ToolCategory
from core.packages.src.schemas import ToolManifest
from .components.human_simulator import HumanSimulator
from .components.financial_platform import FinancialPlatform

# Configure logging
logger = logging.getLogger(__name__)


class MakerPackageTools:
    """
    Integration of Maker Package capabilities with the SpaceNew Tools System
    
    This class provides the tools that the Maker Package exposes to the
    SpaceNew platform, enabling its functionality to be used by AI agents
    and other components.
    """
    
    def __init__(self, tools_system: ToolsSystem, 
                 human_simulator: Optional[HumanSimulator] = None,
                 financial_platform: Optional[FinancialPlatform] = None):
        """
        Initialize the tools integration
        
        Args:
            tools_system: The SpaceNew Tools System to register with
            human_simulator: Human Simulator component (optional)
            financial_platform: Financial Platform component (optional)
        """
        self.tools_system = tools_system
        self.human_simulator = human_simulator
        self.financial_platform = financial_platform
        self.registered_tools = set()
    
    def register_tools(self):
        """Register all tools provided by the Maker Package"""
        logger.info("Registering Maker Package tools...")
        
        # Register Human Simulator tools if available
        if self.human_simulator:
            self._register_human_simulator_tools()
        
        # Register Financial Platform tools if available
        if self.financial_platform:
            self._register_financial_platform_tools()
        
        logger.info(f"Registered {len(self.registered_tools)} Maker Package tools")
    
    def _register_human_simulator_tools(self):
        """Register tools provided by the Human Simulator component"""
        logger.info("Registering Human Simulator tools...")
        
        # Create persona tool
        @self.tools_system.register_tool(
            name="maker.persona.create",
            description="Create a new persona with specified traits and characteristics",
            access_level=ToolAccessLevel.ADVANCED,  # Godfather mode required
            category=ToolCategory.CUSTOM
        )
        def create_persona(
            name: str,
            age: int,
            gender: str,
            location: str,
            occupation: str = "",
            background: str = "",
            interests: List[str] = None,
            traits: Dict[str, float] = None
        ) -> Dict[str, Any]:
            """
            Create a new persona with specified traits and characteristics
            
            Args:
                name: Name of the persona
                age: Age of the persona
                gender: Gender of the persona
                location: Location of the persona
                occupation: Occupation of the persona (optional)
                background: Background story of the persona (optional)
                interests: List of interests for the persona (optional)
                traits: Personality traits for the persona (optional)
                
            Returns:
                Dict: Information about the created persona
            """
            logger.info(f"Creating persona: {name}")
            
            # Create persona configuration
            persona_config = {
                "name": name,
                "age": age,
                "gender": gender,
                "location": location,
                "occupation": occupation,
                "background": background,
                "interests": interests or [],
                "traits": traits or {}
            }
            
            # Create the persona using the Human Simulator
            persona_id = self.human_simulator.create_persona(persona_config)
            
            return {
                "persona_id": persona_id,
                "name": name,
                "status": "created"
            }
        
        self.registered_tools.add("maker.persona.create")
        
        # Start conversation tool
        @self.tools_system.register_tool(
            name="maker.conversation.start",
            description="Start a new conversation using a persona on a specific platform",
            access_level=ToolAccessLevel.STANDARD,  # Orchestrator mode required
            category=ToolCategory.CUSTOM
        )
        def start_conversation(
            persona_id: str,
            platform: str,
            target_id: str
        ) -> Dict[str, Any]:
            """
            Start a new conversation using a persona on a specific platform
            
            Args:
                persona_id: ID of the persona to use
                platform: Platform to start the conversation on (e.g., 'dating_site', 'telegram')
                target_id: ID of the target on the platform
                
            Returns:
                Dict: Information about the started conversation
            """
            logger.info(f"Starting conversation for persona: {persona_id} on platform: {platform}")
            
            # Start the conversation using the Human Simulator
            conversation = self.human_simulator.start_conversation(persona_id, platform, target_id)
            
            return {
                "conversation_id": conversation["id"],
                "persona_id": persona_id,
                "platform": platform,
                "status": "active"
            }
        
        self.registered_tools.add("maker.conversation.start")
        
        # Send message tool
        @self.tools_system.register_tool(
            name="maker.conversation.send_message",
            description="Send a message in a conversation",
            access_level=ToolAccessLevel.STANDARD,  # Orchestrator mode required
            category=ToolCategory.CUSTOM
        )
        def send_message(
            conversation_id: str,
            message: str
        ) -> Dict[str, Any]:
            """
            Send a message in a conversation
            
            Args:
                conversation_id: ID of the conversation
                message: Message content to send
                
            Returns:
                Dict: Information about the sent message
            """
            logger.info(f"Sending message in conversation: {conversation_id}")
            
            # Send the message using the Human Simulator
            message_data = self.human_simulator.send_message(conversation_id, message)
            
            return {
                "message_id": message_data["id"],
                "conversation_id": conversation_id,
                "status": "sent"
            }
        
        self.registered_tools.add("maker.conversation.send_message")
        
        # Get response tool
        @self.tools_system.register_tool(
            name="maker.conversation.get_response",
            description="Generate a response to an incoming message",
            access_level=ToolAccessLevel.STANDARD,  # Orchestrator mode required
            category=ToolCategory.CUSTOM
        )
        def get_response(
            conversation_id: str,
            incoming_message: str
        ) -> Dict[str, Any]:
            """
            Generate a response to an incoming message
            
            Args:
                conversation_id: ID of the conversation
                incoming_message: The incoming message to respond to
                
            Returns:
                Dict: The generated response message
            """
            logger.info(f"Generating response in conversation: {conversation_id}")
            
            # Generate the response using the Human Simulator
            response_data = self.human_simulator.get_response(conversation_id, incoming_message)
            
            return {
                "message_id": response_data["id"],
                "conversation_id": conversation_id,
                "content": response_data["content"],
                "status": "generated"
            }
        
        self.registered_tools.add("maker.conversation.get_response")
    
    def _register_financial_platform_tools(self):
        """Register tools provided by the Financial Platform component"""
        logger.info("Registering Financial Platform tools...")
        
        # Generate ID card tool
        @self.tools_system.register_tool(
            name="maker.documents.generate_id_card",
            description="Generate an ID card document with specified person information",
            access_level=ToolAccessLevel.ADVANCED,  # Godfather mode required
            category=ToolCategory.CUSTOM
        )
        def generate_id_card(
            first_name: str,
            last_name: str,
            date_of_birth: str,
            address: str,
            id_number: str = None,
            expiry_date: str = None
        ) -> Dict[str, Any]:
            """
            Generate an ID card document with specified person information
            
            Args:
                first_name: First name of the person
                last_name: Last name of the person
                date_of_birth: Date of birth (YYYY-MM-DD)
                address: Physical address
                id_number: ID number (optional, will be generated if not provided)
                expiry_date: Expiry date (optional, will be generated if not provided)
                
            Returns:
                Dict: Information about the generated ID card
            """
            logger.info(f"Generating ID card for: {first_name} {last_name}")
            
            # Generate ID number if not provided
            if not id_number:
                id_number = f"ID{int(time.time())}"
            
            # Generate expiry date if not provided
            if not expiry_date:
                current_year = time.localtime().tm_year
                expiry_date = f"{current_year + 10}-01-01"
            
            # Create person data
            person_data = {
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": date_of_birth,
                "address": address,
                "id_number": id_number,
                "expiry_date": expiry_date
            }
            
            # Generate the ID card document
            document = self.financial_platform.generate_id_card(person_data)
            
            return {
                "document_id": document["id"],
                "document_type": "id_card",
                "id_number": id_number,
                "status": "generated",
                "path": document["path"]
            }
        
        self.registered_tools.add("maker.documents.generate_id_card")
        
        # Generate bank statement tool
        @self.tools_system.register_tool(
            name="maker.documents.generate_bank_statement",
            description="Generate a bank statement document for a specified account and date range",
            access_level=ToolAccessLevel.ADVANCED,  # Godfather mode required
            category=ToolCategory.CUSTOM
        )
        def generate_bank_statement(
            account_id: str,
            start_date: str,
            end_date: str
        ) -> Dict[str, Any]:
            """
            Generate a bank statement document for a specified account and date range
            
            Args:
                account_id: ID of the account
                start_date: Start date for the statement (YYYY-MM-DD)
                end_date: End date for the statement (YYYY-MM-DD)
                
            Returns:
                Dict: Information about the generated bank statement
            """
            logger.info(f"Generating bank statement for account: {account_id}")
            
            # Generate the bank statement document
            document = self.financial_platform.generate_bank_statement(
                account_id, start_date, end_date
            )
            
            return {
                "document_id": document["id"],
                "document_type": "bank_statement",
                "account_id": account_id,
                "period": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "status": "generated",
                "path": document["path"]
            }
        
        self.registered_tools.add("maker.documents.generate_bank_statement")
        
        # Create account tool
        @self.tools_system.register_tool(
            name="maker.financial.create_account",
            description="Create a simulated financial account",
            access_level=ToolAccessLevel.ADVANCED,  # Godfather mode required
            category=ToolCategory.CUSTOM
        )
        def create_account(
            account_type: str,
            owner: str,
            initial_balance: float = 0.0,
            currency: str = "USD"
        ) -> Dict[str, Any]:
            """
            Create a simulated financial account
            
            Args:
                account_type: Type of account (e.g., 'checking', 'savings', 'investment')
                owner: Owner of the account
                initial_balance: Initial balance for the account (optional)
                currency: Currency for the account (optional)
                
            Returns:
                Dict: Information about the created account
            """
            logger.info(f"Creating {account_type} account for: {owner}")
            
            # Create metadata
            metadata = {
                "currency": currency
            }
            
            # Create the account
            account = self.financial_platform.create_account(
                account_type, owner, initial_balance, metadata
            )
            
            return {
                "account_id": account["id"],
                "account_type": account_type,
                "owner": owner,
                "balance": initial_balance,
                "currency": currency,
                "status": "active"
            }
        
        self.registered_tools.add("maker.financial.create_account")
        
        # Create transaction tool
        @self.tools_system.register_tool(
            name="maker.financial.create_transaction",
            description="Create a simulated financial transaction",
            access_level=ToolAccessLevel.ADVANCED,  # Godfather mode required
            category=ToolCategory.CUSTOM
        )
        def create_transaction(
            transaction_type: str,
            amount: float,
            source: str,
            destination: str,
            description: str = ""
        ) -> Dict[str, Any]:
            """
            Create a simulated financial transaction
            
            Args:
                transaction_type: Type of transaction (e.g., 'transfer', 'payment')
                amount: Transaction amount
                source: Source account or entity
                destination: Destination account or entity
                description: Transaction description (optional)
                
            Returns:
                Dict: Information about the created transaction
            """
            logger.info(f"Creating {transaction_type} transaction: {amount} from {source} to {destination}")
            
            # Create metadata
            metadata = {
                "description": description
            }
            
            # Create the transaction
            transaction = self.financial_platform.create_transaction(
                transaction_type, amount, source, destination, metadata
            )
            
            return {
                "transaction_id": transaction["id"],
                "transaction_type": transaction_type,
                "amount": amount,
                "source": source,
                "destination": destination,
                "status": "completed"
            }
        
        self.registered_tools.add("maker.financial.create_transaction")
