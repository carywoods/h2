import asyncio
import uuid
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import (
    IntakeRequest,
    IntakeResponse,
    JobStatus,
    ProfileResponse,
    FeedbackRequest,
    SubmissionStatus,
)
from app.database import (
    init_db,
    create_submission,
    get_submission_by_job_id,
    get_submission_by_token,
    get_submission_by_url,
    update_submission_status,
    create_profile,
    get_profile_by_submission_id,
    create_feedback,
)
from app.workers import (
    scrape_site,
    detect_technologies,
    lookup_dns_whois,
    fetch_google_business,
    scan_job_postings,
)
from app.services.anthropic_service import generate_profile, check_data_sufficiency
from app.services.email_service import (
    send_profile_email,
    send_insufficient_data_email,
    send_error_email,
)


# Redis connection
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup."""
    global redis_client
    settings = get_settings()

    # Initialize database
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")

    # Initialize Redis
    try:
        redis_client = redis.from_url(settings.redis_url)
        await redis_client.ping()
    except Exception as e:
        print(f"Warning: Could not connect to Redis: {e}")
        redis_client = None

    yield

    # Cleanup
    if redis_client:
        await redis_client.close()


app = FastAPI(
    title="HarnessAI Orchestrator",
    description="Operational intelligence profile generation API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_url(url: str) -> str:
    """Normalize URL to have https:// scheme."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


def extract_domain(url: str) -> str:
    """Extract the base domain from a URL."""
    parsed = urlparse(normalize_url(url))
    domain = parsed.netloc.lower()
    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def validate_email_domain(email: str, url: str) -> tuple[bool, bool]:
    """
    Validate that email domain matches URL domain.

    Returns (is_valid, needs_manual_review).
    - (True, False): Email domain matches URL domain
    - (True, True): Email is a generic provider (Gmail/Yahoo/etc)
    - (False, False): Email domain doesn't match URL domain
    """
    email_domain = email.split("@")[1].lower()
    url_domain = extract_domain(url)

    # Check for generic email providers
    generic_providers = [
        "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
        "aol.com", "icloud.com", "protonmail.com", "mail.com",
    ]
    if email_domain in generic_providers:
        return True, True  # Valid but needs manual review

    # Check for exact match or subdomain match
    # e.g., mail.company.com should match company.com
    if email_domain == url_domain:
        return True, False

    # Check if email domain is subdomain of URL domain
    if email_domain.endswith("." + url_domain):
        return True, False

    # Check if URL domain is subdomain of email domain
    if url_domain.endswith("." + email_domain):
        return True, False

    return False, False


async def check_rate_limit(ip: str) -> bool:
    """Check if IP has exceeded rate limit (10 per hour)."""
    if not redis_client:
        return True  # Allow if Redis unavailable

    key = f"rate_limit:{ip}"
    try:
        count = await redis_client.get(key)
        if count and int(count) >= 10:
            return False

        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, 3600)  # 1 hour TTL
        await pipe.execute()
        return True
    except Exception:
        return True  # Allow if error


async def process_submission(job_id: str, auth_token: str, submission: IntakeRequest):
    """Background task to process a submission."""
    settings = get_settings()

    try:
        # Update status to processing
        update_submission_status(job_id, SubmissionStatus.processing)

        url = normalize_url(submission.company_url)

        # Check cache first
        cached = get_submission_by_url(url)
        if cached and cached["status"] == "complete":
            # Use cached profile
            cached_profile = get_profile_by_submission_id(cached["id"])
            if cached_profile:
                # Get current submission ID
                current = get_submission_by_job_id(job_id)
                if current:
                    create_profile(
                        submission_id=current["id"],
                        profile_json=cached_profile["profile_json"],
                        data_sources_used=cached_profile["data_sources_used"],
                        confidence_score=cached_profile["confidence_score"],
                    )
                    update_submission_status(job_id, SubmissionStatus.complete, datetime.now())
                    await send_profile_email(submission.email, submission.company_name, auth_token)
                    return

        # Run all workers in parallel with timeout
        worker_results = await asyncio.gather(
            scrape_site(url),
            detect_technologies(url),
            lookup_dns_whois(url),
            fetch_google_business(submission.company_name),
            scan_job_postings(submission.company_name),
            return_exceptions=True,
        )

        # Organize results
        worker_data = {
            "site_scraper": worker_results[0] if not isinstance(worker_results[0], Exception) else {"success": False, "error": str(worker_results[0])},
            "tech_detector": worker_results[1] if not isinstance(worker_results[1], Exception) else {"success": False, "error": str(worker_results[1])},
            "dns_whois": worker_results[2] if not isinstance(worker_results[2], Exception) else {"success": False, "error": str(worker_results[2])},
            "google_business": worker_results[3] if not isinstance(worker_results[3], Exception) else {"success": False, "error": str(worker_results[3])},
            "job_scanner": worker_results[4] if not isinstance(worker_results[4], Exception) else {"success": False, "error": str(worker_results[4])},
        }

        # Check data sufficiency
        is_sufficient, available_sources = check_data_sufficiency(worker_data)

        if not is_sufficient:
            update_submission_status(job_id, SubmissionStatus.insufficient_data, datetime.now())
            await send_insufficient_data_email(submission.email, submission.company_name)
            return

        # Generate profile with Anthropic
        profile, error = await generate_profile(submission.company_name, worker_data)

        if error or not profile:
            update_submission_status(job_id, SubmissionStatus.failed, datetime.now())
            await send_error_email(submission.email, submission.company_name)
            return

        # Store the profile
        current = get_submission_by_job_id(job_id)
        if current:
            confidence_score = profile.get("data_confidence", {}).get("overall_score", "Medium")
            create_profile(
                submission_id=current["id"],
                profile_json=profile,
                data_sources_used=available_sources,
                confidence_score=confidence_score,
            )

        # Update status and send email
        update_submission_status(job_id, SubmissionStatus.complete, datetime.now())
        await send_profile_email(submission.email, submission.company_name, auth_token)

        # Cache in Redis (keyed by URL, 24h TTL)
        if redis_client:
            try:
                cache_key = f"profile_cache:{url}"
                await redis_client.setex(cache_key, 86400, job_id)
            except Exception:
                pass

    except Exception as e:
        print(f"Error processing submission {job_id}: {e}")
        update_submission_status(job_id, SubmissionStatus.failed, datetime.now())
        try:
            await send_error_email(submission.email, submission.company_name)
        except Exception:
            pass


