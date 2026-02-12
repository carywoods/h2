import httpx
import re
from typing import Optional


# Simplified Wappalyzer-style technology signatures
TECH_SIGNATURES = {
    # CMS
    "WordPress": {
        "headers": [("x-powered-by", "wordpress")],
        "html": ["/wp-content/", "/wp-includes/", "wp-json"],
        "meta": [("generator", "wordpress")],
    },
    "Shopify": {
        "headers": [("x-shopify-stage", "")],
        "html": ["cdn.shopify.com", "shopify.com/s/"],
        "meta": [],
    },
    "Squarespace": {
        "html": ["squarespace.com", "static.squarespace.com"],
        "meta": [("generator", "squarespace")],
    },
    "Wix": {
        "html": ["wix.com", "parastorage.com", "_wixCIDX"],
        "meta": [("generator", "wix")],
    },
    "Webflow": {
        "html": ["webflow.com", "wf-cdn"],
        "meta": [("generator", "webflow")],
    },
    "Drupal": {
        "html": ["/sites/default/files/", "drupal.js"],
        "meta": [("generator", "drupal")],
        "headers": [("x-drupal-cache", ""), ("x-generator", "drupal")],
    },
    "HubSpot CMS": {
        "html": ["hs-scripts.com", "hubspot.com", "hbspt.forms"],
    },

    # JavaScript Frameworks
    "React": {
        "html": ["react", "_reactRootContainer", "data-reactroot"],
    },
    "Vue.js": {
        "html": ["vue.js", "vuejs", "data-v-"],
    },
    "Angular": {
        "html": ["ng-version", "angular.js", "ng-app"],
    },
    "Next.js": {
        "html": ["_next/static", "__NEXT_DATA__"],
    },
    "Gatsby": {
        "html": ["/gatsby-", "__gatsby"],
    },

    # Analytics
    "Google Analytics (GA4)": {
        "html": ["gtag/js", "googletagmanager.com", "google-analytics.com/g/"],
    },
    "Google Analytics (Universal)": {
        "html": ["google-analytics.com/analytics.js", "ga('create'"],
    },
    "Mixpanel": {
        "html": ["mixpanel.com", "mixpanel.init"],
    },
    "Segment": {
        "html": ["segment.com/analytics.js", "analytics.load"],
    },
    "Hotjar": {
        "html": ["hotjar.com", "static.hotjar.com"],
    },
    "Facebook Pixel": {
        "html": ["connect.facebook.net", "fbq("],
    },
    "LinkedIn Insight": {
        "html": ["snap.licdn.com", "_linkedin_partner_id"],
    },

    # Payment
    "Stripe": {
        "html": ["js.stripe.com", "stripe.com/v3"],
    },
    "PayPal": {
        "html": ["paypal.com/sdk", "paypalobjects.com"],
    },
    "Square": {
        "html": ["squareup.com", "square.js"],
    },

    # CDN
    "Cloudflare": {
        "headers": [("cf-ray", ""), ("server", "cloudflare")],
        "html": ["cloudflare.com"],
    },
    "AWS CloudFront": {
        "headers": [("x-amz-cf-id", ""), ("x-amz-cf-pop", "")],
    },
    "Fastly": {
        "headers": [("x-served-by", "cache"), ("via", "varnish")],
    },
    "Akamai": {
        "headers": [("x-akamai-transformed", "")],
    },

    # Marketing/CRM
    "Mailchimp": {
        "html": ["mailchimp.com", "mc.us", "chimpstatic.com"],
    },
    "HubSpot": {
        "html": ["hubspot.com", "hs-scripts.com", "hbspt"],
    },
    "Salesforce": {
        "html": ["force.com", "salesforce.com", "pardot.com"],
    },
    "Intercom": {
        "html": ["intercom.io", "widget.intercom.io"],
    },
    "Drift": {
        "html": ["drift.com", "js.driftt.com"],
    },
    "Zendesk": {
        "html": ["zendesk.com", "zdassets.com"],
    },

    # Hosting/Platform
    "Vercel": {
        "headers": [("x-vercel-id", ""), ("server", "vercel")],
    },
    "Netlify": {
        "headers": [("x-nf-request-id", ""), ("server", "netlify")],
    },
    "Heroku": {
        "headers": [("via", "heroku"), ("x-runtime", "")],
    },
    "AWS": {
        "headers": [("x-amzn-requestid", ""), ("server", "amazons3")],
    },
    "Google Cloud": {
        "headers": [("x-goog-", "")],
    },

    # Security/Performance
    "reCAPTCHA": {
        "html": ["google.com/recaptcha", "grecaptcha"],
    },
    "hCaptcha": {
        "html": ["hcaptcha.com"],
    },
    "Sucuri": {
        "headers": [("x-sucuri-id", "")],
    },

    # E-commerce
    "WooCommerce": {
        "html": ["woocommerce", "wc-add-to-cart"],
    },
    "Magento": {
        "html": ["/static/frontend/", "mage/cookies"],
        "headers": [("x-magento-vary", "")],
    },
    "BigCommerce": {
        "html": ["bigcommerce.com", "cdn11.bigcommerce.com"],
    },

    # Other
    "jQuery": {
        "html": ["jquery.js", "jquery.min.js", "code.jquery.com"],
    },
    "Bootstrap": {
        "html": ["bootstrap.min.css", "bootstrap.min.js"],
    },
    "Tailwind CSS": {
        "html": ["tailwindcss", "tailwind.min.css"],
    },
    "Font Awesome": {
        "html": ["fontawesome", "font-awesome"],
    },
    "Google Fonts": {
        "html": ["fonts.googleapis.com", "fonts.gstatic.com"],
    },
    "Google Tag Manager": {
        "html": ["googletagmanager.com/gtm.js"],
    },
}


