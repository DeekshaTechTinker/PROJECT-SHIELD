"""
Simple script to test MySQL connection
Run this to verify your database connection settings are correct.
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get configuration (same as app.py)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "exam_proctoring"),
    "port": int(os.getenv("DB_PORT", 3306)),
}

def test_connection():
    """Test the database connection"""
    print("Testing MySQL connection...")
    print(f"Host: {DB_CONFIG['host']}")
    print(f"User: {DB_CONFIG['user']}")
    print(f"Port: {DB_CONFIG['port']}")
    print(f"Database: {DB_CONFIG['database']}")
    print("-" * 40)
    
    try:
        # Test connection without database first
        test_config = DB_CONFIG.copy()
        test_config.pop("database", None)
        
        connection = mysql.connector.connect(**test_config)
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"✓ Connected to MySQL Server (version {db_info})")
            
            # Check if database exists
            cursor = connection.cursor()
            cursor.execute("SHOW DATABASES LIKE 'exam_proctoring'")
            result = cursor.fetchone()
            
            if result:
                print("✓ Database 'exam_proctoring' exists")
                
                # Test connection to database
                connection.close()
                connection = mysql.connector.connect(**DB_CONFIG)
                cursor = connection.cursor()
                
                # Check tables
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print(f"✓ Found {len(tables)} table(s): {', '.join([t[0] for t in tables])}")
                
                print("\n✓ All connection tests passed!")
                print("Your database is ready to use.")
                
            else:
                print("✗ Database 'exam_proctoring' does not exist")
                print("  Run 'python setup_database.py' to create it")
            
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        print(f"✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure MySQL server is running")
        print("  2. Check your credentials in app.py or environment variables")
        print("  3. Verify host and port are correct")
        if "Access denied" in str(e):
            print("  4. Check username and password")
        elif "Can't connect" in str(e):
            print("  4. Check if MySQL service is running")
        return False

if __name__ == "__main__":
    # If password is empty, ask for it
    if not DB_CONFIG["password"]:
        print("Password not set in environment variables.")
        DB_CONFIG["password"] = input("Enter MySQL root password: ").strip()
    
    test_connection()

