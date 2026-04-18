"""
PostgreSQL connection module for EchoMind.
Handles database connection using environment variables.
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_connection():
    """
    Create and return a PostgreSQL database connection.
    
    Returns:
        psycopg2.connection: A database connection object.
        
    Raises:
        psycopg2.Error: If connection fails.
    """
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        print("[OK] Database connection established successfully.")
        return connection
    except psycopg2.Error as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        raise
