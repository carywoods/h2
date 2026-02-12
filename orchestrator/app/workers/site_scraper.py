import httpx
from bs4 import BeautifulSoup
from typing import Optional
from urllib.parse import urljoin, urlparse
import asyncio


async def scrape_site(url: str, timeout: float = 10.0) -> dict:
    """
    Scrape the target URL and extract relevant business information.

    Returns structured data including:
    - Page title and meta description
    - Visible text content (first 5000 chars)
    - Navigation structure
    - Service/product descriptions
    - About page content
    - Team size indicators
    - Location mentions
    """
    result = {
        "source": "site_scraper",
        "success": False,
        "url": url,
        "title": None,
        "meta_description": None,
        "visible_text": None,
        "navigation_items": [],
        "internal_links_count": 0,
        "about_content": None,
        "services_content": None,
        "team_content": None,
        "location_mentions": [],
        "is_spa": False,
        "error": None,
    }

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; HarnessAI/1.0; +https://harnessai.co)"
            }
        ) as client:
            # Fetch main page
            response = await client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # Extract title
            title_tag = soup.find("title")
            result["title"] = title_tag.get_text(strip=True) if title_tag else None

            # Extract meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                result["meta_description"] = meta_desc.get("content", "")

            # Check if likely a JS SPA (minimal content)
            body = soup.find("body")
            if body:
                text_content = body.get_text(separator=" ", strip=True)
                if len(text_content) < 200:
                    result["is_spa"] = True
                result["visible_text"] = text_content[:5000]

            # Extract navigation items
            nav_items = []
            for nav in soup.find_all("nav"):
                for link in nav.find_all("a", href=True):
                    text = link.get_text(strip=True)
                    if text and len(text) < 50:
                        nav_items.append(text)
            result["navigation_items"] = list(set(nav_items))[:20]

            # Count internal links
            base_domain = urlparse(url).netloc
            internal_links = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                full_url = urljoin(url, href)
                if urlparse(full_url).netloc == base_domain:
                    internal_links.append(full_url)
            result["internal_links_count"] = len(set(internal_links))

            # Find key pages to scrape (about, services, team)
            key_pages = {
                "about": None,
                "services": None,
                "team": None,
            }

            for link in soup.find_all("a", href=True):
                href = link["href"].lower()
                text = link.get_text(strip=True).lower()
                full_url = urljoin(url, link["href"])

                if urlparse(full_url).netloc == base_domain:
                    if any(kw in href or kw in text for kw in ["about", "about-us", "who-we-are"]):
                        key_pages["about"] = full_url
                    elif any(kw in href or kw in text for kw in ["service", "what-we-do", "solutions", "offerings"]):
                        key_pages["services"] = full_url
                    elif any(kw in href or kw in text for kw in ["team", "people", "staff", "our-team"]):
                        key_pages["team"] = full_url

            # Fetch key pages (up to 3)
            async def fetch_page_content(page_url: str) -> Optional[str]:
                try:
                    resp = await client.get(page_url)
                    resp.raise_for_status()
                    page_soup = BeautifulSoup(resp.text, "lxml")
                    main_content = page_soup.find("main") or page_soup.find("article") or page_soup.find("body")
                    if main_content:
                        return main_content.get_text(separator=" ", strip=True)[:3000]
                except Exception:
                    pass
                return None

            tasks = []
            if key_pages["about"]:
                tasks.append(("about", fetch_page_content(key_pages["about"])))
            if key_pages["services"]:
                tasks.append(("services", fetch_page_content(key_pages["services"])))
            if key_pages["team"]:
                tasks.append(("team", fetch_page_content(key_pages["team"])))

            if tasks:
                results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
                for i, (page_type, _) in enumerate(tasks):
                    if not isinstance(results[i], Exception) and results[i]:
                        result[f"{page_type}_content"] = results[i]

            # Extract location mentions
            location_patterns = [
                "indiana", "indianapolis", "carmel", "fishers", "noblesville",
                "bloomington", "fort wayne", "south bend", "evansville",
                "chicago", "ohio", "kentucky", "michigan", "illinois"
            ]
            text_lower = (result["visible_text"] or "").lower()
            for pattern in location_patterns:
                if pattern in text_lower:
                    result["location_mentions"].append(pattern.title())
            result["location_mentions"] = list(set(result["location_mentions"]))

            result["success"] = True

    except httpx.TimeoutException:
        result["error"] = "Timeout - site took too long to respond"
    except httpx.HTTPStatusError as e:
        result["error"] = f"HTTP error: {e.response.status_code}"
    except Exception as e:
        result["error"] = f"Error scraping site: {str(e)}"

    return result
