"""
Database connection management module.

Provides connection pooling and access to PostgreSQL database.
"""
import os
import psycopg2
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))


def get_connection():
    """
    Establish and return a PostgreSQL connection.
    
    Reads database configuration from .env file.
    
    Returns:
        psycopg2.extensions.connection: Active database connection
        
    Raises:
        psycopg2.OperationalError: If connection fails
        KeyError: If required environment variables are missing
    """
    try:
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'mp'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
        }
        
        conn = psycopg2.connect(**db_config)
        conn.autocommit = False
        return conn
    
    except psycopg2.OperationalError as e:
        raise psycopg2.OperationalError(
            f"Failed to connect to database at {db_config.get('host')}:{db_config.get('port')} - {str(e)}"
        )
    except Exception as e:
        raise Exception(f"Unexpected error during database connection: {str(e)}")


def close_connection(conn):
    """
    Safely close database connection.
    
    Args:
        conn: psycopg2 connection object
    """
    if conn:
        try:
            conn.close()
        except Exception as e:
            print(f"Error closing connection: {e}")
