"""
Reusable Browser-Use agent utilities
"""
import asyncio
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

from browser_use import Agent, Browser, ChatBrowserUse
from browser_use.agent.views import AgentHistoryList

import logging

logger = logging.getLogger(__name__)


class BrowserUseHelper:
    """Helper class for Browser-Use agent operations"""
    
    def __init__(
        self,
        use_cloud: bool = True,
        headless: bool = True,
        browser_use_api_key: Optional[str] = None
    ):
        """
        Initialize Browser-Use helper
        
        Args:
            use_cloud: Use Browser-Use cloud browser (recommended for production)
            headless: Run browser without UI
            browser_use_api_key: API key for Browser-Use (optional if in env)
        """
        self.use_cloud = use_cloud
        self.headless = headless
        self.browser_use_api_key = browser_use_api_key
        self.llm = ChatBrowserUse()  # Fastest & most cost-effective
    
    async def run_agent_task(
        self,
        task: str,
        output_model: Optional[Type[BaseModel]] = None,
        max_steps: int = 100,
        use_vision: bool = False,
        custom_tools: Optional[Any] = None
    ) -> AgentHistoryList:
        """
        Run a Browser-Use agent task
        
        Args:
            task: Task description for the agent
            output_model: Optional Pydantic model for structured output
            max_steps: Maximum steps the agent can take
            use_vision: Include screenshots in LLM context
            custom_tools: Optional custom tools/actions
            
        Returns:
            AgentHistoryList with execution history
        """
        # Configure browser
        browser_config = {
            "headless": self.headless,
        }
        
        # Use cloud browser if enabled (recommended for production)
        if self.use_cloud:
            browser_config["use_cloud"] = True
        
        browser = Browser(**browser_config)
        
        # Configure agent
        agent_config = {
            "task": task,
            "llm": self.llm,
            "browser": browser,
            "use_vision": use_vision,
        }
        
        if output_model:
            agent_config["output_model_schema"] = output_model
        
        if custom_tools:
            agent_config["tools"] = custom_tools
        
        agent = Agent(**agent_config)
        
        try:
            # Run agent
            logger.info(f"Starting Browser-Use agent: {task[:100]}...")
            history = await agent.run(max_steps=max_steps)
            logger.info(f"Agent completed in {history.total_duration_seconds():.2f}s")
            return history
            
        except Exception as e:
            logger.error(f"Agent error: {str(e)}")
            raise
    
    async def extract_structured_data(
        self,
        task: str,
        output_model: Type[BaseModel],
        max_steps: int = 50
    ) -> Optional[BaseModel]:
        """
        Extract structured data using Browser-Use agent
        
        Args:
            task: Task description
            output_model: Pydantic model for output validation
            max_steps: Maximum steps
            
        Returns:
            Parsed Pydantic model or None if failed
        """
        history = await self.run_agent_task(
            task=task,
            output_model=output_model,
            max_steps=max_steps
        )
        
        # Extract structured output
        result = history.final_result()
        if result:
            try:
                return output_model.model_validate_json(result)
            except Exception as e:
                logger.error(f"Failed to parse output: {e}")
                return None
        
        return None


def create_search_task(
    search_query: str,
    extract_info: str,
    max_results: int = 10
) -> str:
    """
    Create a search task prompt for Browser-Use agent
    
    Args:
        search_query: What to search for
        extract_info: What information to extract
        max_results: Maximum number of results
        
    Returns:
        Formatted task string
    """
    return f"""
    1. Search Google for: "{search_query}"
    2. Visit the top {max_results} results
    3. For each result, extract: {extract_info}
    4. Return the extracted information in structured format
    5. Use the 'done' action when complete
    """


def create_document_parsing_task(
    document_url: str,
    extract_sections: list[str]
) -> str:
    """
    Create a document parsing task for Browser-Use agent
    
    Args:
        document_url: URL of the document to parse
        extract_sections: List of sections to extract
        
    Returns:
        Formatted task string
    """
    sections_str = ", ".join(extract_sections)
    return f"""
    1. Navigate to: {document_url}
    2. Extract the following sections: {sections_str}
    3. For each section, capture the title, content, and any sub-items
    4. Return structured data with clear hierarchy
    5. Use the 'done' action when complete
    """
