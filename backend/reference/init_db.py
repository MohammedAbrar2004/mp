"""
Database initialization module for EchoMind.
Executes schema.sql to set up the PostgreSQL database.
Includes safety checks to warn if tables already exist.
"""

import os
from connection import get_connection


def check_tables_exist(cursor):
    """
    Check if main tables already exist in the database.
    
    Args:
        cursor: Database cursor
        
    Returns:
        bool: True if tables exist, False otherwise
    """
    try:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'users'
            )
        """)
        return cursor.fetchone()[0]
    except Exception:
        return False


def init_database():
    """
    Initialize the database by executing schema.sql.
    
    Reads the schema.sql file and executes all SQL statements.
    Warns if tables already exist to prevent accidental data loss.
    Commits the transaction if successful, otherwise raises an error.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    connection = None
    cursor = None
    
    try:
        # Get database connection
        connection = get_connection()
        cursor = connection.cursor()
        
        # Check if tables already exist
        if check_tables_exist(cursor):
            print("⚠ WARNING: Database tables already exist!")
            print("⚠ The schema.sql uses 'IF NOT EXISTS' to prevent overwrites.")
            print("⚠ Existing data will NOT be modified.")
            response = input("Continue with initialization? (yes/no): ").lower().strip()
            if response not in ('yes', 'y'):
                print("✗ Initialization cancelled by user.")
                return
            print("Proceeding with initialization...")
        
        # Read and execute schema
        with open(schema_path, "r") as schema_file:
            schema_sql = schema_file.read()
        
        cursor.execute(schema_sql)
        connection.commit()
        
        print("✓ Database schema initialized successfully.")
        
    except FileNotFoundError:
        print(f"✗ Schema file not found at {schema_path}")
        raise
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


if __name__ == "__main__":
    init_database()
