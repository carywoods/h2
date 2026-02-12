import psycopg
from psycopg.rows import dict_row
from contextlib import contextmanager
from typing import Generator, Optional
from datetime import datetime
import json

from app.config import get_settings


def get_connection():
    settings = get_settings()
    return psycopg.connect(settings.database_url, row_factory=dict_row)


@contextmanager
def get_db() -> Generator:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database tables."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id SERIAL PRIMARY KEY,
                    company_name VARCHAR(255) NOT NULL,
                    company_url VARCHAR(500) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    job_id UUID UNIQUE NOT NULL,
                    auth_token UUID UNIQUE NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'queued',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id SERIAL PRIMARY KEY,
                    submission_id INTEGER REFERENCES submissions(id),
                    profile_json JSONB NOT NULL,
                    data_sources_used TEXT[],
                    confidence_score VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    profile_id INTEGER REFERENCES profiles(id),
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_submissions_job_id ON submissions(job_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_submissions_auth_token ON submissions(auth_token)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_submissions_company_url ON submissions(company_url)
            """)


def create_submission(
    company_name: str,
    company_url: str,
    email: str,
    job_id: str,
    auth_token: str,
    status: str = "queued"
) -> int:
    """Create a new submission and return its ID."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO submissions (company_name, company_url, email, job_id, auth_token, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (company_name, company_url, email, job_id, auth_token, status))
            result = cur.fetchone()
            return result["id"]


def get_submission_by_job_id(job_id: str) -> Optional[dict]:
    """Get submission by job ID."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM submissions WHERE job_id = %s
            """, (job_id,))
            return cur.fetchone()


def get_submission_by_token(token: str) -> Optional[dict]:
    """Get submission by auth token."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM submissions WHERE auth_token = %s
            """, (token,))
            return cur.fetchone()


def get_submission_by_url(url: str) -> Optional[dict]:
    """Get recent submission by URL (for caching)."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM submissions
                WHERE company_url = %s
                AND status = 'complete'
                AND created_at > NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
                LIMIT 1
            """, (url,))
            return cur.fetchone()


def update_submission_status(job_id: str, status: str, completed_at: Optional[datetime] = None):
    """Update submission status."""
    with get_db() as conn:
        with conn.cursor() as cur:
            if completed_at:
                cur.execute("""
                    UPDATE submissions SET status = %s, completed_at = %s WHERE job_id = %s
                """, (status, completed_at, job_id))
            else:
                cur.execute("""
                    UPDATE submissions SET status = %s WHERE job_id = %s
                """, (status, job_id))


def create_profile(
    submission_id: int,
    profile_json: dict,
    data_sources_used: list[str],
    confidence_score: str
) -> int:
    """Create a profile and return its ID."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO profiles (submission_id, profile_json, data_sources_used, confidence_score)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (submission_id, json.dumps(profile_json), data_sources_used, confidence_score))
            result = cur.fetchone()
            return result["id"]


def get_profile_by_submission_id(submission_id: int) -> Optional[dict]:
    """Get profile by submission ID."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM profiles WHERE submission_id = %s
            """, (submission_id,))
            return cur.fetchone()


def create_feedback(profile_id: int, rating: int, comment: Optional[str] = None) -> int:
    """Create feedback and return its ID."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO feedback (profile_id, rating, comment)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (profile_id, rating, comment))
            result = cur.fetchone()
            return result["id"]
