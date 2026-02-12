import httpx
from typing import Optional

from app.config import get_settings


async def scan_job_postings(
    company_name: str,
    location: Optional[str] = None,
    timeout: float = 10.0
) -> dict:
    """
    Search for job postings using SerpAPI (Google Jobs).

    Extracts:
    - Number of open positions
    - Job titles
    - Departments hiring
    - Seniority levels

    This worker is fragile and will gracefully return empty data if unavailable.
    """
    result = {
        "source": "job_scanner",
        "success": False,
        "company_name": company_name,
        "total_positions": 0,
        "job_titles": [],
        "departments": [],
        "seniority_levels": [],
        "recent_postings": [],
        "error": None,
    }

    settings = get_settings()
    api_key = settings.serpapi_key

    if not api_key:
        result["error"] = "SerpAPI key not configured - skipping job scan"
        return result

    try:
        # Build search query
        query = f"{company_name} jobs"
        if location:
            query = f"{company_name} {location} jobs"

        async with httpx.AsyncClient(timeout=timeout) as client:
            # Use SerpAPI Google Jobs endpoint
            search_url = "https://serpapi.com/search.json"
            params = {
                "engine": "google_jobs",
                "q": query,
                "api_key": api_key,
            }

            response = await client.get(search_url, params=params)
            data = response.json()

            if "error" in data:
                result["error"] = data["error"]
                return result

            jobs = data.get("jobs_results", [])

            if not jobs:
                result["success"] = True
                result["error"] = "No job postings found"
                return result

            result["total_positions"] = len(jobs)

            # Extract job details
            titles = []
            departments = set()
            seniority = set()
            recent = []

            for job in jobs[:10]:  # Limit to first 10
                title = job.get("title", "")
                titles.append(title)

                # Try to infer department from title
                title_lower = title.lower()
                if any(kw in title_lower for kw in ["engineer", "developer", "software", "tech", "devops", "sre"]):
                    departments.add("Engineering")
                elif any(kw in title_lower for kw in ["sales", "account", "business development"]):
                    departments.add("Sales")
                elif any(kw in title_lower for kw in ["marketing", "content", "brand", "seo", "growth"]):
                    departments.add("Marketing")
                elif any(kw in title_lower for kw in ["hr", "human resources", "recruiter", "people"]):
                    departments.add("Human Resources")
                elif any(kw in title_lower for kw in ["finance", "accounting", "controller", "cfo"]):
                    departments.add("Finance")
                elif any(kw in title_lower for kw in ["operations", "ops", "logistics", "supply"]):
                    departments.add("Operations")
                elif any(kw in title_lower for kw in ["product", "pm", "product manager"]):
                    departments.add("Product")
                elif any(kw in title_lower for kw in ["design", "ux", "ui", "creative"]):
                    departments.add("Design")
                elif any(kw in title_lower for kw in ["customer", "support", "success"]):
                    departments.add("Customer Success")

                # Try to infer seniority
                if any(kw in title_lower for kw in ["intern", "internship"]):
                    seniority.add("Intern")
                elif any(kw in title_lower for kw in ["junior", "entry", "associate", "jr"]):
                    seniority.add("Junior")
                elif any(kw in title_lower for kw in ["senior", "sr", "lead", "principal"]):
                    seniority.add("Senior")
                elif any(kw in title_lower for kw in ["manager", "director", "head of"]):
                    seniority.add("Manager")
                elif any(kw in title_lower for kw in ["vp", "vice president", "chief", "cto", "ceo", "cfo"]):
                    seniority.add("Executive")
                else:
                    seniority.add("Mid-level")

                # Add to recent postings
                recent.append({
                    "title": title,
                    "company": job.get("company_name"),
                    "location": job.get("location"),
                    "posted": job.get("detected_extensions", {}).get("posted_at"),
                })

            result["job_titles"] = titles
            result["departments"] = list(departments)
            result["seniority_levels"] = list(seniority)
            result["recent_postings"] = recent[:5]
            result["success"] = True

    except httpx.TimeoutException:
        result["error"] = "Timeout - job search took too long"
    except Exception as e:
        result["error"] = f"Error scanning job postings: {str(e)}"

    return result
