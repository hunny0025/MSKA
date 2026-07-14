"""
Factory for initializing the active AI provider based on settings.
"""

from core.config import get_settings
from adapters.ai.ai_provider import BaseAIProvider
from adapters.ai.azure_openai_adapter import AzureOpenAIAdapter
from adapters.ai.copilot_studio_adapter import CopilotStudioConnectorAdapter
from adapters.ai.mock_adapter import MockAIProvider

settings = get_settings()


def get_ai_provider() -> BaseAIProvider:
    """
    Returns the configured AI Provider instance.
    """
    provider_name = settings.ai_provider.lower().strip()
    
    if provider_name == "copilot_studio":
        return CopilotStudioConnectorAdapter()
    
    if provider_name == "mock":
        return MockAIProvider()
        
    # Default to Azure OpenAI
    return AzureOpenAIAdapter()


# Active singleton instance
ai_provider = get_ai_provider()
