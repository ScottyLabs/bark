"""Google Maps tools for Geocoding and Place Search."""

import httpx
import logging
from typing import Any

from bark.core.config import get_settings
from bark.core.tools import tool

logger = logging.getLogger(__name__)


@tool(
    name="geocode_address",
    description="Convert an address into geographic coordinates (latitude and longitude).",
    parameters={
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "The address to geocode.",
            }
        },
        "required": ["address"],
    }
)
async def geocode_address(address: str) -> str:
    """Geocode an address."""
    settings = get_settings()
    if not settings.google_maps_api_key:
        return "❌ GOOGLE_MAPS_API_KEY is not configured."
        
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": settings.google_maps_api_key
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            
        if data.get("status") != "OK":
            return f"❌ Geocoding failed: {data.get('status')} - {data.get('error_message', '')}"
            
        result = data["results"][0]
        location = result["geometry"]["location"]
        formatted_address = result["formatted_address"]
        
        return (
            f"✅ Geocoded Address: {formatted_address}\n"
            f"Latitude: {location['lat']}\n"
            f"Longitude: {location['lng']}"
        )
            
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return f"❌ Error checking Maps API: {e}"


@tool(
    name="search_places",
    description="Search for places using a text query (e.g., 'restaurants in Pittsburgh').",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The text query to search for.",
            }
        },
        "required": ["query"],
    }
)
async def search_places(query: str) -> str:
    """Search for places via Google Maps Text Search."""
    settings = get_settings()
    if not settings.google_maps_api_key:
        return "❌ GOOGLE_MAPS_API_KEY is not configured."
        
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "key": settings.google_maps_api_key
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            
        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            return f"❌ Places search failed: {data.get('status')} - {data.get('error_message', '')}"
            
        results = data.get("results", [])
        if not results:
            return f"No results found for '{query}'."
            
        out = [f"Found {len(results)} places matching '{query}':"]
        for r in results[:10]: # Limit to 10
            name = r.get("name", "Unknown")
            addr = r.get("formatted_address", "Unknown Address")
            rating = r.get("rating", "N/A")
            out.append(f"- {name} ({rating}⭐) | {addr}")
            
        return "\n".join(out)
            
    except Exception as e:
        logger.error(f"Places error: {e}")
        return f"❌ Error searching Maps API: {e}"
