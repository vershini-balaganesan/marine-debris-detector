# database/connection.py
"""
Single place to open a PostgreSQL connection.
Raises a clear ConnectionError if PostgreSQL isn't reachable, instead of
letting a raw psycopg2 traceback surface in the dashboard.
"""

import psycopg2
from config import DATABASE_URL, DB_CONFIG


def get_connection():
    try:
        if DATABASE_URL:
            return psycopg2.connect(DATABASE_URL)
        return psycopg2.connect(**DB_CONFIG)
    except (psycopg2.OperationalError, psycopg2.ProgrammingError) as e:
        raise ConnectionError(
            "Could not connect to PostgreSQL. Set DATABASE_URL to a real PostgreSQL "
            "connection string, or remove the placeholder and use local DB_* settings. "
            f"Original error: {e}"
        )