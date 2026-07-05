import json
import logging
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings

from .chat_tools import (
    check_activity_availability,
    get_active_coupons,
    get_best_selling_courses,
    get_best_selling_items,
    get_best_selling_trips,
    get_blog_posts,
    get_bundle_offers,
    get_course_by_id,
    get_course_contents,
    get_courses,
    get_dashboard_data,
    get_dive_center_info,
    get_gallery_images,
    get_package_by_id,
    get_packages,
    get_public_notifications,
    get_testimonials,
    get_transfer_zones,
    get_trip_by_id,
    get_trip_fees,
    get_trip_transfer_fees,
    get_user_invoices,
    get_user_notifications,
    get_user_profile,
    get_user_subscribed_courses,
    get_website_settings,
    search_all_products,
    search_courses,
    search_trips,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert, friendly travel sales agent for TopDivers, a premier diving and travel company based in Hurghada, Egypt. You are a world-class sales consultant who deeply understands every product, service, and detail the company offers. Your goal is to maximize customer satisfaction and bookings.

PERSONALITY & TONE:
- Warm, enthusiastic, and deeply knowledgeable about every aspect of the business
- A persuasive sales consultant who listens carefully and matches customers to perfect experiences
- Proactive about suggesting upgrades, bundles, packages, and complementary activities
- Confident and trustworthy — you know the inventory inside and out

YOUR KNOWLEDGE BASE:
You have access to ALL company data in real-time through tools. You MUST use tools instead of guessing.

TRIPS & ACTIVITIES:
- Best-selling trips/courses ranked by sales
- Search trips by keyword, price, or features
- Trip details: full info including included/not included, terms, images, discounts
- Trip fees: mandatory and optional add-on fees
- Transfer fees & zones: transportation from hotels to trip locations

COURSES & EDUCATION:
- All diving courses: prices, levels, providers (PADI/SSI), durations, types
- Course search: filter by keyword, level, type, or provider
- Course details: full description, certification, online content
- Course curriculum: modules, lessons, content types per course

PACKAGES, BUNDLES & DEALS:
- Travel packages bundling multiple trips
- Package details with full trip listings and prices
- Bundle offers: cross-trip discounts when booking together
- Active coupon/promo codes: discount percentages, remaining uses, expiry dates

DIVE CENTER & WEBSITE:
- Dive center: location, phone, email, working hours, photos
- Website settings: currency (EGP), WhatsApp, social media, contact email
- Gallery: all website images and media

CONTENT & SOCIAL PROOF:
- Blog posts: latest articles, filterable by tag
- Testimonials: customer reviews with ratings and names
- Public notifications: current announcements and offers

PAY METHODS:
- All payments are processed securely through the website for online after booking trip auto forword to payment gateway. We accept credit cards, debit cards, Apple Pay, Meeza Prepaid Card (Egypt), Mobile Wallet (Egypt) and cash money (select pay at diving center while booking) .

AVAILABILITY:
- Date availability checks for any trip or course

UNIVERSAL SEARCH:
- Search ALL products at once (trips, courses, packages) with a single query
- Get dashboard overview: total counts of trips, courses, packages, testimonials

FOR AUTHENTICATED USERS:
- User profile: name, email
- User invoices: full booking history with amounts, payment status, payment methods
- User subscribed courses: enrolled courses
- User notifications: personal messages and alerts

BOOKING INFORMATION RULES:
1. When discussing prices, always state the currency. All prices on the website are in EGP (Egyptian Pounds). If a customer asks about other currencies, tell them we handle currency conversion at booking time. Mention if a child price is different.
2. Always check real-time data — NEVER invent prices, discounts, or availability.
3. For bundled savings: check package and bundle offers to find the best value for the customer.
4. Mention transfer/transportation options and fees when discussing trips.
5. Use testimonials and social proof to build confidence.
6. For authenticated users asking about their bookings: use get_user_invoices to check their history.
7. If the user asks about account-specific info and is not authenticated, ask them to log in.

SALES STRATEGY:
- Understand the customer's needs first (experience level, group size, budget, interests)
- Recommend the best-matching option from real data
- Mention specific prices, durations, and what's included
- Suggest complementary add-ons (e.g., transfer, courses, additional trips)
- Highlight current deals, bundles, and discounts
- ALWAYS include relevant frontend links in your responses using the FRONTEND_URL
- End with a clear call-to-action or a question to continue the conversation

FRONTEND LINK GUIDE — Use these URL patterns in your responses:

Products:
- {frontend_url}/trips — Browse all trips
- {frontend_url}/trips/{id} — Specific trip details & booking
- {frontend_url}/courses — Browse all courses
- {frontend_url}/courses/{id} — Specific course details
- {frontend_url}/courses/{id}/enroll — Enroll in a course
- {frontend_url}/courses/{id}/inquire — Inquire about a course
- {frontend_url}/packages — Browse all packages
- {frontend_url}/packages/{id} — Specific package details
- {frontend_url}/bestsellers — Best-selling trips & courses

Information:
- {frontend_url}/blog — Read articles & diving guides
- {frontend_url}/blog/{title} — Specific blog post
- {frontend_url}/dive-sites — Explore dive sites
- {frontend_url}/destinations — Travel destinations
- {frontend_url}/divingcenter-locations — Dive center locations
- {frontend_url}/divingcenter-locations/{id} — Specific location
- {frontend_url}/safety-guidelines — Diving safety information
- {frontend_url}/contact — Contact & find us

Account & Booking:
- {frontend_url}/profile — User profile (require login)
- {frontend_url}/invoices — Booking history (require login)
- {frontend_url}/invoices/{id} — Specific invoice (require login)
- {frontend_url}/fast-invoice-checker — Quick invoice lookup
- {frontend_url}/login — Login page
- {frontend_url}/register — Create an account
- {frontend_url}/privacy-policy — Privacy policy
- {frontend_url}/terms-and-conditions — Terms & conditions

ABOUT HURGHADA:
Hurghada is one of the world's premier diving destinations on the Red Sea. Year-round diving, crystal-clear waters, vibrant coral reefs, and diverse marine life including dolphins, sea turtles, and reef sharks. Popular spots include Giftun Island, Abu Ramada, and the famous SS Thistlegorm wreck.
"""

TOOL_DEFINITIONS = [
    # =========================================================================
    # Trip Tools
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_best_selling_trips",
            "description": "Get the most popular/best-selling trips ranked by sales. Use this first to recommend top options.",
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
            "description": "Search for trips by keyword, price range, or features. Use when a customer asks about specific activities or has budget constraints.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g. 'snorkeling', 'dolphin', 'sunset', 'parasailing')",
                    },
                    "price_min": {
                        "type": "number",
                        "description": "Minimum price filter in EGP (Egyptian Pounds)",
                    },
                    "price_max": {
                        "type": "number",
                        "description": "Maximum price filter in EGP (Egyptian Pounds)",
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
            "name": "get_trip_by_id",
            "description": "Get detailed information about a specific trip by its ID. Includes included/not included items, terms, images, and discount details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "trip_id": {
                        "type": "integer",
                        "description": "The trip ID to look up",
                    }
                },
                "required": ["trip_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trip_fees",
            "description": "Get all mandatory and optional add-on fees for a specific trip (e.g. national park fees, equipment rental, insurance).",
            "parameters": {
                "type": "object",
                "properties": {
                    "trip_id": {
                        "type": "integer",
                        "description": "The trip ID to get fees for",
                    }
                },
                "required": ["trip_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_transfer_zones",
            "description": "Get all available hotel/resort zones for pickup and transfer to trip locations.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trip_transfer_fees",
            "description": "Get transfer/transportation prices for a specific trip from different hotel zones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "trip_id": {
                        "type": "integer",
                        "description": "The trip ID to get transfer prices for",
                    }
                },
                "required": ["trip_id"],
            },
        },
    },
    # =========================================================================
    # Course Tools
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_courses",
            "description": "Get all available diving courses (e.g. Open Water, Advanced, Rescue, Instructor) with prices, levels, providers, and duration.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_best_selling_courses",
            "description": "Get the most popular/best-selling courses ranked by sales.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of courses to return (default 5, max 10)",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_courses",
            "description": "Search for diving courses by keyword, level, type, or provider (e.g. PADI, SSI).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g. 'Open Water', 'Advanced', 'Rescue')",
                    },
                    "level": {
                        "type": "string",
                        "description": "Filter by course level (e.g. 'Beginner', 'Advanced', 'Professional')",
                    },
                    "course_type": {
                        "type": "string",
                        "description": "Filter by course type (e.g. 'Diving', 'Snorkeling', 'First Aid')",
                    },
                    "provider": {
                        "type": "string",
                        "description": "Filter by certification provider (e.g. 'PADI', 'SSI')",
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
            "name": "get_course_by_id",
            "description": "Get detailed information about a specific course by its ID, including full description, images, and discount info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "integer",
                        "description": "The course ID to look up",
                    }
                },
                "required": ["course_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_course_contents",
            "description": "Get the curriculum/modules/lessons for a specific course. Use when a customer asks what they will learn in a course.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "integer",
                        "description": "The course ID to get contents for",
                    }
                },
                "required": ["course_id"],
            },
        },
    },
    # =========================================================================
    # Package & Bundle Tools
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_packages",
            "description": "Get available travel packages that bundle multiple trips together at a better value. Optionally filter by a specific trip ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "trip_id": {
                        "type": "integer",
                        "description": "Optional trip ID to find packages that include this trip",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_package_by_id",
            "description": "Get full details of a travel package including all trips it contains with their prices.",
            "parameters": {
                "type": "object",
                "properties": {
                    "package_id": {
                        "type": "integer",
                        "description": "The package ID to look up",
                    }
                },
                "required": ["package_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_bundle_offers",
            "description": "Get special bundle discount offers. These are deals where booking specific trips together unlocks discounts (e.g. book trip A and get discount on trip B).",
            "parameters": {
                "type": "object",
                "properties": {
                    "trip_id": {
                        "type": "integer",
                        "description": "Optional trip ID to find bundle offers that include this trip",
                    },
                },
            },
        },
    },
    # =========================================================================
    # Dive Center & Info Tools
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_dive_center_info",
            "description": "Get information about the dive center including location, phone, email, working hours, and description.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_website_settings",
            "description": "Get website contact information including phone, WhatsApp, email, social media links, and default currency. Use this find out what currency prices are displayed in.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    # =========================================================================
    # Content & Social Proof Tools
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_blog_posts",
            "description": "Get recent blog posts about diving in Hurghada, travel tips, and company updates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of posts to return (default 5)",
                    },
                    "tag": {
                        "type": "string",
                        "description": "Optional tag filter (e.g. 'diving', 'tips', 'news')",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_testimonials",
            "description": "Get customer reviews and testimonials with ratings. Use for social proof when recommending trips.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of testimonials to return (default 10)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_public_notifications",
            "description": "Get current announcements, offers, and important notifications published on the website.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of notifications to return (default 5)",
                    },
                },
            },
        },
    },
    # =========================================================================
    # Availability Tools
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "check_activity_availability",
            "description": "Check if a specific trip or course is available on a given date. Use before recommending a booking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "activity_type": {
                        "type": "string",
                        "description": "Type of activity: 'trip' or 'course'",
                    },
                    "activity_id": {
                        "type": "integer",
                        "description": "The trip or course ID to check",
                    },
                    "check_date": {
                        "type": "string",
                        "description": "Date to check in YYYY-MM-DD format",
                    },
                },
                "required": ["activity_type", "activity_id", "check_date"],
            },
        },
    },
    # =========================================================================
    # User Tools
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "Get the current authenticated user's profile information (name and email). Only call when the user asks about their account.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_invoices",
            "description": "Get the current authenticated user's booking/invoice history with amounts, statuses, and payment info. Only call when the user asks about their bookings.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_subscribed_courses",
            "description": "Get the current authenticated user's enrolled/subscribed courses. Only call when the user asks about their courses.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_notifications",
            "description": "Get the current authenticated user's personal notifications and alerts. Only call when the user asks about their notifications.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    # =========================================================================
    # Coupon Tools
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_active_coupons",
            "description": "Get all active promo/discount codes. Use to tell customers about current deals. Optionally filter by activity type (trip, course, all).",
            "parameters": {
                "type": "object",
                "properties": {
                    "activity": {
                        "type": "string",
                        "description": "Optional filter: 'trip', 'course', or 'all'",
                    },
                },
            },
        },
    },
    # =========================================================================
    # Gallery & Media Tools
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_gallery_images",
            "description": "Get website gallery images and media. Use when a customer asks to see photos of the location, trips, or dive center.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of images to return (default 20)",
                    },
                },
            },
        },
    },
    # =========================================================================
    # Comprehensive Search Tools
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_best_selling_items",
            "description": "Get BOTH best-selling trips AND best-selling courses in one call. Use when you want a quick overview of what's most popular.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of items per category (default 5)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_all_products",
            "description": "Universal search across ALL products (trips, courses, and packages) at once. Use when the customer has a general query and you want to see everything available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g. 'snorkeling', 'beginner', 'family')",
                    },
                    "price_min": {
                        "type": "number",
                        "description": "Minimum price filter in EGP",
                    },
                    "price_max": {
                        "type": "number",
                        "description": "Maximum price filter in EGP",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results per category (default 5)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dashboard_data",
            "description": "Get overview counts of all products: total trips, courses, packages, and testimonials. Use for a quick summary of what's available.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


async def _run_tool(
    name: str, args: dict, auth_user_id: Optional[int], db: Session
) -> Any:
    safe_args = {k: v for k, v in args.items()}
    logger.info("Tool call: %s args=%s", name, safe_args)

    # Trip tools
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
    elif name == "get_trip_by_id":
        return get_trip_by_id(db, trip_id=args["trip_id"])
    elif name == "get_trip_fees":
        return get_trip_fees(db, trip_id=args["trip_id"])
    elif name == "get_transfer_zones":
        return get_transfer_zones(db)
    elif name == "get_trip_transfer_fees":
        return get_trip_transfer_fees(db, trip_id=args["trip_id"])

    # Course tools
    elif name == "get_courses":
        return get_courses(db)
    elif name == "get_best_selling_courses":
        return get_best_selling_courses(db, limit=min(args.get("limit", 5), 10))
    elif name == "search_courses":
        return search_courses(
            db,
            query=args.get("query", ""),
            level=args.get("level"),
            course_type=args.get("course_type"),
            provider=args.get("provider"),
            limit=min(args.get("limit", 10), 20),
        )
    elif name == "get_course_by_id":
        return get_course_by_id(db, course_id=args["course_id"])
    elif name == "get_course_contents":
        return get_course_contents(db, course_id=args["course_id"])

    # Package & Bundle tools
    elif name == "get_packages":
        return get_packages(db, trip_id=args.get("trip_id"))
    elif name == "get_package_by_id":
        return get_package_by_id(db, package_id=args["package_id"])
    elif name == "get_bundle_offers":
        return get_bundle_offers(db, trip_id=args.get("trip_id"))

    # Dive Center & Info tools
    elif name == "get_dive_center_info":
        return get_dive_center_info(db)
    elif name == "get_website_settings":
        return get_website_settings(db)

    # Content & Social Proof tools
    elif name == "get_blog_posts":
        return get_blog_posts(
            db, limit=min(args.get("limit", 5), 20), tag=args.get("tag")
        )
    elif name == "get_testimonials":
        return get_testimonials(db, limit=min(args.get("limit", 10), 50))
    elif name == "get_public_notifications":
        return get_public_notifications(db, limit=min(args.get("limit", 5), 20))

    # Availability tools
    elif name == "check_activity_availability":
        return check_activity_availability(
            db,
            activity_type=args["activity_type"],
            activity_id=args["activity_id"],
            check_date=args["check_date"],
        )

    # User tools
    elif name == "get_user_profile":
        if auth_user_id is None:
            return {"_error": "Authentication required. Ask the user to log in first."}
        return get_user_profile(db, auth_user_id)
    elif name == "get_user_invoices":
        if auth_user_id is None:
            return {"_error": "Authentication required. Ask the user to log in first."}
        return get_user_invoices(db, auth_user_id)
    elif name == "get_user_subscribed_courses":
        if auth_user_id is None:
            return {"_error": "Authentication required. Ask the user to log in first."}
        return get_user_subscribed_courses(db, auth_user_id)
    elif name == "get_user_notifications":
        if auth_user_id is None:
            return {"_error": "Authentication required. Ask the user to log in first."}
        return get_user_notifications(
            db, auth_user_id, limit=min(args.get("limit", 20), 50)
        )

    # Coupon tools
    elif name == "get_active_coupons":
        return get_active_coupons(db, activity=args.get("activity"))

    # Gallery tools
    elif name == "get_gallery_images":
        return get_gallery_images(db, limit=min(args.get("limit", 20), 50))

    # Comprehensive search tools
    elif name == "get_best_selling_items":
        return get_best_selling_items(db, limit=min(args.get("limit", 5), 10))
    elif name == "search_all_products":
        return search_all_products(
            db,
            query=args.get("query", ""),
            price_min=args.get("price_min"),
            price_max=args.get("price_max"),
            limit=min(args.get("limit", 5), 10),
        )
    elif name == "get_dashboard_data":
        return get_dashboard_data(db)

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

    from app.core.config import settings as app_settings

    system_prompt = SYSTEM_PROMPT.replace("{frontend_url}", app_settings.FRONTEND_URL)

    openai_messages = [{"role": "system", "content": system_prompt}]
    for m in messages:
        if m["role"] in ("user", "assistant"):
            openai_messages.append({"role": m["role"], "content": m["content"]})

    max_rounds = 10

    async with httpx.AsyncClient(timeout=60.0) as client:
        for _ in range(max_rounds):
            body = {
                "model": model,
                "max_tokens": 2048,
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

            openai_messages.append(
                {"role": "assistant", "content": content, "tool_calls": tool_calls}
            )

            for tc in tool_calls:
                tool_name = tc["function"]["name"]
                tool_args = json.loads(tc["function"]["arguments"])
                result = await _run_tool(tool_name, tool_args, auth_user_id, db)
                result_json = json.dumps(result, default=str)
                openai_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result_json,
                    }
                )

    return "I've gathered all the information I need. How else can I help you?"
