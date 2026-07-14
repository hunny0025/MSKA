"""
Microsoft Copilot Studio Connector adapter.
"""

import asyncio
from typing import Any, Dict, List
import httpx

from core.config import get_settings
from core.logging import get_logger
from adapters.ai.ai_provider import BaseAIProvider

settings = get_settings()
logger = get_logger(__name__)


class CopilotStudioConnectorAdapter(BaseAIProvider):
    """
    Alternative adapter for programmatic integration with Microsoft 365 Copilot/Copilot Studio.
    Communicates with Copilot Studio via the Direct Line API channel.
    """

    def __init__(self):
        self.token_endpoint = settings.copilot_studio_token_endpoint
        if self.token_endpoint:
            logger.info("Copilot Studio Connector Adapter initialized with token endpoint.")
        else:
            logger.warning("Copilot Studio token endpoint not configured. Will run with mock fallback.")

    async def generate_response(
        self, 
        query: str, 
        context_chunks: List[Dict[str, Any]], 
        system_instruction: str | None = None
    ) -> str:
        # Build prompt or context description for log or if fallback is used
        context_text = "\n\n".join([
            f"[Source: {c['metadata'].get('filename', 'Unknown')}]\n{c['text']}" 
            for c in context_chunks
        ])

        if not self.token_endpoint:
            logger.warning("Using local mock generator fallback in Copilot Studio Adapter (no token endpoint set).")
            if not context_chunks:
                return "I do not have enough verified information to answer your request."
                
            best_match = context_chunks[0]
            filename = best_match["metadata"].get("filename", "SOP manual")
            return (
                f"Based on the Maruti Suzuki reference document [{filename}] (Mock Copilot fallback), "
                f"here is the information: {best_match['text'][:250]}..."
            )

        try:
            async with httpx.AsyncClient() as client:
                # 1. Exchange secret/token endpoint for Direct Line token and conversation ID
                logger.info("Fetching token from Copilot Studio token endpoint...")
                token_resp = await client.get(self.token_endpoint)
                token_resp.raise_for_status()
                token_data = token_resp.json()
                
                token = token_data.get("token") or token_data.get("conversationToken")
                conversation_id = token_data.get("conversationId")
                
                if not token:
                    raise ValueError("Failed to retrieve token from token endpoint.")
                
                # If conversationId is not returned directly, start conversation using the token
                if not conversation_id:
                    logger.info("Starting conversation via Direct Line endpoint...")
                    start_headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }
                    start_resp = await client.post(
                        "https://directline.botframework.com/v3/directline/conversations",
                        headers=start_headers
                    )
                    start_resp.raise_for_status()
                    start_data = start_resp.json()
                    conversation_id = start_data.get("conversationId")
                    token = start_data.get("token") or token

                if not conversation_id:
                    raise ValueError("Failed to establish conversation ID.")

                # 2. Send the message activity to the conversation
                logger.info("Sending message activity to conversation: %s", conversation_id)
                activity_url = f"https://directline.botframework.com/v3/directline/conversations/{conversation_id}/activities"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "type": "message",
                    "from": {
                        "id": "user-mska"
                    },
                    "text": query
                }
                
                send_resp = await client.post(activity_url, json=payload, headers=headers)
                send_resp.raise_for_status()
                
                # 3. Poll for the bot's response activities
                logger.info("Polling for Bot activities...")
                poll_url = f"https://directline.botframework.com/v3/directline/conversations/{conversation_id}/activities"
                watermark = None
                max_attempts = 30
                poll_interval = 1.0
                
                for attempt in range(max_attempts):
                    url = poll_url
                    if watermark:
                        url += f"?watermark={watermark}"
                        
                    poll_resp = await client.get(url, headers=headers)
                    poll_resp.raise_for_status()
                    poll_data = poll_resp.json()
                    
                    activities = poll_data.get("activities", [])
                    watermark = poll_data.get("watermark", watermark)
                    
                    for act in activities:
                        # Find the first message from the bot (not user-mska)
                        if act.get("type") == "message" and act.get("from", {}).get("id") != "user-mska":
                            bot_text = act.get("text")
                            if bot_text:
                                return bot_text
                            
                            # Fallback for adaptive card attachments
                            attachments = act.get("attachments", [])
                            for attachment in attachments:
                                content = attachment.get("content", {})
                                if isinstance(content, dict):
                                    text = content.get("text") or content.get("speak")
                                    if text:
                                        return text
                    
                    await asyncio.sleep(poll_interval)
                
                raise TimeoutError("Timed out waiting for response from Copilot Studio.")

        except Exception as e:
            logger.error("Error communicating with Copilot Studio API: %s", e)
            # Fallback to local mock generator if API call fails
            logger.warning("Using local mock generator fallback after error.")
            if not context_chunks:
                return f"I encountered an error communicating with the AI service: {str(e)}"
                
            best_match = context_chunks[0]
            filename = best_match["metadata"].get("filename", "SOP manual")
            return (
                f"Based on the Maruti Suzuki reference document [{filename}] (Fallback due to API error: {str(e)[:50]}), "
                f"here is the information: {best_match['text'][:250]}..."
            )

