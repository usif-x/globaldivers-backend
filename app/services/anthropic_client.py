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

ANTHROPIC_API_URL = "https://api.deepseek.com/anthropic"
ANTHROPIC_VERSION = "2026-06-01"

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
        "name": "get_best_selling_trips",
        "description": "Get the most popular/best-selling trips. Use this to recommend top options to customers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of trips to return (default 5, max 10)",
                }
            },
        },
    },
    {
        "name": "search_trips",
        "description": "Search for trips by keyword, price range, or features. Use this when a customer asks about specific activities or has budget constraints.",
        "input_schema": {
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
    {
        "name": "get_packages",
        "description": "Get available travel packages that bundle multiple trips together. Optionally filter by a specific trip ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "trip_id": {
                    "type": "integer",
                    "description": "Optional trip ID to filter packages that include this trip",
                },
            },
        },
    },
    {
        "name": "get_courses",
        "description": "Get all available diving courses (e.g. Open Water, Advanced, Rescue) with prices and details.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_user_profile",
        "description": "Get the current user's profile information (name and email). Only call when the user asks about their account details.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_user_invoices",
        "description": "Get the current user's booking/invoice history. Only call when the user asks about their past or current bookings.",
        "input_schema": {"type": "object", "properties": {}},
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
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not configured")
        return (
            "I'm sorry, the AI chat service is not configured. Please contact support."
        )

    model = settings.ANTHROPIC_MODEL

    anthropic_messages = []
    for m in messages:
        if m["role"] in ("user", "assistant"):
            anthropic_messages.append({"role": m["role"], "content": m["content"]})

    max_rounds = 10

    async with httpx.AsyncClient(timeout=60.0) as client:
        for _ in range(max_rounds):
            body = {
                "model": model,
                "max_tokens": 1024,
                "system": SYSTEM_PROMPT,
                "messages": anthropic_messages,
                "tools": TOOL_DEFINITIONS,
            }

            resp = await client.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json=body,
            )

            if resp.status_code == 429:
                logger.warning("Anthropic API rate limited")
                return "I'm experiencing high demand right now. Please try again in a moment."

            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError:
                logger.error("Anthropic API error: %s %s", resp.status_code, resp.text)
                return (
                    "I encountered an error processing your request. Please try again."
                )

            data = resp.json()
            content_blocks = data.get("content", [])
            stop_reason = data.get("stop_reason")

            tool_uses = [b for b in content_blocks if b.get("type") == "tool_use"]

            if not tool_uses or stop_reason != "tool_use":
                text_parts = [
                    b["text"] for b in content_blocks if b.get("type") == "text"
                ]
                return "\n".join(text_parts)

            assistant_blocks = []
            tool_result_blocks = []
            for block in content_blocks:
                if block["type"] == "text":
                    assistant_blocks.append({"type": "text", "text": block["text"]})
                elif block["type"] == "tool_use":
                    tool_name = block["name"]
                    tool_args = block.get("input", {})
                    result = await _run_tool(tool_name, tool_args, auth_user_id, db)
                    assistant_blocks.append(
                        {
                            "type": "tool_use",
                            "id": block["id"],
                            "name": tool_name,
                            "input": tool_args,
                        }
                    )
                    result_json = json.dumps(result, default=str)
                    tool_result_blocks.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block["id"],
                            "content": result_json,
                        }
                    )

            anthropic_messages.append(
                {"role": "assistant", "content": assistant_blocks}
            )
            anthropic_messages.append({"role": "user", "content": tool_result_blocks})

    return "I've gathered all the information I need. How else can I help you?"
