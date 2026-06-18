# ============================================================
# Grand Palms Hotel — MCP Server
# Project 2: Tool Design & MCP Integration (Domain 2)
#
# This server exposes hotel data as MCP tools that any
# Claude-powered application can discover and use.
#
# Transport: stdio (local development)
# Protocol: JSON-RPC 2.0 (handled by SDK)
# Auth: none (local) — add API key layer for production
#
# Cost architecture:
#   - Tool descriptions are sent on every tools/list call
#   - Keep them precise — every word is tokens downstream
#   - PMS responses cached at this layer (added in Pass 2)
# ============================================================

from mcp.server.fastmcp import FastMCP
from typing import Optional
import json

# FastMCP is the high-level SDK interface
# It handles JSON-RPC framing, handshake, tools/list, tools/call
# You just write functions
mcp = FastMCP("grand-palms-hotel")


# ============================================================
# SIMULATED PMS (Property Management System)
# In production: replace these with real PMS API calls
# Opera, Maestro, Cloudbeds, Apaleo, etc.
# ============================================================

RESERVATIONS = {
    "412": {
        "guest_name": "Marcus Johnson",
        "confirmation": "GP-2024-8821",
        "check_in": "2024-12-18",
        "check_out": "2024-12-21",
        "room_type": "Double Double",
        "requested_room_type": "King",
        "rate": 289.00,
        "loyalty_tier": "Gold",
        "special_requests": "King bed - medical (back condition)",
        "balance_due": 0.00
    },
    "215": {
        "guest_name": "Sarah Chen",
        "confirmation": "GP-2024-9103",
        "check_in": "2024-12-19",
        "check_out": "2024-12-22",
        "room_type": "King Suite",
        "requested_room_type": "King Suite",
        "rate": 459.00,
        "loyalty_tier": "Platinum",
        "special_requests": "",
        "balance_due": 459.00
    },
    "301": {
        "guest_name": "Robert Martinez",
        "confirmation": "GP-2024-7734",
        "check_in": "2024-12-17",
        "check_out": "2024-12-20",
        "room_type": "Ocean View King",
        "requested_room_type": "Ocean View King",
        "rate": 389.00,
        "loyalty_tier": "Silver",
        "special_requests": "Anniversary - flowers requested",
        "balance_due": 389.00
    }
}

ROOM_INVENTORY = {
    "king_available": 0,
    "king_suite_available": 1,
    "double_double_available": 8,
    "ocean_view_king_available": 2,
}

RESORT_INFO = {
    "pool": {
        "closes": "10:00 PM",
        "opens": "7:00 AM",
        "heated": True,
        "adult_only_hours": "8:00 PM - 10:00 PM"
    },
    "restaurant": {
        "name": "The Palms Grille",
        "breakfast": "7:00 AM - 11:00 AM",
        "lunch": "12:00 PM - 3:00 PM",
        "dinner": "5:00 PM - 11:00 PM",
        "dress_code": "Smart casual"
    },
    "spa": {
        "name": "Serenity Spa",
        "opens": "8:00 AM",
        "closes": "9:00 PM",
        "booking": "Call ext. 4400 or book at front desk"
    },
    "checkin_time": "4:00 PM",
    "checkout_time": "11:00 AM",
    "wifi_password": "GrandPalms2024"
}

GUEST_PROFILES = {
    "GP-GOLD-8821": {
        "guest_name": "Marcus Johnson",
        "loyalty_number": "GP-GOLD-8821",
        "tier": "Gold",
        "points_balance": 45200,
        "stays_this_year": 8,
        "preferred_room": "King",
        "dietary": "None on file",
        "past_issues": ["Room type mismatch 2023-08"],
        "total_lifetime_stays": 23
    },
    "GP-PLAT-9103": {
        "guest_name": "Sarah Chen",
        "loyalty_number": "GP-PLAT-9103",
        "tier": "Platinum",
        "points_balance": 128500,
        "stays_this_year": 22,
        "preferred_room": "King Suite",
        "dietary": "Vegetarian",
        "past_issues": [],
        "total_lifetime_stays": 67
    }
}


# ============================================================
# MCP TOOLS
# The @mcp.tool() decorator registers each function as a tool.
# The SDK generates JSON schema from type hints automatically.
# The docstring becomes the tool description — keep it precise.
#
# EXAM PATTERN: 4-5 tools per agent max for optimal selection.
# We have 4 here — deliberate.
# ============================================================

@mcp.tool()
def get_reservation(room_number: str) -> str:
    """
    Look up a guest reservation by room number. Returns guest name,
    confirmation number, check-in/out dates, room type, loyalty tier,
    special requests, and balance due. Use when guest asks about their
    booking, checkout time, or reservation details.
    """
    if room_number not in RESERVATIONS:
        return json.dumps({
            "isError": True,
            "errorCategory": "not_found",
            "isRetryable": False,
            "context": f"No active reservation for room {room_number}"
        })

    return json.dumps({
        "isError": False,
        **RESERVATIONS[room_number]
    })


@mcp.tool()
def get_room_availability(room_type: Optional[str] = None) -> str:
    """
    Get current room availability across all room types, or filter by
    a specific type. Room types: king, king_suite, double_double,
    ocean_view_king. Use when handling room change requests or
    checking upgrade options.
    """
    if room_type:
        key = f"{room_type.lower().replace(' ', '_')}_available"
        count = ROOM_INVENTORY.get(key)
        if count is None:
            return json.dumps({
                "isError": True,
                "errorCategory": "invalid_room_type",
                "isRetryable": False,
                "context": f"Unknown room type: {room_type}. "
                           f"Valid types: king, king_suite, "
                           f"double_double, ocean_view_king"
            })
        return json.dumps({
            "isError": False,
            "room_type": room_type,
            "available": count
        })

    return json.dumps({
        "isError": False,
        **ROOM_INVENTORY
    })


@mcp.tool()
def get_resort_info(category: Optional[str] = None) -> str:
    """
    Get Grand Palms Resort operational information. Categories:
    pool, restaurant, spa, or omit for all info including
    check-in/out times and wifi. Use for guest questions about
    amenities, hours, and resort services.
    """
    if category:
        info = RESORT_INFO.get(category.lower())
        if not info:
            return json.dumps({
                "isError": True,
                "errorCategory": "invalid_category",
                "isRetryable": False,
                "context": f"Unknown category: {category}. "
                           f"Valid: pool, restaurant, spa"
            })
        info_dict = info if isinstance(info, dict) else {"value": info}
        return json.dumps({
            "isError": False,
            "category": category,
            **info_dict
        })

    return json.dumps({
        "isError": False,
        **RESORT_INFO
    })


@mcp.tool()
def get_guest_profile(loyalty_number: str) -> str:
    """
    Retrieve a guest's loyalty profile including tier, points balance,
    stay history, preferences, and past issues. Use when handling
    loyalty inquiries, personalization, or escalation decisions
    that require guest history context.
    """
    profile = GUEST_PROFILES.get(loyalty_number)
    if not profile:
        return json.dumps({
            "isError": True,
            "errorCategory": "not_found",
            "isRetryable": False,
            "context": f"No loyalty profile found for {loyalty_number}"
        })

    return json.dumps({
        "isError": False,
        **profile
    })


# ============================================================
# SERVER ENTRY POINT
# stdio transport for local development and Claude Code
# ============================================================

if __name__ == "__main__":
    print("Grand Palms Hotel MCP Server starting...")
    print("Transport: stdio")
    print("Waiting for MCP client connection...")
    mcp.run(transport="stdio")