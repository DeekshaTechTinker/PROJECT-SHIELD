"""
Quick script to create an admin user
"""

import mysql.connector
from mysql.connector import Error
import hashlib
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_admin():
    """Create an admin user"""
    # Database config
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "exam_proctoring"),
        "port": int(os.getenv("DB_PORT", 3306)),
    }
    
    print("=" * 50)
    print("Create Admin User")
    print("=" * 50)
    
    username = input("Enter admin username [admin]: ").strip() or "admin"
    password = input("Enter admin password: ").strip()
    
    if not password:
        print("✗ Password cannot be empty!")
        return
    
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            print(f"✗ Username '{username}' already exists!")
            overwrite = input("Do you want to update the password? (y/n): ").strip().lower()
            if overwrite == 'y':
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute(
                    "UPDATE users SET password_hash = %s, role = 'admin' WHERE username = %s",
                    (password_hash, username)
                )
                connection.commit()
                print(f"✓ Admin user '{username}' password updated!")
            else:
                print("Cancelled.")
            cursor.close()
            connection.close()
            return
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create admin user
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'admin')",
            (username, password_hash)
        )
        connection.commit()
        
        print(f"\n✓ Admin user '{username}' created successfully!")
        print("\nAdmin Credentials:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print("\nYou can now log in at: http://localhost:8000/admin")
        
        cursor.close()
        connection.close()
        
    except Error as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    create_admin()

