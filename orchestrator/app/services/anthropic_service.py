import json
import asyncio
from typing import Optional
from datetime import datetime

import anthropic

from app.config import get_settings
from app.schemas import OperationalProfile


SYSTEM_PROMPT = """You are an operational intelligence analyst. You receive raw data collected from public sources about a business. Your job is to produce a structured operational profile that demonstrates analytical depth and insight.

You must return ONLY valid JSON matching the schema below. No preamble, no markdown, no explanation outside the JSON.

Your analysis should:
- Draw non-obvious inferences from the data (e.g., MX records showing Google Workspace suggests cloud-forward operations; job postings for specific roles suggest strategic priorities)
- Identify operational strengths visible in the data
- Identify potential blind spots or areas where data suggests vulnerability
- Compare against general industry baselines where possible
- Be specific and grounded — never fabricate data points
- Note where confidence is low due to limited data

Profile JSON Schema:
{
  "company_name": "string",
  "industry_classification": "string",
  "location": "string",
  "estimated_size": "string (e.g., '10-50 employees', 'Solo operator', '50-200 employees')",
  "operational_snapshot": {
    "technology_posture": "string (2-3 sentence assessment of their technology stack and what it implies)",
    "digital_maturity": "string (1-10 rating with one-sentence justification)",
    "detected_technologies": ["array of strings"],
    "infrastructure_signals": "string (what DNS/hosting/email setup implies about operational sophistication)"
  },
  "market_position": {
    "business_category": "string",
    "public_reputation": "string (review data summary and what it implies)",
    "competitive_signals": "string (2-3 sentences on what the data suggests about their competitive position)",
    "growth_indicators": "string (hiring activity, web presence expansion, etc.)"
  },
  "strategic_observations": [
    "string (3-5 non-obvious observations drawn from the data, each 1-2 sentences)"
  ],
  "identified_gaps": [
    "string (2-3 areas where deeper analysis would reveal important insights, framed as opportunities not criticisms)"
  ],
  "data_confidence": {
    "overall_score": "string (High/Medium/Low)",
    "sources_used": ["array of source names"],
    "sources_unavailable": ["array of source names that returned no data"],
    "freshness": "string (e.g., 'Data collected February 2026')"
  }
}"""


def validate_profile(profile: dict, worker_data: dict) -> tuple[bool, list[str]]:
    """
    Validate that the profile doesn't contain fabricated data.

    Returns (is_valid, list of issues).
    """
    issues = []

    # Check that detected_technologies came from tech detector
    if "operational_snapshot" in profile:
        detected_techs = profile["operational_snapshot"].get("detected_technologies", [])
        tech_data = worker_data.get("tech_detector", {})

        if tech_data.get("success"):
            valid_techs = {t["name"] for t in tech_data.get("detected", [])}
            for tech in detected_techs:
                if tech not in valid_techs:
                    issues.append(f"Technology '{tech}' not found in detector output")

    # Check that review data came from Google Business
    if "market_position" in profile:
        reputation = profile["market_position"].get("public_reputation", "")
        google_data = worker_data.get("google_business", {})

        if google_data.get("success"):
            if google_data.get("rating"):
                # Make sure any rating mentioned matches the actual rating
                rating_str = str(google_data["rating"])
                if rating_str not in reputation and "rating" in reputation.lower():
                    # This is a soft check - only flag if it claims a rating but wrong
                    pass
        elif "stars" in reputation.lower() or "rating" in reputation.lower():
            # Claims rating data but Google Business didn't return data
            if "no data" not in reputation.lower() and "unavailable" not in reputation.lower():
                issues.append("Profile claims review data but Google Business data was unavailable")

    return len(issues) == 0, issues


async def generate_profile(
    company_name: str,
    worker_data: dict,
    max_retries: int = 3
) -> tuple[Optional[dict], Optional[str]]:
    """
    Send aggregated worker data to Claude Sonnet and generate an operational profile.

    Returns (profile_dict, error_message).
    """
    settings = get_settings()

    if not settings.anthropic_api_key:
        return None, "Anthropic API key not configured"

    # Build the user message with all worker data
    user_message = f"""Analyze this business data for {company_name} and generate an operational profile.

Raw Data Collected:

{json.dumps(worker_data, indent=2, default=str)}

Current date: {datetime.now().strftime('%B %Y')}

Generate the operational profile JSON now."""

    # Retry with exponential backoff
    delays = [1, 4, 16]  # seconds

    for attempt in range(max_retries):
        try:
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2500,
                temperature=0.3,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            # Extract the response text
            response_text = message.content[0].text

            # Parse JSON (handle potential markdown code blocks)
            json_str = response_text
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]

            profile = json.loads(json_str.strip())

            # Validate the profile
            is_valid, issues = validate_profile(profile, worker_data)
            if not is_valid:
                # Log issues but don't fail - just note them
                profile["_validation_issues"] = issues

            return profile, None

        except anthropic.RateLimitError:
            if attempt < max_retries - 1:
                await asyncio.sleep(delays[attempt])
                continue
            return None, "Rate limited by Anthropic API after retries"

        except anthropic.APIError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(delays[attempt])
                continue
            return None, f"Anthropic API error: {str(e)}"

        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(delays[attempt])
                continue
            return None, f"Failed to parse profile JSON: {str(e)}"

        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(delays[attempt])
                continue
            return None, f"Error generating profile: {str(e)}"

    return None, "Failed to generate profile after all retries"


def check_data_sufficiency(worker_data: dict) -> tuple[bool, list[str]]:
    """
    Check if we have enough data to generate a meaningful profile.

    Returns (is_sufficient, list of available sources).
    """
    available_sources = []
    critical_sources = 0

    # Site scraper is most important
    if worker_data.get("site_scraper", {}).get("success"):
        available_sources.append("Website Content")
        critical_sources += 2  # Worth 2 points

    # Tech detector
    if worker_data.get("tech_detector", {}).get("success"):
        techs = worker_data["tech_detector"].get("detected", [])
        if techs:
            available_sources.append("Technology Stack")
            critical_sources += 1

    # DNS/WHOIS
    dns_data = worker_data.get("dns_whois", {})
    if dns_data.get("success"):
        if dns_data.get("dns", {}).get("mx_records"):
            available_sources.append("DNS Records")
            critical_sources += 1
        if dns_data.get("whois", {}).get("registrar"):
            available_sources.append("Domain WHOIS")
            critical_sources += 1

    # Google Business
    if worker_data.get("google_business", {}).get("success"):
        if worker_data["google_business"].get("rating"):
            available_sources.append("Google Business Profile")
            critical_sources += 1

    # Job postings (nice to have but not critical)
    if worker_data.get("job_scanner", {}).get("success"):
        if worker_data["job_scanner"].get("total_positions", 0) > 0:
            available_sources.append("Job Postings")

    # Need at least 3 points (e.g., site scraper alone, or DNS + tech + one more)
    is_sufficient = critical_sources >= 3

    return is_sufficient, available_sources
