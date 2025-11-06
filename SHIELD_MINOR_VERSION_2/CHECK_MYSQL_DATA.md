# How to Check if MySQL is Getting Updated

## Method 1: Using MySQL Workbench (Visual - Recommended)

### Step 1: View Proctor Logs (Real-time Events)
1. Open MySQL Workbench
2. In the **Navigator** panel (left side), expand:
   - `exam_proctoring` schema
   - `Tables`
   - Right-click on `proctor_logs`
   - Select **"Select Rows - Limit 1000"**

3. You'll see a table with columns:
   - `id` - Auto-increment ID
   - `user_id` - User who generated the event
   - `session_id` - Test session ID
   - `timestamp` - When the event occurred
   - `event_type` - Type of event (KEYSTROKE, MOUSE_MOVE, FULLSCREEN_EXIT, FOCUS_LOST)
   - `event_data` - JSON data with event details

4. **To see new data:**
   - Click the **refresh icon** (circular arrow) in the toolbar
   - Or press `F5` to refresh
   - New rows will appear at the bottom (sorted by timestamp)

### Step 2: View Question Responses (Question Timing)
1. In MySQL Workbench Navigator:
   - Expand `exam_proctoring` → `Tables`
   - Right-click on `question_responses`
   - Select **"Select Rows - Limit 1000"**

2. You'll see:
   - `question_number` - Question index (1, 2, 3, etc.)
   - `question_type` - MCQ or coding
   - `answer` - User's answer
   - `time_taken_seconds` - Time spent on question
   - `first_viewed_at` - When question was first viewed
   - `last_updated_at` - Last update time

### Step 3: View Test Sessions
1. Right-click on `test_sessions` table
2. Select **"Select Rows - Limit 1000"**
3. See active/completed sessions

## Method 2: Using SQL Queries (More Control)

### View Recent Proctor Logs
```sql
USE exam_proctoring;

-- View all recent events (last 50)
SELECT * FROM proctor_logs 
ORDER BY timestamp DESC 
LIMIT 50;

-- View events for a specific user
SELECT * FROM proctor_logs 
WHERE user_id = 2  -- Replace with your user_id
ORDER BY timestamp DESC;

-- Count events by type
SELECT event_type, COUNT(*) as count 
FROM proctor_logs 
GROUP BY event_type;

-- View fullscreen exits
SELECT * FROM proctor_logs 
WHERE event_type = 'FULLSCREEN_EXIT'
ORDER BY timestamp DESC;

-- View tab switches
SELECT * FROM proctor_logs 
WHERE event_type = 'FOCUS_LOST'
ORDER BY timestamp DESC;
```

### View Question Responses
```sql
-- View all question responses
SELECT * FROM question_responses 
ORDER BY session_id, question_number;

-- View responses for a specific session
SELECT * FROM question_responses 
WHERE session_id = 'your_session_id_here'
ORDER BY question_number;

-- View time taken per question
SELECT 
    question_number,
    question_type,
    answer,
    time_taken_seconds,
    CONCAT(FLOOR(time_taken_seconds / 60), 'm ', time_taken_seconds % 60, 's') as time_formatted
FROM question_responses
WHERE session_id = 'your_session_id_here'
ORDER BY question_number;
```

### View Active Sessions
```sql
-- View all active test sessions
SELECT * FROM test_sessions 
WHERE status = 'active';

-- View all sessions with user info
SELECT 
    ts.session_id,
    u.username,
    ts.status,
    ts.started_at,
    ts.ended_at
FROM test_sessions ts
JOIN users u ON ts.user_id = u.id
ORDER BY ts.started_at DESC;
```

## Method 3: Real-time Monitoring (Auto-refresh)

### Option A: Use MySQL Workbench Auto-refresh
1. Open a query tab
2. Run: `SELECT * FROM proctor_logs ORDER BY timestamp DESC LIMIT 20;`
3. Right-click on the result grid
4. Select **"Refresh"** periodically (or set up auto-refresh if available)

### Option B: Create a Monitoring Query
```sql
-- Run this query to see latest activity
SELECT 
    pl.id,
    u.username,
    pl.event_type,
    pl.timestamp,
    JSON_EXTRACT(pl.event_data, '$.count') as event_count
FROM proctor_logs pl
JOIN users u ON pl.user_id = u.id
ORDER BY pl.timestamp DESC
LIMIT 20;
```

## Method 4: Check Data in Admin Dashboard

The admin dashboard also shows data from MySQL:
1. Go to http://localhost:8000/admin
2. Select a user
3. Select a session
4. You'll see:
   - **Event Log** - Shows all proctor_logs events
   - **Question Timing Data** - Shows question_responses data
   - **Activity Timeline** - Visual chart of activity

## Quick Verification Steps

1. **Start a test** as a user
2. **Move your mouse** - Should see MOUSE_MOVE events
3. **Type something** - Should see KEYSTROKE events
4. **Switch tabs** - Should see FOCUS_LOST events
5. **Exit fullscreen** - Should see FULLSCREEN_EXIT events
6. **Answer questions** - Should see question_responses entries

## Troubleshooting

### If you don't see data:
1. **Check if the app is running** - Events are sent every 3 seconds
2. **Check browser console** - Look for errors in F12 Developer Tools
3. **Verify database connection** - Run `python test_connection.py`
4. **Check user_id** - Make sure you're logged in as a user (not admin)
5. **Wait a few seconds** - Data is batched and sent every 3 seconds

### Common Issues:
- **No data appearing**: Make sure you've started a test session (clicked "Start Test")
- **Old data only**: Click refresh in MySQL Workbench (F5)
- **Connection errors**: Check your `.env` file has correct MySQL credentials

## Expected Data Flow

1. User starts test → `test_sessions` table gets a new row
2. User moves mouse → `proctor_logs` gets MOUSE_MOVE events (batched every 3 seconds)
3. User types → `proctor_logs` gets KEYSTROKE events
4. User views question → `question_responses` gets a row with `first_viewed_at`
5. User answers question → `question_responses` row is updated with answer and `time_taken_seconds`
6. User switches tab → `proctor_logs` gets FOCUS_LOST event
7. User exits fullscreen → `proctor_logs` gets FULLSCREEN_EXIT event

All data is committed to MySQL in real-time!

