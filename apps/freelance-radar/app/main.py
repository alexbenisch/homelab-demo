from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import httpx
from datetime import datetime
import json

app = FastAPI(title="Freelance Radar", version="1.0.0")

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")
ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"

DB_CONFIG = {
    "host": os.getenv("DATABASE_HOST", "postgres"),
    "dbname": os.getenv("DATABASE_NAME", "radar"),
    "user": os.getenv("POSTGRES_USER", "radar"),
    "password": os.getenv("POSTGRES_PASSWORD", "radar123"),
}


class JobSearchRequest(BaseModel):
    keywords: str
    country: str = "us"
    location: Optional[str] = None
    max_days_old: Optional[int] = 7
    results_per_page: int = 20
    page: int = 1


class JobResult(BaseModel):
    id: str
    title: str
    description: str
    company: Optional[str]
    location: Optional[str]
    salary_min: Optional[float]
    salary_max: Optional[float]
    contract_type: Optional[str]
    contract_time: Optional[str]
    redirect_url: str
    created: str


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG)


def init_db():
    """Initialize database schema."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS job_searches (
            id SERIAL PRIMARY KEY,
            search_query TEXT NOT NULL,
            country VARCHAR(10) NOT NULL,
            location TEXT,
            result_count INTEGER,
            mean_salary FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            search_id INTEGER REFERENCES job_searches(id),
            job_id VARCHAR(255) UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            company TEXT,
            location TEXT,
            salary_min FLOAT,
            salary_max FLOAT,
            contract_type VARCHAR(50),
            contract_time VARCHAR(50),
            redirect_url TEXT,
            created_date TIMESTAMP,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        init_db()
    except Exception as e:
        print(f"Failed to initialize database: {e}")


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "freelance-radar"}


@app.get("/db")
def db_check():
    """Database connectivity check."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {"db": "connected", "test_query": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


@app.post("/search", response_model=dict)
async def search_jobs(request: JobSearchRequest):
    """Search for jobs using Adzuna API and store results."""
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        raise HTTPException(status_code=500, detail="Adzuna API credentials not configured")

    url = f"{ADZUNA_BASE_URL}/{request.country}/search/{request.page}"

    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "results_per_page": request.results_per_page,
        "what": request.keywords,
    }

    if request.location:
        params["where"] = request.location

    if request.max_days_old:
        params["max_days_old"] = request.max_days_old

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO job_searches (search_query, country, location, result_count, mean_salary)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (request.keywords, request.country, request.location, data.get("count", 0), data.get("mean", 0)))

        search_id = cur.fetchone()[0]

        jobs_saved = 0
        for job in data.get("results", []):
            try:
                cur.execute("""
                    INSERT INTO jobs (
                        search_id, job_id, title, description, company, location,
                        salary_min, salary_max, contract_type, contract_time,
                        redirect_url, created_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (job_id) DO NOTHING
                """, (
                    search_id,
                    job.get("id"),
                    job.get("title"),
                    job.get("description"),
                    job.get("company", {}).get("display_name"),
                    job.get("location", {}).get("display_name"),
                    job.get("salary_min"),
                    job.get("salary_max"),
                    job.get("contract_type"),
                    job.get("contract_time"),
                    job.get("redirect_url"),
                    datetime.fromisoformat(job.get("created").replace("Z", "+00:00")) if job.get("created") else None
                ))
                jobs_saved += 1
            except Exception as e:
                print(f"Error saving job {job.get('id')}: {e}")

        conn.commit()
        cur.close()
        conn.close()

        return {
            "search_id": search_id,
            "total_results": data.get("count", 0),
            "mean_salary": data.get("mean", 0),
            "results_returned": len(data.get("results", [])),
            "jobs_saved": jobs_saved,
            "results": data.get("results", [])
        }

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Adzuna API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/searches")
def get_searches(limit: int = Query(default=10, le=100)):
    """Get recent job searches."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT id, search_query, country, location, result_count, mean_salary, created_at
            FROM job_searches
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))

        searches = cur.fetchall()
        cur.close()
        conn.close()

        return {"searches": searches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch searches: {str(e)}")


@app.get("/jobs")
def get_jobs(search_id: Optional[int] = None, limit: int = Query(default=20, le=100)):
    """Get saved jobs, optionally filtered by search_id."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        if search_id:
            cur.execute("""
                SELECT * FROM jobs
                WHERE search_id = %s
                ORDER BY saved_at DESC
                LIMIT %s
            """, (search_id, limit))
        else:
            cur.execute("""
                SELECT * FROM jobs
                ORDER BY saved_at DESC
                LIMIT %s
            """, (limit,))

        jobs = cur.fetchall()
        cur.close()
        conn.close()

        return {"jobs": jobs, "count": len(jobs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs: {str(e)}")


@app.get("/stats")
def get_stats():
    """Get statistics about saved jobs and searches."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT COUNT(*) as total_searches FROM job_searches")
        total_searches = cur.fetchone()["total_searches"]

        cur.execute("SELECT COUNT(*) as total_jobs FROM jobs")
        total_jobs = cur.fetchone()["total_jobs"]

        cur.execute("""
            SELECT AVG(salary_min) as avg_min_salary, AVG(salary_max) as avg_max_salary
            FROM jobs
            WHERE salary_min IS NOT NULL AND salary_max IS NOT NULL
        """)
        salary_stats = cur.fetchone()

        cur.close()
        conn.close()

        return {
            "total_searches": total_searches,
            "total_jobs": total_jobs,
            "avg_min_salary": salary_stats["avg_min_salary"],
            "avg_max_salary": salary_stats["avg_max_salary"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")
