"""
Database Setup Script
This script will help you set up the MySQL database for the Exam Proctoring System.
Run this script to create the database and tables automatically.
"""

import mysql.connector
from mysql.connector import Error
import os
import sys

def get_db_config():
    """Get database configuration from environment variables or user input"""
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "port": int(os.getenv("DB_PORT", 3306))
    }
    
    # If password not in env, ask user
    if not config["password"]:
        print("\n=== MySQL Database Setup ===")
        print("Please provide your MySQL connection details:")
        config["host"] = input(f"Host [{config['host']}]: ").strip() or config["host"]
        config["user"] = input(f"Username [{config['user']}]: ").strip() or config["user"]
        config["password"] = input("Password: ").strip()
        port_input = input(f"Port [{config['port']}]: ").strip()
        if port_input:
            config["port"] = int(port_input)
    
    return config

def test_connection(config):
    """Test MySQL connection"""
    try:
        print("\nTesting MySQL connection...")
        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            print("✓ Successfully connected to MySQL server!")
            db_info = connection.get_server_info()
            print(f"  MySQL Server version: {db_info}")
            connection.close()
            return True
    except Error as e:
        print(f"✗ Connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("  1. Make sure MySQL server is running")
        print("  2. Check your username and password")
        print("  3. Verify the host and port are correct")
        return False

def create_database(config):
    """Create the exam_proctoring database"""
    try:
        print("\nCreating database 'exam_proctoring'...")
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        cursor.execute("CREATE DATABASE IF NOT EXISTS exam_proctoring")
        print("✓ Database 'exam_proctoring' created/exists")
        
        cursor.close()
        connection.close()
        return True
    except Error as e:
        print(f"✗ Failed to create database: {e}")
        return False

def setup_tables(config):
    """Create all tables from schema.sql"""
    try:
        print("\nSetting up database tables...")
        config["database"] = "exam_proctoring"
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Read and execute schema.sql
        with open("schema.sql", "r", encoding="utf-8") as f:
            sql_script = f.read()
        
        # Split by semicolons and execute each statement
        statements = [s.strip() for s in sql_script.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for statement in statements:
            if statement:
                try:
                    cursor.execute(statement)
                except Error as e:
                    # Ignore "table already exists" errors
                    if "already exists" not in str(e).lower():
                        print(f"  Warning: {e}")
        
        connection.commit()
        print("✓ All tables created successfully!")
        
        # Verify tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\n  Created tables: {', '.join([t[0] for t in tables])}")
        
        cursor.close()
        connection.close()
        return True
    except Error as e:
        print(f"✗ Failed to create tables: {e}")
        return False
    except FileNotFoundError:
        print("✗ schema.sql file not found!")
        print("  Make sure schema.sql is in the same directory as this script.")
        return False

def create_admin_user(config):
    """Optionally create an admin user"""
    try:
        print("\n=== Create Admin User ===")
        create = input("Would you like to create an admin user now? (y/n): ").strip().lower()
        
        if create != 'y':
            return
        
        config["database"] = "exam_proctoring"
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        username = input("Admin username: ").strip()
        password = input("Admin password: ").strip()
        
        # Hash password (simple SHA256 - same as app.py)
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'admin')",
            (username, password_hash)
        )
        connection.commit()
        
        print(f"✓ Admin user '{username}' created successfully!")
        
        cursor.close()
        connection.close()
    except Error as e:
        print(f"✗ Failed to create admin user: {e}")

def main():
    """Main setup function"""
    print("=" * 50)
    print("Exam Proctoring System - Database Setup")
    print("=" * 50)
    
    # Get configuration
    config = get_db_config()
    
    # Test connection
    if not test_connection(config):
        print("\nSetup aborted. Please fix connection issues and try again.")
        sys.exit(1)
    
    # Create database
    if not create_database(config):
        print("\nSetup aborted.")
        sys.exit(1)
    
    # Setup tables
    if not setup_tables(config):
        print("\nSetup aborted.")
        sys.exit(1)
    
    # Create admin user
    create_admin_user(config)
    
    print("\n" + "=" * 50)
    print("✓ Database setup completed successfully!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Make sure your app.py has the correct database configuration")
    print("2. Run: python app.py")
    print("3. Access the application at http://localhost:8000")
    print("\nDatabase configuration for app.py:")
    print(f"  Host: {config['host']}")
    print(f"  User: {config['user']}")
    print(f"  Port: {config['port']}")
    print(f"  Database: exam_proctoring")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)

