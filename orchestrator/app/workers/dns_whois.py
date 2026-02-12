import dns.resolver
import whois
from urllib.parse import urlparse
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor


def _sync_dns_lookup(domain: str) -> dict:
    """Synchronous DNS lookup."""
    result = {
        "mx_records": [],
        "txt_records": [],
        "nameservers": [],
        "email_provider": None,
        "has_spf": False,
        "has_dkim": False,
        "has_dmarc": False,
    }

    try:
        # MX records (email provider)
        try:
            mx_answers = dns.resolver.resolve(domain, "MX")
            result["mx_records"] = [str(r.exchange).rstrip(".") for r in mx_answers]

            # Detect email provider from MX records
            mx_str = " ".join(result["mx_records"]).lower()
            if "google" in mx_str or "googlemail" in mx_str:
                result["email_provider"] = "Google Workspace"
            elif "outlook" in mx_str or "microsoft" in mx_str:
                result["email_provider"] = "Microsoft 365"
            elif "zoho" in mx_str:
                result["email_provider"] = "Zoho Mail"
            elif "protonmail" in mx_str:
                result["email_provider"] = "ProtonMail"
            elif "mimecast" in mx_str:
                result["email_provider"] = "Mimecast"
            elif "barracuda" in mx_str:
                result["email_provider"] = "Barracuda"
            else:
                result["email_provider"] = "Custom/Other"
        except dns.resolver.NoAnswer:
            pass
        except dns.resolver.NXDOMAIN:
            pass

        # TXT records (SPF, DKIM, DMARC)
        try:
            txt_answers = dns.resolver.resolve(domain, "TXT")
            for txt in txt_answers:
                txt_str = str(txt)
                result["txt_records"].append(txt_str[:200])
                if "v=spf1" in txt_str:
                    result["has_spf"] = True
        except dns.resolver.NoAnswer:
            pass
        except dns.resolver.NXDOMAIN:
            pass

        # Check DMARC
        try:
            dmarc_answers = dns.resolver.resolve(f"_dmarc.{domain}", "TXT")
            for txt in dmarc_answers:
                if "v=DMARC1" in str(txt):
                    result["has_dmarc"] = True
                    break
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass

        # Nameservers
        try:
            ns_answers = dns.resolver.resolve(domain, "NS")
            result["nameservers"] = [str(r).rstrip(".") for r in ns_answers]
        except dns.resolver.NoAnswer:
            pass
        except dns.resolver.NXDOMAIN:
            pass

    except Exception:
        pass

    return result


def _sync_whois_lookup(domain: str) -> dict:
    """Synchronous WHOIS lookup."""
    result = {
        "registrar": None,
        "creation_date": None,
        "expiration_date": None,
        "domain_age_years": None,
    }

    try:
        w = whois.whois(domain)

        if w.registrar:
            result["registrar"] = str(w.registrar)

        # Handle creation_date (can be list or single value)
        creation_date = w.creation_date
        if creation_date:
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            if creation_date:
                result["creation_date"] = creation_date.isoformat() if hasattr(creation_date, "isoformat") else str(creation_date)
                # Calculate domain age
                from datetime import datetime
                if hasattr(creation_date, "year"):
                    age = datetime.now().year - creation_date.year
                    result["domain_age_years"] = age

        expiration_date = w.expiration_date
        if expiration_date:
            if isinstance(expiration_date, list):
                expiration_date = expiration_date[0]
            if expiration_date:
                result["expiration_date"] = expiration_date.isoformat() if hasattr(expiration_date, "isoformat") else str(expiration_date)

    except Exception:
        pass

    return result


async def lookup_dns_whois(url: str, timeout: float = 10.0) -> dict:
    """
    Perform DNS and WHOIS lookups on the domain.

    Returns:
    - MX records (email provider)
    - TXT records (SPF/DKIM indicating email maturity)
    - Nameservers (hosting provider indicator)
    - WHOIS: registration date, registrar
    """
    result = {
        "source": "dns_whois",
        "success": False,
        "url": url,
        "domain": None,
        "dns": {},
        "whois": {},
        "error": None,
    }

    try:
        # Extract domain from URL
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        domain = domain.replace("www.", "")
        result["domain"] = domain

        # Run DNS and WHOIS lookups in thread pool (they're blocking)
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=2) as executor:
            dns_future = loop.run_in_executor(executor, _sync_dns_lookup, domain)
            whois_future = loop.run_in_executor(executor, _sync_whois_lookup, domain)

            try:
                result["dns"] = await asyncio.wait_for(dns_future, timeout=timeout)
            except asyncio.TimeoutError:
                result["dns"] = {"error": "DNS lookup timed out"}

            try:
                result["whois"] = await asyncio.wait_for(whois_future, timeout=timeout)
            except asyncio.TimeoutError:
                result["whois"] = {"error": "WHOIS lookup timed out"}

        result["success"] = bool(result["dns"] or result["whois"])

    except Exception as e:
        result["error"] = f"Error in DNS/WHOIS lookup: {str(e)}"

    return result
