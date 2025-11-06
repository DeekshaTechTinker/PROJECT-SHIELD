"""
FastAPI Exam Proctoring System
Real-time proctoring with risk assessment dashboard
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import pooling
import hashlib
import secrets
import jwt
import json
import os
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "exam_proctoring"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "autocommit": True
}

# Create connection pool
db_pool = pooling.MySQLConnectionPool(
    pool_name="exam_pool",
    pool_size=5,
    pool_reset_session=True,
    **DB_CONFIG
)

app = FastAPI(title="Exam Proctoring System")
security = HTTPBearer()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic Models
class UserSignup(BaseModel):
    username: str
    password: str
    role: str = "user"

class UserLogin(BaseModel):
    username: str
    password: str

class LogEvent(BaseModel):
    session_id: str
    timestamp: str
    event_type: str
    event_data: Optional[Dict[str, Any]] = None

class LogBatch(BaseModel):
    events: List[LogEvent]

class QuestionResponse(BaseModel):
    session_id: str
    question_number: int
    question_type: str
    answer: Optional[str] = None
    time_taken_seconds: int = 0
    first_viewed_at: str

class RiskResponse(BaseModel):
    user_id: int
    session_id: str
    risk_score: int
    risk_level: str
    details: Dict[str, Any]

# Database helper
@contextmanager
def get_db_connection():
    conn = db_pool.get_connection()
    try:
        yield conn
    finally:
        conn.close()

# Authentication helpers
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash

def create_token(username: str, user_id: int, role: str) -> str:
    payload = {
        "username": username,
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_admin(token_data: dict = Depends(verify_token)):
    if token_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return token_data

# API Routes
@app.post("/api/signup")
async def signup(user_data: UserSignup):
    """User registration endpoint"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (user_data.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create user
        password_hash = hash_password(user_data.password)
        role = "admin" if user_data.role == "admin" else "user"
        
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            (user_data.username, password_hash, role)
        )
        user_id = cursor.lastrowid
        
        token = create_token(user_data.username, user_id, role)
        
        return {
            "message": "User created successfully",
            "token": token,
            "user_id": user_id,
            "role": role
        }

@app.post("/api/login")
async def login(credentials: UserLogin):
    """User login endpoint"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = %s",
            (credentials.username,)
        )
        user = cursor.fetchone()
        
        if not user or not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_token(user["username"], user["id"], user["role"])
        
        return {
            "message": "Login successful",
            "token": token,
            "user_id": user["id"],
            "role": user["role"]
        }

@app.post("/api/log")
async def log_events(batch: LogBatch, token_data: dict = Depends(verify_token)):
    """Batch log events endpoint - high performance"""
    user_id = token_data["user_id"]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Batch insert for performance
        insert_query = """
            INSERT INTO proctor_logs (user_id, session_id, timestamp, event_type, event_data)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        values = []
        for event in batch.events:
            values.append((
                user_id,
                event.session_id,
                datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')),
                event.event_type,
                json.dumps(event.event_data) if event.event_data else None
            ))
        
        cursor.executemany(insert_query, values)
        conn.commit()
        
        return {"message": f"Logged {len(batch.events)} events", "count": len(batch.events)}

@app.post("/api/session/start")
async def start_session(test_id: Optional[int] = None, token_data: dict = Depends(verify_token)):
    """Start a new test session"""
    user_id = token_data["user_id"]
    session_id = secrets.token_urlsafe(32)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO test_sessions (user_id, session_id, test_id, status) VALUES (%s, %s, %s, 'active')",
            (user_id, session_id, test_id)
        )
        conn.commit()
    
    return {"session_id": session_id, "message": "Session started"}

@app.post("/api/session/end")
async def end_session(session_id: str, token_data: dict = Depends(verify_token)):
    """End a test session"""
    user_id = token_data["user_id"]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE test_sessions SET status = 'completed', ended_at = NOW() WHERE session_id = %s AND user_id = %s",
            (session_id, user_id)
        )
        conn.commit()
    
    return {"message": "Session ended"}

@app.post("/api/question/response")
async def save_question_response(response: QuestionResponse, token_data: dict = Depends(verify_token)):
    """Save or update question response with timing"""
    user_id = token_data["user_id"]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if response already exists
        cursor.execute(
            """
            SELECT id FROM question_responses 
            WHERE user_id = %s AND session_id = %s AND question_number = %s
            """,
            (user_id, response.session_id, response.question_number)
        )
        existing = cursor.fetchone()
        
        first_viewed = datetime.fromisoformat(response.first_viewed_at.replace('Z', '+00:00'))
        last_updated = datetime.utcnow()
        
        if existing:
            # Update existing response
            cursor.execute(
                """
                UPDATE question_responses 
                SET answer = %s, time_taken_seconds = %s, last_updated_at = %s
                WHERE user_id = %s AND session_id = %s AND question_number = %s
                """,
                (response.answer, response.time_taken_seconds, last_updated, 
                 user_id, response.session_id, response.question_number)
            )
        else:
            # Insert new response
            cursor.execute(
                """
                INSERT INTO question_responses 
                (user_id, session_id, question_number, question_type, answer, time_taken_seconds, first_viewed_at, last_updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, response.session_id, response.question_number, response.question_type,
                 response.answer, response.time_taken_seconds, first_viewed, last_updated)
            )
        
        conn.commit()
        return {"message": "Question response saved", "question_number": response.question_number}

@app.get("/api/admin/logs/{user_id}")
async def get_user_logs(user_id: int, session_id: Optional[str] = None, token_data: dict = Depends(require_admin)):
    """Get all logs for a specific user/session"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        if session_id:
            cursor.execute(
                """
                SELECT id, user_id, session_id, timestamp, event_type, event_data
                FROM proctor_logs
                WHERE user_id = %s AND session_id = %s
                ORDER BY timestamp ASC
                """,
                (user_id, session_id)
            )
        else:
            cursor.execute(
                """
                SELECT id, user_id, session_id, timestamp, event_type, event_data
                FROM proctor_logs
                WHERE user_id = %s
                ORDER BY timestamp ASC
                """,
                (user_id,)
            )
        
        logs = cursor.fetchall()
        
        # Parse JSON event_data
        for log in logs:
            if log["event_data"]:
                log["event_data"] = json.loads(log["event_data"])
        
        return {"logs": logs, "count": len(logs)}

@app.get("/api/admin/question-responses/{user_id}")
async def get_question_responses(user_id: int, session_id: Optional[str] = None, token_data: dict = Depends(require_admin)):
    """Get question responses with timing for a user/session"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        if session_id:
            cursor.execute(
                """
                SELECT question_number, question_type, answer, time_taken_seconds, 
                       first_viewed_at, last_updated_at
                FROM question_responses
                WHERE user_id = %s AND session_id = %s
                ORDER BY question_number ASC
                """,
                (user_id, session_id)
            )
        else:
            cursor.execute(
                """
                SELECT question_number, question_type, answer, time_taken_seconds, 
                       first_viewed_at, last_updated_at, session_id
                FROM question_responses
                WHERE user_id = %s
                ORDER BY session_id, question_number ASC
                """,
                (user_id,)
            )
        
        responses = cursor.fetchall()
        
        # Convert datetime objects to strings
        for response in responses:
            if response["first_viewed_at"]:
                response["first_viewed_at"] = response["first_viewed_at"].isoformat()
            if response["last_updated_at"]:
                response["last_updated_at"] = response["last_updated_at"].isoformat()
        
        return {"responses": responses, "count": len(responses)}

@app.get("/api/admin/users")
async def get_all_users(token_data: dict = Depends(require_admin)):
    """Get all users with active sessions"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT u.id, u.username, u.role,
                   ts.session_id, ts.status, ts.started_at
            FROM users u
            LEFT JOIN test_sessions ts ON u.id = ts.user_id AND ts.status = 'active'
            WHERE u.role = 'user'
            ORDER BY ts.started_at DESC
        """)
        users = cursor.fetchall()
        return {"users": users}

@app.get("/api/admin/risk/{user_id}/{session_id}", response_model=RiskResponse)
async def calculate_risk(user_id: int, session_id: str, token_data: dict = Depends(require_admin)):
    """Calculate risk score for a user session"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Get all logs for this session
        cursor.execute("""
            SELECT event_type, timestamp, event_data
            FROM proctor_logs
            WHERE user_id = %s AND session_id = %s
            ORDER BY timestamp ASC
        """, (user_id, session_id))
        
        logs = cursor.fetchall()
        
        # Check session status
        cursor.execute("""
            SELECT status, started_at
            FROM test_sessions
            WHERE user_id = %s AND session_id = %s
        """, (user_id, session_id))
        session_info = cursor.fetchone()
        
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Risk calculation - Comprehensive scoring system
        risk_score = 0
        details = {
            "fullscreen_exits": 0,
            "focus_lost_count": 0,
            "tab_switches": 0,
            "time_spikes": 0,
            "total_events": len(logs),
            "breakdown": {}
        }
        
        # Parse event data to get more details
        
        # 1. Full-screen breach check - Tiered scoring
        fullscreen_exits = sum(1 for log in logs if log["event_type"] == "FULLSCREEN_EXIT")
        details["fullscreen_exits"] = fullscreen_exits
        
        if fullscreen_exits > 0:
            # Tiered scoring: Each exit is penalized, with increasing severity
            if fullscreen_exits == 1:
                fullscreen_points = 20
            elif fullscreen_exits == 2:
                fullscreen_points = 45  # 20 + 25
            elif fullscreen_exits == 3:
                fullscreen_points = 75  # 20 + 25 + 30
            else:  # 4 or more
                fullscreen_points = 75 + (fullscreen_exits - 3) * 15  # Additional 15 per exit after 3rd
            risk_score += fullscreen_points
            details["breakdown"]["fullscreen_exits"] = fullscreen_points
        
        # 2. Tab switch/Focus lost check - Per event scoring with distinction
        focus_lost_events = [log for log in logs if log["event_type"] == "FOCUS_LOST"]
        focus_lost_count = len(focus_lost_events)
        details["focus_lost_count"] = focus_lost_count
        
        # Count actual tab switches (events with reason='tab_switch')
        tab_switches = 0
        other_focus_lost = 0
        
        for event in focus_lost_events:
            event_data = event.get("event_data")
            if event_data:
                if isinstance(event_data, str):
                    try:
                        event_data = json.loads(event_data)
                    except:
                        event_data = {}
                
                reason = event_data.get("reason", "")
                if reason == "tab_switch" or "tab" in reason.lower():
                    tab_switches += 1
                else:
                    other_focus_lost += 1
            else:
                # If no event_data, assume it's a tab switch (most common)
                tab_switches += 1
        
        details["tab_switches"] = tab_switches
        
        # Tab switches are more serious - higher penalty
        if tab_switches > 0:
            # Tiered scoring for tab switches
            if tab_switches == 1:
                tab_points = 15
            elif tab_switches == 2:
                tab_points = 35  # 15 + 20
            elif tab_switches >= 3:
                tab_points = 35 + (tab_switches - 2) * 20  # 20 per additional switch after 2nd
            risk_score += tab_points
            details["breakdown"]["tab_switches"] = tab_points
        
        # Other focus lost events (window blur, etc.) - lower penalty
        if other_focus_lost > 0:
            other_focus_points = other_focus_lost * 5  # 5 points each
            risk_score += other_focus_points
            details["breakdown"]["other_focus_lost"] = other_focus_points
        
        # 3. Time spikes check (45+ seconds of inactivity during active session)
        time_spikes = 0
        if session_info["status"] == "active" and len(logs) > 1:
            activity_events = [log for log in logs if log["event_type"] in ["KEYSTROKE", "MOUSE_MOVE"]]
            
            if len(activity_events) > 1:
                for i in range(len(activity_events) - 1):
                    current_time = activity_events[i]["timestamp"]
                    next_time = activity_events[i + 1]["timestamp"]
                    
                    # Handle different datetime formats
                    if isinstance(current_time, str):
                        try:
                            current_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
                        except:
                            current_time = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
                    elif not isinstance(current_time, datetime):
                        current_time = datetime.fromisoformat(str(current_time))
                    
                    if isinstance(next_time, str):
                        try:
                            next_time = datetime.fromisoformat(next_time.replace('Z', '+00:00'))
                        except:
                            next_time = datetime.strptime(next_time, '%Y-%m-%d %H:%M:%S')
                    elif not isinstance(next_time, datetime):
                        next_time = datetime.fromisoformat(str(next_time))
                    
                    time_diff = (next_time - current_time).total_seconds()
                    if time_diff > 45:
                        time_spikes += 1
        
        details["time_spikes"] = time_spikes
        if time_spikes > 0:
            time_spike_points = time_spikes * 25  # 25 points per time spike
            risk_score += time_spike_points
            details["breakdown"]["time_spikes"] = time_spike_points
        
        # Cap risk score at 100
        risk_score = min(risk_score, 100)
        
        # Determine risk level with updated thresholds
        if risk_score >= 70:
            risk_level = "HIGH"
        elif risk_score >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return RiskResponse(
            user_id=user_id,
            session_id=session_id,
            risk_score=min(risk_score, 100),  # Cap at 100
            risk_level=risk_level,
            details=details
        )

# Frontend Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page"""
    with open("templates/landing.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/user", response_class=HTMLResponse)
async def user_interface():
    """User test interface"""
    with open("templates/user.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    """Admin dashboard"""
    with open("templates/admin.html", "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

