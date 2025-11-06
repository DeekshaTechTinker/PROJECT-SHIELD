# Real-Time FastAPI & MySQL Exam Proctoring System

A comprehensive full-stack web application for proctored online examinations with real-time event monitoring and risk assessment.

## Features

- **Real-time Proctoring**: Captures keystrokes, mouse movements, fullscreen exits, and focus loss events
- **Risk Assessment**: Automated risk scoring based on suspicious activities
- **Admin Dashboard**: Visual timeline charts and detailed event logs
- **Fullscreen Enforcement**: Automatic fullscreen mode with exit monitoring
- **Batch Logging**: High-performance event batching for efficient data ingestion

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: MySQL
- **Frontend**: HTML5, JavaScript, Tailwind CSS
- **Visualization**: Chart.js

## Prerequisites

- Python 3.8+
- MySQL 5.7+ or MySQL 8.0+
- pip (Python package manager)

## Installation

### 1. Clone or Download the Project

```bash
cd Exam_proc_deeksha
```

### 2. Set Up MySQL Database

1. Start your MySQL server
2. Log in to MySQL:
   ```bash
   mysql -u root -p
   ```
3. Run the schema file:
   ```bash
   source schema.sql
   ```
   Or:
   ```bash
   mysql -u root -p < schema.sql
   ```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Database Connection

Set environment variables or modify the `DB_CONFIG` in `app.py`:

**Option 1: Environment Variables (Recommended)**
```bash
# Windows PowerShell
$env:DB_HOST="localhost"
$env:DB_USER="root"
$env:DB_PASSWORD="your_password"
$env:DB_NAME="exam_proctoring"
$env:DB_PORT="3306"
$env:JWT_SECRET="your-secret-key-change-in-production"

# Linux/Mac
export DB_HOST="localhost"
export DB_USER="root"
export DB_PASSWORD="your_password"
export DB_NAME="exam_proctoring"
export DB_PORT="3306"
export JWT_SECRET="your-secret-key-change-in-production"
```

**Option 2: Edit app.py directly**
Modify the `DB_CONFIG` dictionary in `app.py` (lines 20-26).

### 5. Run the Application

```bash
python app.py
```

Or using uvicorn directly:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at:
- **User Interface**: http://localhost:8000/user
- **Admin Dashboard**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/docs

## Usage

### Creating Users

1. Navigate to http://localhost:8000/user
2. Click "Sign Up" tab
3. Create a regular user account

### Creating Admin Account

You can create an admin account by:
1. Using the signup endpoint with `role: "admin"` in the request body
2. Or directly in MySQL:
   ```sql
   INSERT INTO users (username, password_hash, role) 
   VALUES ('admin', SHA2('your_password', 256), 'admin');
   ```

### Taking a Test (User)

1. Log in at http://localhost:8000/user
2. Click "Start Test"
3. The browser will automatically enter fullscreen mode
4. Answer the questions while the system monitors your activity
5. Submit the test when finished

**Important**: 
- Do not exit fullscreen more than 2 times (3rd exit will terminate the test)
- Keep the browser tab focused
- All activities are logged in real-time

### Admin Dashboard

1. Log in at http://localhost:8000/admin with admin credentials
2. View all active test-takers
3. Click on a user to see:
   - Risk score and level
   - Activity timeline chart
   - Detailed event log
   - Session-specific data

## API Endpoints

### Authentication
- `POST /api/signup` - Register a new user
- `POST /api/login` - Login and get JWT token

### Session Management
- `POST /api/session/start` - Start a new test session
- `POST /api/session/end` - End a test session

### Logging
- `POST /api/log` - Batch submit proctoring events

### Admin
- `GET /api/admin/users` - Get all users with active sessions
- `GET /api/admin/logs/{user_id}` - Get logs for a user
- `GET /api/admin/risk/{user_id}/{session_id}` - Calculate risk score

## Risk Calculation

The system calculates risk scores based on:

1. **Fullscreen Breaches** (50 points): More than 3 fullscreen exits
2. **Focus Loss** (30 points): Any tab switch or window blur events
3. **Time Spikes** (20 points each): Periods of 45+ seconds with no activity during an active test

**Risk Levels:**
- **LOW**: 0-39 points
- **MEDIUM**: 40-69 points
- **HIGH**: 70-100 points

## Proctoring Events

The system captures:
- `KEYSTROKE`: All keyboard inputs
- `MOUSE_MOVE`: Mouse movements (rate-limited to 1 per 500ms)
- `FULLSCREEN_EXIT`: When user exits fullscreen mode
- `FOCUS_LOST`: When browser tab loses focus or becomes hidden

## Database Schema

### Tables

1. **users**: User accounts and authentication
2. **tests**: Test definitions and questions
3. **proctor_logs**: Real-time event logs (indexed for performance)
4. **test_sessions**: Active and completed test sessions

See `schema.sql` for complete schema definition.

## Security Notes

⚠️ **Important**: This is a demonstration system. For production use:

1. Change the `JWT_SECRET` to a strong, random value
2. Use HTTPS for all connections
3. Implement rate limiting on API endpoints
4. Add input validation and sanitization
5. Use environment variables for sensitive configuration
6. Implement proper password hashing (consider bcrypt instead of SHA256)
7. Add CORS configuration if serving from different domains
8. Implement session timeout and token refresh

## Troubleshooting

### Database Connection Errors

- Verify MySQL is running: `mysqladmin ping`
- Check database credentials in `DB_CONFIG`
- Ensure the database exists: `SHOW DATABASES;`

### Import Errors

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

### Fullscreen Not Working

- Some browsers require user interaction before allowing fullscreen
- Check browser console for errors
- Ensure HTTPS in production (some browsers require it)

## License

This project is provided as-is for educational and demonstration purposes.

## Support

For issues or questions, please check:
- FastAPI documentation: https://fastapi.tiangolo.com/
- MySQL documentation: https://dev.mysql.com/doc/

