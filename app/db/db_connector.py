import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

def get_db_connection():
    """Establishes a connection to the MySQL database."""
    try:
        # When running in Docker, the database host should be the service name ('db')
        # not 'localhost', as each container has its own localhost
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "db"), # Default to 'db' for Docker environment
            user=os.getenv("MYSQL_USER", "root"), # Default to 'root' if not set
            password=os.getenv("MYSQL_PASSWORD", "password"), # Default to 'password' to match docker-compose.yml
            database=os.getenv("MYSQL_DATABASE", "muscle_fitness"), # Default to 'muscle_fitness' if not set
            port=int(os.getenv("MYSQL_PORT", 3306)) # Default to 3306 if not set, ensure it's an integer
        )
        if conn.is_connected():
            # print("Successfully connected to the database") # Optional: for debugging
            return conn
        else:
            # print("Failed to connect to the database.") # Optional: for debugging
            return None
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        # In a real app, you might want to raise this or handle it more gracefully,
        # e.g., by raising a custom exception that can be caught by FastAPI
        raise ConnectionError(f"Database connection failed: {err}") from err

# Example usage (for testing connection directly):
# if __name__ == "__main__":
#     connection = get_db_connection()
#     if connection:
#         print("Connection successful!")
#         cursor = connection.cursor()
#         cursor.execute("SELECT DATABASE();")
#         db_name = cursor.fetchone()
#         print(f"Connected to database: {db_name[0] if db_name else 'N/A'}")
#         cursor.close()
#         connection.close()
#     else:
#         print("Connection failed.")
