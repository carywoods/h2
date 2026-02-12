import resend
from typing import Optional

from app.config import get_settings


def _get_profile_email_html(company_name: str, profile_url: str) -> str:
    """Generate minimal HTML for the profile ready email."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.5;
            color: #1a2b4a;
            max-width: 480px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        .button {{
            display: inline-block;
            background-color: #1a2b4a;
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            margin-top: 20px;
        }}
        .footer {{
            margin-top: 40px;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <p>Your operational profile for <strong>{company_name}</strong> is ready.</p>

    <a href="{profile_url}" class="button">View Your Profile</a>

    <p class="footer">
        This link expires in 7 days.<br>
        HarnessAI
    </p>
</body>
</html>"""


def _get_insufficient_data_email_html(company_name: str) -> str:
    """Generate HTML for insufficient data email."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.5;
            color: #1a2b4a;
            max-width: 480px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        .footer {{
            margin-top: 40px;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <p>We need a bit more information to build your operational profile for <strong>{company_name}</strong>.</p>

    <p>Our team will follow up within 24 hours.</p>

    <p class="footer">
        HarnessAI
    </p>
</body>
</html>"""


def _get_error_email_html(company_name: str) -> str:
    """Generate HTML for error notification email."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.5;
            color: #1a2b4a;
            max-width: 480px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        .footer {{
            margin-top: 40px;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <p>We encountered an issue generating your operational profile for <strong>{company_name}</strong>.</p>

    <p>Our team has been notified and will reach out within 24 hours.</p>

    <p class="footer">
        HarnessAI
    </p>
</body>
</html>"""


async def send_profile_email(
    to_email: str,
    company_name: str,
    auth_token: str
) -> tuple[bool, Optional[str]]:
    """
    Send the profile ready email with the authenticated link.

    Returns (success, error_message).
    """
    settings = get_settings()

    if not settings.resend_api_key:
        return False, "Resend API key not configured"

    resend.api_key = settings.resend_api_key

    profile_url = f"{settings.base_url}/profile/{auth_token}"

    try:
        resend.Emails.send({
            "from": "HarnessAI <noreply@harnessai.co>",
            "to": [to_email],
            "subject": "Your HarnessAI Operational Profile",
            "html": _get_profile_email_html(company_name, profile_url),
        })
        return True, None
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"


async def send_insufficient_data_email(
    to_email: str,
    company_name: str
) -> tuple[bool, Optional[str]]:
    """
    Send email when there's insufficient data to generate a profile.

    Returns (success, error_message).
    """
    settings = get_settings()

    if not settings.resend_api_key:
        return False, "Resend API key not configured"

    resend.api_key = settings.resend_api_key

    try:
        resend.Emails.send({
            "from": "HarnessAI <noreply@harnessai.co>",
            "to": [to_email],
            "subject": "Your HarnessAI Profile Request",
            "html": _get_insufficient_data_email_html(company_name),
        })
        return True, None
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"


async def send_error_email(
    to_email: str,
    company_name: str
) -> tuple[bool, Optional[str]]:
    """
    Send email when profile generation fails.

    Returns (success, error_message).
    """
    settings = get_settings()

    if not settings.resend_api_key:
        return False, "Resend API key not configured"

    resend.api_key = settings.resend_api_key

    try:
        resend.Emails.send({
            "from": "HarnessAI <noreply@harnessai.co>",
            "to": [to_email],
            "subject": "Your HarnessAI Profile Request",
            "html": _get_error_email_html(company_name),
        })
        return True, None
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"
