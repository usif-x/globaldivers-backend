"""
Chatbot Routes - AI-powered travel & diving sales chatbot endpoints
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.chatbot import (
    generate_ai_response,
    generate_final_response,
    get_conversation_history,
    validate_promo_code,
    detect_intent,
)

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


# =============================================================================
# Request/Response Models
# =============================================================================

class ConversationRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier for the conversation")
    message: str = Field(..., description="User's message to the chatbot")


class ConversationResponse(BaseModel):
    session_id: str
    reply: str
    intent_detected: Optional[Dict[str, bool]] = None


class CompleteRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier for the conversation")


class CompleteResponse(BaseModel):
    session_id: str
    final_reply: str


class MessageHistory(BaseModel):
    role: str
    content: str
    timestamp: datetime


class ConversationHistoryResponse(BaseModel):
    session_id: str
    messages: List[MessageHistory]


class ValidatePromoRequest(BaseModel):
    code: str = Field(..., description="Promo code to validate")


class ValidatePromoResponse(BaseModel):
    valid: bool
    code: str
    discount_percent: Optional[int] = None
    description: Optional[str] = None
    message: str


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/conversation",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message and receive AI reply",
    description="""
    Send a user message to the AI chatbot and receive a personalized response.
    
    - If session_id is new, a new conversation will be created
    - If session_id exists, the message will be appended to existing conversation
    - The AI uses full conversation history to generate contextual replies
    - Automatically detects user intent (trip, course, package, discounts)
    - Recommends best-selling activities based on user preferences
    - Includes booking links when relevant
    """
)
async def conversation(request: ConversationRequest):
    """
    Send a user message and receive AI reply.
    
    The chatbot acts as a professional sales representative who:
    - Asks clarifying questions about preferences
    - Recommends best-selling trips, courses, and packages
    - Suggests promo codes when applicable
    - Provides booking links
    - Uses persuasive sales language
    """
    try:
        # Generate AI response
        ai_reply = await generate_ai_response(
            session_id=request.session_id,
            user_message=request.message
        )
        
        # Detect intent for additional insights
        intents = detect_intent(request.message)
        
        return ConversationResponse(
            session_id=request.session_id,
            reply=ai_reply,
            intent_detected=intents
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing conversation: {str(e)}"
        )


@router.post(
    "/complete",
    response_model=CompleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate final booking persuasion response",
    description="""
    Generate a final persuasive response to encourage booking completion.
    
    This endpoint analyzes the entire conversation history and creates:
    - A summary of customer needs and preferences
    - Best product recommendation based on the conversation
    - Specific booking link for the recommended product
    - Promo code validation and application
    - Urgency and scarcity messaging
    - Strong call-to-action
    """
)
async def complete(request: CompleteRequest):
    """
    Generate final AI response for booking persuasion.
    
    This creates a closing sales pitch that:
    - Summarizes what the customer wants
    - Recommends the best matching product
    - Validates any mentioned promo codes
    - Creates urgency to book now
    - Provides direct booking link
    """
    try:
        final_reply = await generate_final_response(request.session_id)
        
        return CompleteResponse(
            session_id=request.session_id,
            final_reply=final_reply
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating completion response: {str(e)}"
        )


@router.get(
    "/conversation/{session_id}",
    response_model=ConversationHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation history",
    description="""
    Retrieve the full conversation history for a given session.
    
    Returns all messages (user and assistant) stored in memory for the session.
    Note: Sessions are stored in-memory and will be lost on server restart.
    """
)
async def get_conversation(session_id: str):
    """
    Get full conversation history for the session.
    
    Returns all messages in chronological order with timestamps.
    """
    try:
        history = get_conversation_history(session_id)
        
        if not history:
            # Return empty conversation rather than 404
            return ConversationHistoryResponse(
                session_id=session_id,
                messages=[]
            )
        
        messages = [
            MessageHistory(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg.get("timestamp", datetime.now())
            )
            for msg in history
        ]
        
        return ConversationHistoryResponse(
            session_id=session_id,
            messages=messages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversation: {str(e)}"
        )


@router.post(
    "/validate-promo",
    response_model=ValidatePromoResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate a promo code",
    description="""
    Validate if a promo code is active and available.
    
    Returns discount percentage and description if valid.
    """
)
async def validate_promo(request: ValidatePromoRequest):
    """
    Validate a promo code.
    
    Checks if the code exists and is currently active.
    """
    try:
        promo = validate_promo_code(request.code)
        
        if promo:
            return ValidatePromoResponse(
                valid=True,
                code=promo["code"],
                discount_percent=promo["discount_percent"],
                description=promo["description"],
                message=f"Promo code '{promo['code']}' is valid! You get {promo['discount_percent']}% off."
            )
        else:
            return ValidatePromoResponse(
                valid=False,
                code=request.code.upper(),
                message=f"Sorry, promo code '{request.code}' is invalid or expired."
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating promo code: {str(e)}"
        )
