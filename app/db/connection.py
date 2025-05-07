import pymysql
from pymysql.cursors import DictCursor
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "muscle_fitness")

def convert_datetime_to_iso(result):
    """
    Convert datetime objects to ISO format strings for JSON serialization.

    Args:
        result: A dictionary or list of dictionaries with potential datetime values

    Returns:
        The same structure with datetime objects converted to ISO format strings
    """
    if isinstance(result, list):
        return [convert_datetime_to_iso(item) for item in result]

    if isinstance(result, dict):
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, list):
                result[key] = [convert_datetime_to_iso(item) for item in value]
            elif isinstance(value, dict):
                result[key] = convert_datetime_to_iso(value)

    return result

def get_connection():
    """
    Create and return a connection to the MySQL database.
    Uses environment variables for configuration.
    """
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=DictCursor,
            charset='utf8mb4'
        )
        return connection
    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL database: {e}")
        raise

def execute_query(query, params=None, fetch=True):
    """
    Execute an SQL query and return the results.

    Args:
        query (str): SQL query to execute
        params (tuple, dict, optional): Parameters for the query
        fetch (bool): Whether to fetch results or not (for SELECT vs. INSERT/UPDATE)

    Returns:
        List of dictionaries for SELECT queries, or
        The last row id for INSERT queries, or
        The number of affected rows for UPDATE/DELETE queries
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)

            if fetch:
                result = cursor.fetchall()
                # Convert datetime objects to strings
                result = convert_datetime_to_iso(result)
                return result
            else:
                connection.commit()

                # For INSERT statements, return the last row id
                if query.strip().upper().startswith("INSERT"):
                    return cursor.lastrowid
                # For UPDATE/DELETE statements, return affected rows
                return cursor.rowcount
    except pymysql.MySQLError as e:
        print(f"Database error: {e}")
        connection.rollback()
        raise
    finally:
        connection.close()

def execute_many(query, params_list):
    """
    Execute an SQL query with multiple parameter sets.

    Args:
        query (str): SQL query to execute
        params_list (list): List of parameter tuples or dictionaries

    Returns:
        int: Number of affected rows
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            rows = cursor.executemany(query, params_list)
            connection.commit()
            return rows
    except pymysql.MySQLError as e:
        print(f"Database error: {e}")
        connection.rollback()
        raise
    finally:
        connection.close()