@app.get("/health")
async def health_check():
    """Health check endpoint for Coolify."""
    return {"status": "ok"}


@app.post("/intake", response_model=IntakeResponse)
async def submit_intake(
    request: Request,
    submission: IntakeRequest,
    background_tasks: BackgroundTasks,
):
    """
    Submit a new company for analysis.

    Validates email domain, rate limits, and queues the analysis job.
    """
    # Get client IP
    client_ip = request.client.host
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    # Check rate limit
    if not await check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
        )

    # Validate email domain
    is_valid, needs_review = validate_email_domain(submission.email, submission.company_url)

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Please use a business email address matching your company domain.",
        )

    # Generate IDs
    job_id = str(uuid.uuid4())
    auth_token = str(uuid.uuid4())

    # Determine initial status
    initial_status = SubmissionStatus.manual_review if needs_review else SubmissionStatus.queued

    # Create submission record
    try:
        create_submission(
            company_name=submission.company_name,
            company_url=normalize_url(submission.company_url),
            email=submission.email,
            job_id=job_id,
            auth_token=auth_token,
            status=initial_status,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to process submission. Please try again.",
        )

    # If valid (not needing manual review), queue the processing
    if not needs_review:
        background_tasks.add_task(process_submission, job_id, auth_token, submission)

    return IntakeResponse(
        job_id=job_id,
        message="Your operational profile is being generated. You'll receive an email when it's ready."
        if not needs_review
        else "Your request has been received and will be reviewed by our team.",
    )


@app.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get the status of a submission."""
    submission = get_submission_by_job_id(job_id)

    if not submission:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatus(
        job_id=job_id,
        status=submission["status"],
        created_at=submission["created_at"],
        completed_at=submission["completed_at"],
    )


@app.get("/profile/{token}")
async def get_profile(token: str):
    """
    Get a profile by its auth token.

    Tokens expire after 7 days.
    """
    submission = get_submission_by_token(token)

    if not submission:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Check token expiration (7 days)
    created_at = submission["created_at"]
    if datetime.now() - created_at > timedelta(days=7):
        raise HTTPException(status_code=410, detail="This profile link has expired")

    if submission["status"] != "complete":
        raise HTTPException(
            status_code=202,
            detail={
                "status": submission["status"],
                "message": "Your profile is being prepared" if submission["status"] in ["queued", "processing"] else "Unable to generate profile",
            },
        )

    profile = get_profile_by_submission_id(submission["id"])

    if not profile:
        raise HTTPException(status_code=404, detail="Profile data not found")

    return {
        "profile": profile["profile_json"],
        "company_name": submission["company_name"],
        "created_at": profile["created_at"],
    }


@app.post("/profile/{token}/feedback")
async def submit_feedback(token: str, feedback: FeedbackRequest):
    """Submit feedback for a profile."""
    submission = get_submission_by_token(token)

    if not submission:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = get_profile_by_submission_id(submission["id"])

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if feedback.rating < 1 or feedback.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    create_feedback(
        profile_id=profile["id"],
        rating=feedback.rating,
        comment=feedback.comment,
    )

    return {"message": "Thank you for your feedback"}
