from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.chat_service import ChatService
from app.api.auth import verify_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

chat_service = ChatService()

class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []
    context: Optional[Dict[str, Any]] = {}

class ChatResponse(BaseModel):
    success: bool
    message: str
    model: Optional[str] = None
    tokens_used: Optional[int] = 0
    error: Optional[str] = None

class ChatSuggestionsRequest(BaseModel):
    user_type: str = "general"

class ChatSuggestionsResponse(BaseModel):
    suggestions: List[str]

@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_message: ChatMessage,
    current_user: dict = Depends(verify_token)
):
    """
    Send a message to the AI chat assistant
    """
    logger.info(f"Chat message: {chat_message}")
    try:
        # Add user context
        context = chat_message.context or {}
        context.update({
            "user_id": current_user.get("id"),
            "user_type": current_user.get("user_type", "general"),
            "current_page": context.get("current_page", "contact")
        })
        
        response = await chat_service.generate_response(
            message=chat_message.message,
            conversation_history=chat_message.conversation_history,
            context=context
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Chat API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )

@router.post("/suggestions", response_model=ChatSuggestionsResponse)
async def get_suggestions(
    request: ChatSuggestionsRequest,
    current_user: dict = Depends(verify_token)
):
    """
    Get suggested questions based on user type
    """
    try:
        user_type = request.user_type or current_user.get("user_type", "general")
        suggestions = await chat_service.get_chat_suggestions(user_type)
        
        return ChatSuggestionsResponse(suggestions=suggestions)
        
    except Exception as e:
        logger.error(f"Chat suggestions API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat suggestions"
        )

@router.post("/message/public", response_model=ChatResponse)
async def send_message_public(chat_message: ChatMessage):
    """
    Send a message to the AI chat assistant (public endpoint for unauthenticated users)
    """
    try:
        # Add basic context for public users
        context = chat_message.context or {}
        context.update({
            "user_type": "general",
            "current_page": context.get("current_page", "contact")
        })
        
        response = await chat_service.generate_response(
            message=chat_message.message,
            conversation_history=chat_message.conversation_history,
            context=context
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Public chat API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )
