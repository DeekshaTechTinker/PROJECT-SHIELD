# MySQL Setup Guide - Step by Step

## Step 1: Install MySQL (if not already installed)

### Option A: Download MySQL Installer (Recommended for Windows)
1. Go to: https://dev.mysql.com/downloads/installer/
2. Download "MySQL Installer for Windows"
3. Run the installer and choose "Developer Default" or "Server only"
4. During installation:
   - Set a root password (remember this!)
   - Note the port (default is 3306)
   - Start MySQL Server as a Windows Service

### Option B: Use XAMPP/WAMP (Easier alternative)
1. Download XAMPP from: https://www.apachefriends.org/
2. Install XAMPP
3. Start MySQL from XAMPP Control Panel
4. Default settings:
   - Username: `root`
   - Password: (empty/blank)
   - Port: `3306`

### Option C: Check if MySQL is already installed
- Check Windows Services: Press `Win + R`, type `services.msc`, look for "MySQL"
- If MySQL service exists, note the service name

## Step 2: Verify MySQL is Running

Open a new terminal/PowerShell and try:
```powershell
# If MySQL is in PATH:
mysql --version

# Or check if the service is running:
Get-Service | Where-Object {$_.Name -like "*mysql*"}
```

## Step 3: Create the Database

### Method 1: Using MySQL Command Line (if available)
```powershell
# Connect to MySQL (replace 'your_password' with your root password)
mysql -u root -p

# Then run:
source schema.sql

# Or manually:
CREATE DATABASE IF NOT EXISTS exam_proctoring;
USE exam_proctoring;
# Then copy and paste the contents of schema.sql
```

### Method 2: Using MySQL Workbench (GUI - Recommended)
1. Download MySQL Workbench from: https://dev.mysql.com/downloads/workbench/
2. Install and open MySQL Workbench
3. Create a new connection:
   - Connection Name: `Local MySQL`
   - Hostname: `localhost`
   - Port: `3306`
   - Username: `root`
   - Password: (your MySQL root password)
   - Click "Test Connection" to verify
4. Click "OK" and connect
5. Open `schema.sql` file in a text editor
6. Copy all SQL commands
7. In MySQL Workbench, paste and execute (click the lightning bolt icon)

### Method 3: Using Python Script (We'll create this)
We'll create a Python script to set up the database automatically.

## Step 4: Configure Database Connection in app.py

You have two options:

### Option A: Edit app.py directly
Open `app.py` and modify lines 20-26:
```python
DB_CONFIG = {
    "host": "localhost",        # Change if MySQL is on different host
    "user": "root",             # Your MySQL username
    "password": "your_password", # Your MySQL root password
    "database": "exam_proctoring",
    "port": 3306,               # Change if using different port
    "autocommit": True
}
```

### Option B: Use Environment Variables (Recommended)
Set environment variables before running the app:
```powershell
# In PowerShell:
$env:DB_HOST="localhost"
$env:DB_USER="root"
$env:DB_PASSWORD="your_password_here"
$env:DB_NAME="exam_proctoring"
$env:DB_PORT="3306"
```

## Step 5: Test the Connection

We'll create a test script to verify everything works.

## Troubleshooting

### "Access denied" error
- Check username and password
- Verify MySQL is running
- Check if user has proper permissions

### "Can't connect to MySQL server"
- Verify MySQL service is running
- Check if port 3306 is correct
- Check firewall settings

### "Unknown database"
- Make sure you ran schema.sql to create the database
- Verify database name in config matches

