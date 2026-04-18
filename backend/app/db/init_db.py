"""
Database initialization module.

Reads schema.sql and creates all tables and extensions.
Safe for repeated execution (uses IF NOT EXISTS).
"""
import os
import sys
from pathlib import Path

from .connection import get_connection, close_connection


def init_database():
    """
    Initialize database by executing schema.sql.
    
    - Reads schema.sql from current directory
    - Creates extensions (pgcrypto, vector) if they don't exist
    - Creates all tables if they don't exist
    - Safe for repeated runs (no dropping)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Get path to schema.sql
        current_dir = Path(__file__).parent
        schema_path = current_dir / 'schema.sql'
        
        if not schema_path.exists():
            return False, f"schema.sql not found at {schema_path}"
        
        # Read schema
        with open(schema_path, 'r') as f:
            schema = f.read()
        
        # Connect to database
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Execute schema
            cursor.execute(schema)
            conn.commit()
            
            # Verify tables were created
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            table_count = len(tables)
            
            return True, f"Database initialized successfully. Created/verified {table_count} tables."
        
        except Exception as e:
            conn.rollback()
            return False, f"Error executing schema: {str(e)}"
        
        finally:
            cursor.close()
            close_connection(conn)
    
    except Exception as e:
        return False, f"Unexpected error during database initialization: {str(e)}"


if __name__ == '__main__':
    success, message = init_database()
    print(message)
    sys.exit(0 if success else 1)
