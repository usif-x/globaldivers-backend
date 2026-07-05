import json
import logging
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings

from .chat_tools import (
    get_best_selling_trips,
    get_courses,
    get_packages,
    get_user_invoices,
    get_user_profile,
    search_trips,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert, friendly travel sales agent for TopDivers, a premier diving and travel company based in Hurghada, Egypt. Your mission is to help customers discover and book unforgettable diving experiences, courses, and travel packages.

PERSONALITY & TONE:
- Warm, enthusiastic, and professional
- Knowledgeable about Hurghada's diving locations, marine life, and local attractions
- A persuasive sales consultant who focuses on matching customers to the perfect experience
- Comfortable suggesting upgrades, bundles, and complementary activities

CAPABILITIES:
You have access to real-time data through tools. ALWAYS use these tools instead of guessing:
- Check our best-selling trips and current inventory
- Search for specific trips by name, price range, or features
- Look up available packages and courses
- For authenticated users: check their profile and booking history

RULES:
1. NEVER invent prices, discounts, or availability — always call the appropriate tool
2. Be proactive: suggest specific trips based on what the customer shares
3. When mentioning prices, always state the currency
4. Upsell naturally: "Since you're interested in snorkeling, you might also enjoy..."
5. Bundle offers: mention package deals that combine multiple activities at a better value
6. If the user asks about account-specific info (their bookings, profile), ask them to log in if they haven't
7. Keep responses concise but informative — customers appreciate clarity
8. Always end with a question to keep the conversation flowing or a call-to-action to book
9. For common questions about Hurghada (best season, what to bring, etc.), use your general knowledge

ABOUT HURGHADA:
Hurghada is one of the world's premier diving destinations on the Red Sea. Year-round diving, crystal-clear waters, vibrant coral reefs, and diverse marine life including dolphins, sea turtles, and reef sharks. Popular spots include Giftun Island, Abu Ramada, and the famous SS Thistlegorm wreck.
"""

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_best_selling_trips",
            "description": "Get the most popular/best-selling trips. Use this to recommend top options to customers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of trips to return (default 5, max 10)",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_trips",
            "description": "Search for trips by keyword, price range, or features. Use this when a customer asks about specific activities or has budget constraints.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g. 'snorkeling', 'dolphin', 'sunset')",
                    },
                    "price_min": {
                        "type": "number",
                        "description": "Minimum price filter",
                    },
                    "price_max": {
                        "type": "number",
                        "description": "Maximum price filter",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default 10)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_packages",
            "description": "Get available travel packages that bundle multiple trips together. Optionally filter by a specific trip ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "trip_id": {
                        "type": "integer",
                        "description": "Optional trip ID to filter packages that include this trip",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_courses",
            "description": "Get all available diving courses (e.g. Open Water, Advanced, Rescue) with prices and details.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "Get the current user's profile information (name and email). Only call when the user asks about their account details.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_invoices",
            "description": "Get the current user's booking/invoice history. Only call when the user asks about their past or current bookings.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


async def _run_tool(
    name: str, args: dict, auth_user_id: Optional[int], db: Session
) -> Any:
    safe_args = {k: v for k, v in args.items()}
    logger.info("Tool call: %s args=%s", name, safe_args)

    if name == "get_best_selling_trips":
        return get_best_selling_trips(db, limit=min(args.get("limit", 5), 10))
    elif name == "search_trips":
        return search_trips(
            db,
            query=args.get("query", ""),
            price_min=args.get("price_min"),
            price_max=args.get("price_max"),
            limit=min(args.get("limit", 10), 20),
        )
    elif name == "get_packages":
        return get_packages(db, trip_id=args.get("trip_id"))
    elif name == "get_courses":
        return get_courses(db)
    elif name == "get_user_profile":
        if auth_user_id is None:
            return {"_error": "Authentication required. Ask the user to log in first."}
        return get_user_profile(db, auth_user_id)
    elif name == "get_user_invoices":
        if auth_user_id is None:
            return {"_error": "Authentication required. Ask the user to log in first."}
        return get_user_invoices(db, auth_user_id)
    else:
        return {"_error": f"Unknown tool: {name}"}


async def run_chat_turn(
    messages: list[dict],
    auth_user_id: Optional[int],
    db: Session,
) -> str:
    api_key = settings.AI_API_KEY
    if not api_key:
        logger.error("AI_API_KEY not configured")
        return (
            "I'm sorry, the AI chat service is not configured. Please contact support."
        )

    base_url = settings.AI_BASE_URL.rstrip("/")
    model = settings.AI_MODEL

    openai_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in messages:
        if m["role"] in ("user", "assistant"):
            openai_messages.append({"role": m["role"], "content": m["content"]})

    max_rounds = 10

    async with httpx.AsyncClient(timeout=60.0) as client:
        for _ in range(max_rounds):
            body = {
                "model": model,
                "max_tokens": 1024,
                "messages": openai_messages,
                "tools": TOOL_DEFINITIONS,
            }

            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )

            if resp.status_code == 429:
                logger.warning("AI API rate limited")
                return "I'm experiencing high demand right now. Please try again in a moment."

            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError:
                logger.error("AI API error: %s %s", resp.status_code, resp.text)
                return (
                    "I encountered an error processing your request. Please try again."
                )

            data = resp.json()
            choice = data["choices"][0]
            message = choice["message"]
            finish_reason = choice.get("finish_reason")
            content = message.get("content")
            tool_calls = message.get("tool_calls")

            if not tool_calls or finish_reason != "tool_calls":
                return content or ""

            openai_messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls})

            for tc in tool_calls:
                tool_name = tc["function"]["name"]
                tool_args = json.loads(tc["function"]["arguments"])
                result = await _run_tool(tool_name, tool_args, auth_user_id, db)
                result_json = json.dumps(result, default=str)
                openai_messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_json,
                })

    return "I've gathered all the information I need. How else can I help you?"
