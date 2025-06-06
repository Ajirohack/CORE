"""
Knowledge Agent for AI Council
Specializes in retrieving and providing relevant knowledge from RAG system
"""

import logging
from typing import Dict, List, Any, Optional
import autogen
from autogen.agentchat.agent import Agent

# Import knowledge retrieval components
from core.rag_system.retrieval.knowledge_retriever import KnowledgeRetriever

# Setup logging
logger = logging.getLogger(__name__)

class KnowledgeAgent(autogen.ConversableAgent):
    """
    Knowledge Agent that specializes in retrieving relevant information 
    from knowledge bases and external sources
    """
    
    def __init__(
        self, 
        name: str, 
        system_message: str, 
        llm_config: Dict[str, Any],
        retriever_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Knowledge Agent
        
        Args:
            name: Name of the agent
            system_message: The system message that defines the agent's role
            llm_config: Configuration for the language model
            retriever_config: Configuration for the knowledge retriever
        """
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=llm_config
        )
        
        # Initialize knowledge retriever
        self.retriever_config = retriever_config or {}
        self.knowledge_retriever = KnowledgeRetriever(config=self.retriever_config)
        
        # Register retrieval functions
        self._register_functions()
        
        logger.info(f"Knowledge Agent '{name}' initialized with retriever")
    
    def _register_functions(self):
        """Register knowledge retrieval functions with the agent"""
        # Register retrieve_context function
        self.register_function(
            function_map={
                "retrieve_context": self.retrieve_context,
                "search_knowledge_base": self.search_knowledge_base,
                "add_knowledge": self.add_knowledge
            }
        )
    
    async def retrieve_context(self, query: str, max_documents: int = 5) -> str:
        """
        Retrieve relevant context for a query
        
        Args:
            query: The query to retrieve context for
            max_documents: Maximum number of documents to retrieve
            
        Returns:
            Formatted context as a string
        """
        logger.info(f"Retrieving context for: {query[:50]}...")
        
        try:
            context = self.knowledge_retriever.get_relevant_context(
                query=query, 
                max_documents=max_documents
            )
            
            if not context or context == "No relevant context found.":
                return "I don't have any specific information about this topic in my knowledge base."
                
            return f"Here's relevant information I found:\n\n{context}"
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return "I encountered an error while trying to retrieve relevant information."
    
    async def search_knowledge_base(self, query: str, k: int = 3) -> str:
        """
        Search the knowledge base for information
        
        Args:
            query: The search query
            k: Number of results to return
            
        Returns:
            Search results as a formatted string
        """
        logger.info(f"Searching knowledge base for: {query[:50]}...")
        
        try:
            results = self.knowledge_retriever.search_knowledge_base(query=query, k=k)
            
            if not results:
                return "I couldn't find any relevant information in my knowledge base."
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results):
                content = result["content"].strip()
                source = result.get("metadata", {}).get("source", "Unknown source")
                
                formatted_results.append(f"[Result {i+1}] {content}\nSource: {source}\n")
            
            return "Here are the most relevant results:\n\n" + "\n".join(formatted_results)
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return "I encountered an error while searching for information."
    
    async def add_knowledge(self, text: str, source: str = "user input") -> str:
        """
        Add new knowledge to the knowledge base
        
        Args:
            text: Text to add to the knowledge base
            source: Source of the information
            
        Returns:
            Status message
        """
        logger.info(f"Adding knowledge from {source}: {text[:50]}...")
        
        try:
            metadata = {"source": source, "added_by": self.name}
            
            doc_ids = self.knowledge_retriever.add_text_to_knowledge_base(
                text=text, 
                metadata=metadata
            )
            
            if doc_ids:
                return f"Successfully added new information to my knowledge base."
            else:
                return "I wasn't able to add this information to my knowledge base."
        except Exception as e:
            logger.error(f"Error adding knowledge: {str(e)}")
            return "I encountered an error while trying to add this information."
    
    async def _process_with_retrieval(self, message: str) -> str:
        """
        Process a message by first retrieving relevant context
        
        Args:
            message: User message to process
            
        Returns:
            Response with knowledge-enhanced context
        """
        # First, retrieve relevant context
        context = await self.retrieve_context(message)
        
        # Prepare a prompt that includes the retrieved context
        enhanced_prompt = f"""
        I need to respond to the following message:
        
        "{message}"
        
        Based on my knowledge base, I have this relevant information:
        {context}
        
        Using this information (if relevant), I should provide a helpful, accurate response.
        """
        
        # Process with LLM
        # In a real implementation, this would call the model
        # For now, we'll return a placeholder
        
        return f"Response based on retrieved knowledge: {context[:100]}..."