def check_signature(tech_name: str, signature: dict, headers: dict, html: str, meta_tags: dict) -> Optional[dict]:
    """Check if a technology signature matches."""
    confidence = 0
    matches = []

    # Check headers
    for header_name, header_value in signature.get("headers", []):
        header_name_lower = header_name.lower()
        for h_name, h_value in headers.items():
            if header_name_lower == h_name.lower():
                if not header_value or header_value.lower() in h_value.lower():
                    confidence += 30
                    matches.append(f"header:{header_name}")
                    break

    # Check HTML patterns
    html_lower = html.lower()
    for pattern in signature.get("html", []):
        if pattern.lower() in html_lower:
            confidence += 25
            matches.append(f"html:{pattern[:30]}")

    # Check meta tags
    for meta_name, meta_value in signature.get("meta", []):
        if meta_name in meta_tags:
            if not meta_value or meta_value.lower() in meta_tags[meta_name].lower():
                confidence += 30
                matches.append(f"meta:{meta_name}")

    if confidence >= 25:
        return {
            "name": tech_name,
            "confidence": min(confidence, 100),
            "evidence": matches[:3],
        }
    return None


async def detect_technologies(url: str, timeout: float = 10.0) -> dict:
    """
    Analyze HTTP response headers and HTML source to detect technologies.

    Returns array of detected technologies with confidence levels.
    """
    result = {
        "source": "tech_detector",
        "success": False,
        "url": url,
        "detected": [],
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
            response = await client.get(url)
            response.raise_for_status()

            headers = dict(response.headers)
            html = response.text

            # Extract meta tags
            meta_tags = {}
            meta_pattern = re.compile(r'<meta[^>]+name=["\']([^"\']+)["\'][^>]+content=["\']([^"\']*)["\']', re.IGNORECASE)
            for match in meta_pattern.finditer(html):
                meta_tags[match.group(1).lower()] = match.group(2)

            # Also check content before name pattern
            meta_pattern2 = re.compile(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']([^"\']+)["\']', re.IGNORECASE)
            for match in meta_pattern2.finditer(html):
                meta_tags[match.group(2).lower()] = match.group(1)

            # Check all signatures
            detected = []
            for tech_name, signature in TECH_SIGNATURES.items():
                match = check_signature(tech_name, signature, headers, html, meta_tags)
                if match:
                    detected.append(match)

            # Sort by confidence
            detected.sort(key=lambda x: x["confidence"], reverse=True)

            result["detected"] = detected
            result["success"] = True

    except httpx.TimeoutException:
        result["error"] = "Timeout - site took too long to respond"
    except httpx.HTTPStatusError as e:
        result["error"] = f"HTTP error: {e.response.status_code}"
    except Exception as e:
        result["error"] = f"Error detecting technologies: {str(e)}"

    return result
