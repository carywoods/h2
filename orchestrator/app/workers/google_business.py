import httpx
from typing import Optional

from app.config import get_settings


async def fetch_google_business(
    company_name: str,
    location: Optional[str] = None,
    timeout: float = 10.0
) -> dict:
    """
    Use Google Places API (Text Search) to find the business.

    Extracts:
    - Rating
    - Review count
    - Business category
    - Hours
    - Phone
    - Address
    - Photo count
    """
    result = {
        "source": "google_business",
        "success": False,
        "company_name": company_name,
        "place_id": None,
        "name": None,
        "rating": None,
        "review_count": None,
        "business_category": None,
        "address": None,
        "phone": None,
        "website": None,
        "hours": None,
        "photo_count": None,
        "price_level": None,
        "error": None,
    }

    settings = get_settings()
    api_key = settings.google_places_api_key

    if not api_key:
        result["error"] = "Google Places API key not configured"
        return result

    try:
        # Build search query
        query = company_name
        if location:
            query = f"{company_name} {location}"

        async with httpx.AsyncClient(timeout=timeout) as client:
            # Text Search to find the place
            search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            search_params = {
                "query": query,
                "key": api_key,
            }

            search_response = await client.get(search_url, params=search_params)
            search_data = search_response.json()

            if search_data.get("status") != "OK" or not search_data.get("results"):
                result["error"] = f"No results found: {search_data.get('status', 'Unknown error')}"
                return result

            # Get the first (most relevant) result
            place = search_data["results"][0]
            place_id = place.get("place_id")
            result["place_id"] = place_id

            # Basic info from text search
            result["name"] = place.get("name")
            result["rating"] = place.get("rating")
            result["review_count"] = place.get("user_ratings_total")
            result["address"] = place.get("formatted_address")
            result["business_category"] = place.get("types", [None])[0]
            result["price_level"] = place.get("price_level")

            if place.get("photos"):
                result["photo_count"] = len(place["photos"])

            # Get more details via Place Details API
            if place_id:
                details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                details_params = {
                    "place_id": place_id,
                    "fields": "formatted_phone_number,website,opening_hours,reviews",
                    "key": api_key,
                }

                details_response = await client.get(details_url, params=details_params)
                details_data = details_response.json()

                if details_data.get("status") == "OK" and details_data.get("result"):
                    details = details_data["result"]
                    result["phone"] = details.get("formatted_phone_number")
                    result["website"] = details.get("website")

                    if details.get("opening_hours"):
                        result["hours"] = details["opening_hours"].get("weekday_text")

            result["success"] = True

    except httpx.TimeoutException:
        result["error"] = "Timeout - Google Places API took too long to respond"
    except Exception as e:
        result["error"] = f"Error fetching Google Business data: {str(e)}"

    return result
