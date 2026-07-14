"""
Azure OpenAI Service Provider adapter.
"""

from typing import Any, Dict, List
from core.config import get_settings
from core.logging import get_logger
from adapters.ai.ai_provider import BaseAIProvider

try:
    from openai import AsyncAzureOpenAI
except ImportError:
    AsyncAzureOpenAI = None

settings = get_settings()
logger = get_logger(__name__)


class AzureOpenAIAdapter(BaseAIProvider):
    """
    Concrete AI provider utilizing Microsoft Azure OpenAI service.
    Falls back to a local mock generator if credentials are missing or
    the openai package is not installed.
    """

    def __init__(self):
        self.api_key = settings.azure_openai_api_key
        self.endpoint = settings.azure_openai_endpoint
        self.deployment = settings.azure_openai_deployment_name
        self.api_version = settings.azure_openai_api_version
        
        self.client = None
        if AsyncAzureOpenAI and self.api_key and self.endpoint and self.deployment:
            try:
                self.client = AsyncAzureOpenAI(
                    api_key=self.api_key,
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint
                )
                logger.info("Azure OpenAI client initialized successfully.")
            except Exception as e:
                logger.error("Failed to initialize Azure OpenAI client: %s", e)

    async def generate_response(
        self, 
        query: str, 
        context_chunks: List[Dict[str, Any]], 
        system_instruction: str | None = None
    ) -> str:
        # Build prompt content from chunks
        context_text = "\n\n".join([
            f"[Source: {c['metadata'].get('filename', 'Unknown')}]\n{c['text']}" 
            for c in context_chunks
        ])

        system_prompt = system_instruction or (
            "You are an enterprise AI assistant for Maruti Suzuki India Limited.\n"
            "Use the provided context to answer the user's question accurately.\n"
            "If the context does not contain enough information to answer, abstain.\n"
            "Cite files dynamically."
        )

        user_prompt = (
            f"Context details:\n{context_text}\n\n"
            f"User Query: {query}\n\n"
            f"Provide a grounded, direct answer citing the sources."
        )

        if self.client:
            try:
                response = await self.client.chat.completions.create(
                    model=self.deployment,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error("Azure OpenAI completion call failed: %s. Falling back.", e)

        # Local mock generator (fallback)
        logger.warning("Using local mock generator fallback.")
        if not context_chunks:
            return "I do not have enough verified information to answer your request."
            
        best_match = context_chunks[0]
        filename = best_match["metadata"].get("filename", "SOP manual")
        return (
            f"Based on the Maruti Suzuki reference document [{filename}], "
            f"here is the information: {best_match['text'][:250]}..."
        )
