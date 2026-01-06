"""
Broadway Pizza Chatbot - Database Utilities
============================================
Database connection management and utility functions.
"""

import sqlite3
from typing import Optional, Any, List, Tuple
from contextlib import contextmanager

from config import DB_PATH, VALID_TABLES, setup_logging

# Setup logger for this module
logger = setup_logging(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


class DatabaseConnection:
    """
    Context manager for SQLite database connections.
    
    Usage:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM menu_items")
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.conn: Optional[sqlite3.Connection] = None
    
    def __enter__(self) -> sqlite3.Connection:
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Enable dict-like access
            logger.debug(f"Database connection opened: {self.db_path}")
            return self.conn
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise DatabaseError(f"Database connection failed: {e}")
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.conn:
            if exc_type is not None:
                self.conn.rollback()
                logger.warning(f"Transaction rolled back due to: {exc_val}")
            self.conn.close()
            logger.debug("Database connection closed")


@contextmanager
def get_db_connection(db_path: str = None):
    """
    Functional alternative to DatabaseConnection class.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM menu_items")
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path or DB_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise DatabaseError(f"Database operation failed: {e}")
    finally:
        if conn:
            conn.close()


def safe_delete_table(cursor: sqlite3.Cursor, table_name: str) -> bool:
    """
    Safely delete all rows from a table using whitelist validation.
    
    Args:
        cursor: SQLite cursor object
        table_name: Name of the table to clear
        
    Returns:
        True if deletion was successful, False if table not in whitelist
    """
    if table_name not in VALID_TABLES:
        logger.warning(f"Attempted to delete from non-whitelisted table: {table_name}")
        return False
    
    # Defense-in-depth: assertion guard even after whitelist check
    assert table_name in VALID_TABLES, f"SQL injection attempt blocked: {table_name}"
    cursor.execute(f"DELETE FROM {table_name}")  # Safe after assertion
    logger.info(f"Cleared table: {table_name}")
    return True


def execute_query(
    query: str, 
    params: Tuple = (), 
    fetch_one: bool = False,
    fetch_all: bool = True,
    commit: bool = False
) -> Optional[Any]:
    """
    Execute a query and return results.
    
    Args:
        query: SQL query string
        params: Query parameters tuple
        fetch_one: If True, fetch single row
        fetch_all: If True, fetch all rows (default)
        commit: If True, explicitly commit transaction after execution
        
    Returns:
        Query results, lastrowid for inserts, or None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = cursor.lastrowid
        
        if commit:
            conn.commit()
        return result


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None


def get_table_row_count(table_name: str) -> int:
    """Get the number of rows in a table."""
    if table_name not in VALID_TABLES:
        raise DatabaseError(f"Invalid table name: {table_name}")
    
    # Defense-in-depth: assertion guard even after validation
    assert table_name in VALID_TABLES, f"SQL injection attempt blocked: {table_name}"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")  # Safe after assertion
        result = cursor.fetchone()
        return result[0] if result else 0
