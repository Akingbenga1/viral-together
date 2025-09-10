import ollama
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings
import json

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.model = settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_BASE_URL
        
    async def generate_response(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using Ollama with conversation history and context
        """
        try:
            # Prepare conversation history for Ollama
            messages = []
            
            # Add system context if provided
            if context:
                system_context = self._build_system_context(context)
                messages.append({
                    "role": "system",
                    "content": system_context
                })
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:  # Limit to last 10 messages
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            logger.info(f"🤖 CHAT: Sending {len(messages)} messages to Ollama")
            
            # Call Ollama with custom base URL
            client = ollama.Client(host=self.base_url)
            response = client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 1000,
                    "stop": ["<|endoftext|>", "<|im_end|>"]
                }
            )

            logger.info(f"🤖 CHAT: Response: {response}")
            
            if response and "message" in response:
                assistant_message = response["message"]["content"]
                logger.info(f"🤖 CHAT: Received response ({len(assistant_message)} chars)")
                
                return {
                    "success": True,
                    "message": assistant_message,
                    "model": self.model,
                    "tokens_used": response.get("usage", {}).get("total_tokens", 0)
                }
            else:
                logger.error("🤖 CHAT: Invalid response format from Ollama")
                return {
                    "success": False,
                    "message": "Sorry, I couldn't generate a response at the moment.",
                    "error": "Invalid response format"
                }
                
        except Exception as e:
            logger.error(f"🤖 CHAT: Error generating response: {str(e)}")
            return {
                "success": False,
                "message": "Sorry, I'm experiencing technical difficulties. Please try again later.",
                "error": str(e)
            }
    
    def _build_system_context(self, context: Dict[str, Any]) -> str:
        """
        Build system context for the AI based on available information
        """
        context_parts = []
        
        # Language enforcement - must be first
        context_parts.append("LANGUAGE: ENGLISH ONLY. Respond in English language exclusively.")
        context_parts.append("")
        
        # Core identity and language instruction
        context_parts.append("You are a professional customer support AI assistant for Viral Together, an influencer marketing platform.")
        context_parts.append("CRITICAL LANGUAGE REQUIREMENT: You MUST respond ONLY in English language. Do not use any other language including Chinese, Spanish, French, or any other non-English language.")
        context_parts.append("Even if the user writes in another language, you must respond in English only.")
        context_parts.append("Your communication style should be warm, professional, and customer-service oriented.")
        
        # Customer support role definition
        context_parts.append("\nAs a customer support AI assistant, your primary responsibilities are:")
        context_parts.append("- Providing clear, helpful answers to user questions")
        context_parts.append("- Offering step-by-step guidance for platform features")
        context_parts.append("- Troubleshooting common issues and problems")
        context_parts.append("- Escalating complex issues to human support when necessary")
        context_parts.append("- Maintaining a positive, solution-focused approach")
        
        # Platform-specific knowledge areas
        context_parts.append("\nYou are knowledgeable about Viral Together's platform features:")
        context_parts.append("- Platform features and functionality")
        context_parts.append("- Account management and settings")
        context_parts.append("- Influencer and business collaboration processes")
        context_parts.append("- Technical support and troubleshooting")
        context_parts.append("- Billing and subscription questions")
        context_parts.append("- Content guidelines and policies")
        context_parts.append("- Rate card management and pricing")
        context_parts.append("- Social media platform integrations")
        
        # Customer service best practices
        context_parts.append("\nCustomer service guidelines:")
        context_parts.append("- Always greet users warmly and acknowledge their question")
        context_parts.append("- Provide specific, actionable answers")
        context_parts.append("- If you don't know something, suggest contacting support or checking the help center")
        context_parts.append("- Offer to help with follow-up questions")
        context_parts.append("- Use a friendly, professional tone")
        context_parts.append("- Keep responses concise but comprehensive")
        
        # Add specific context if provided
        if context.get("user_type"):
            context_parts.append(f"\nUser type: {context['user_type']}")
        
        if context.get("user_id"):
            context_parts.append(f"User ID: {context['user_id']}")
        
        if context.get("current_page"):
            context_parts.append(f"Current page: {context['current_page']}")
        
        # Closing instruction
        context_parts.append("\nFINAL REMINDER: You must respond in ENGLISH ONLY. No other languages are permitted.")
        context_parts.append("Be helpful and professional, and focus on providing excellent customer support in English.")
        
        return "\n".join(context_parts)
    
    async def get_chat_suggestions(self, user_type: str = "general") -> List[str]:
        """
        Get suggested questions based on user type
        """
        suggestions = {
            "influencer": [
                "How do I create an effective profile?",
                "How do I set up my rate cards?",
                "How does the collaboration process work?",
                "How and when do I get paid?",
                "How can I increase my visibility to brands?"
            ],
            "business": [
                "How do I find the right influencers?",
                "How do I create effective promotions?",
                "How does influencer pricing work?",
                "How do I measure campaign success?",
                "What are the best practices for collaborations?"
            ],
            "general": [
                "What is Viral Together?",
                "How do I create an account?",
                "What are the different subscription plans?",
                "How do I contact support?",
                "Where can I find help documentation?"
            ]
        }
        
        return suggestions.get(user_type, suggestions["general"])
