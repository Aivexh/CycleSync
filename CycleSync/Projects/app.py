"""
CycleSync - Complete Period Tracking Web App
Flask application with login, period tracking, daily logs, and insights
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import json
import os
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Database configuration
DATABASE = 'cyclesync.db'


def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with correct schema"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create users table with correct schema
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        avg_cycle_length INTEGER DEFAULT 28
    )
    ''')

    # Create cycles table (period tracking)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cycles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        cycle_length INTEGER,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Create daily_logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        log_date DATE NOT NULL,
        mood TEXT,
        energy_level INTEGER,
        symptoms TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(user_id, log_date)
    )
    ''')

    # Create indexes for better performance
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_cycles_user_date ON cycles(user_id, start_date)')
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_logs_user_date ON daily_logs(user_id, log_date)')

    # Check if we need to add demo user
    cursor.execute('SELECT COUNT(*) as count FROM users')
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        # Add demo user
        cursor.execute('''
        INSERT INTO users (username, email, password)
        VALUES (?, ?, ?)
        ''', ('demo', 'demo@example.com', 'password123'))
        print("✅ Demo user created: username='demo', password='password123'")

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")


# Initialize database
init_db()

# ============ HELPER FUNCTIONS ============


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def calculate_cycle_day(user_id):
    """Calculate current cycle day based on most recent period"""
    conn = get_db_connection()
    latest_cycle = conn.execute('''
        SELECT * FROM cycles WHERE user_id = ? 
        ORDER BY start_date DESC LIMIT 1
    ''', (user_id,)).fetchone()
    conn.close()

    if not latest_cycle:
        return None

    start_date = datetime.strptime(latest_cycle['start_date'], '%Y-%m-%d')
    today = datetime.now().date()

    days_since_start = (today - start_date.date()).days
    return days_since_start + 1


def predict_next_period(user_id):
    """Predict next period start date"""
    conn = get_db_connection()

    # Get latest cycle
    latest_cycle = conn.execute('''
        SELECT * FROM cycles WHERE user_id = ? 
        ORDER BY start_date DESC LIMIT 1
    ''', (user_id,)).fetchone()

    if not latest_cycle:
        conn.close()
        return None

    # Get user's average cycle length
    user = conn.execute('SELECT * FROM users WHERE id = ?',
                        (user_id,)).fetchone()
    cycles = conn.execute('''
        SELECT cycle_length FROM cycles 
        WHERE user_id = ? AND cycle_length IS NOT NULL
    ''', (user_id,)).fetchall()

    conn.close()

    if cycles:
        avg_cycle = sum(c['cycle_length'] for c in cycles) / len(cycles)
    else:
        avg_cycle = user['avg_cycle_length'] if user else 28

    end_date = datetime.strptime(latest_cycle['end_date'], '%Y-%m-%d')
    next_period = end_date + timedelta(days=int(avg_cycle))

    days_until = (next_period.date() - datetime.now().date()).days

    return {
        'date': next_period.strftime('%Y-%m-%d'),
        'days_until': days_until
    }


def get_cycle_phase(cycle_day):
    """Determine cycle phase based on cycle day"""
    if not cycle_day:
        return None

    if cycle_day <= 5:
        return 'menstrual'
    elif cycle_day <= 14:
        return 'follicular'
    elif cycle_day <= 21:
        return 'ovulation'
    else:
        return 'luteal'


def get_phase_recommendations(phase):
    """Get recommendations based on cycle phase"""
    recommendations = {
        'menstrual': [
            {'type': 'Rest', 'text': 'Prioritize rest and gentle movement. Your body needs extra care.', 'icon': '🧘‍♀️'},
            {'type': 'Nutrition',
                'text': 'Eat iron-rich foods like spinach, lentils, and lean meat.', 'icon': '🥬'},
            {'type': 'Self-Care',
                'text': 'Take warm baths, practice mindfulness, and rest well.', 'icon': '🛁'},
            {'type': 'Exercise',
                'text': 'Light stretching, walking, or gentle yoga.', 'icon': '🚶‍♀️'}
        ],
        'follicular': [
            {'type': 'Energy', 'text': 'Your energy is rising! Great time for new projects.', 'icon': '⚡'},
            {'type': 'Exercise', 'text': 'Increase exercise intensity. Cardio and strength training work well.', 'icon': '🏃‍♀️'},
            {'type': 'Social', 'text': 'Schedule social activities and networking events.', 'icon': '👥'},
            {'type': 'Creativity',
                'text': 'Start creative projects and learn new skills.', 'icon': '🎨'}
        ],
        'ovulation': [
            {'type': 'Peak Energy',
                'text': "You're at your peak! Great for important meetings and presentations.", 'icon': '💪'},
            {'type': 'Social', 'text': "You're naturally more outgoing. Connect with others.", 'icon': '👥'},
            {'type': 'Exercise',
                'text': 'High-intensity workouts feel great. Push yourself!', 'icon': '⚡'},
            {'type': 'Communication',
                'text': 'Express yourself freely. Your communication skills are enhanced.', 'icon': '💬'}
        ],
        'luteal': [
            {'type': 'Wind Down',
                'text': 'Focus on completing tasks and wrapping up projects.', 'icon': '📝'},
            {'type': 'Self-Care',
                'text': 'Practice self-compassion. Listen to your body.', 'icon': '💕'},
            {'type': 'Nutrition',
                'text': 'Complex carbs and magnesium-rich foods help with mood.', 'icon': '🌰'},
            {'type': 'Exercise',
                'text': 'Gentle exercise like yoga, pilates, or walking.', 'icon': '🧘'}
        ]
    }

    return recommendations.get(phase, [])


def get_user_stats(user_id):
    """Get user statistics"""
    conn = get_db_connection()

    # Get total cycles
    cycles_count = conn.execute(
        'SELECT COUNT(*) as count FROM cycles WHERE user_id = ?',
        (user_id,)
    ).fetchone()['count']

    # Get total logs
    logs_count = conn.execute(
        'SELECT COUNT(*) as count FROM daily_logs WHERE user_id = ?',
        (user_id,)
    ).fetchone()['count']

    # Get streak (consecutive days with logs)
    today = datetime.now().date()
    streak = 0
    check_date = today

    while True:
        log = conn.execute(
            'SELECT log_date FROM daily_logs WHERE user_id = ? AND log_date = ?',
            (user_id, check_date.strftime('%Y-%m-%d'))
        ).fetchone()

        if log:
            streak += 1
            check_date = check_date - timedelta(days=1)
        else:
            break

    conn.close()

    return {
        'total_cycles': cycles_count,
        'total_logs': logs_count,
        'current_streak': streak
    }

# ============ ROUTES ============


@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('login.html')

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?',
            (username,)
        ).fetchone()
        conn.close()

        if user is None:
            flash('Invalid username or password', 'error')
            return render_template('login.html')

        # Check password
        if user['password'] != password:
            flash('Invalid username or password', 'error')
            return render_template('login.html')

        # Login successful
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['email'] = user['email']
        session.permanent = True

        flash(f'Welcome back, {username}! 🌸', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration page"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash('All fields are required!', 'error')
            return render_template('signup.html')

        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, password)
            )
            conn.commit()
            conn.close()

            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                flash('Username already exists!', 'error')
            elif 'email' in str(e):
                flash('Email already exists!', 'error')
            else:
                flash('An error occurred. Please try again.', 'error')
            return render_template('signup.html')

    return render_template('signup.html')


@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with cycle overview"""
    user_id = session['user_id']

    # Get user stats
    user_stats = get_user_stats(user_id)

    # Get recent cycles
    conn = get_db_connection()
    recent_cycles = conn.execute('''
        SELECT * FROM cycles WHERE user_id = ? 
        ORDER BY start_date DESC LIMIT 6
    ''', (user_id,)).fetchall()

    # Get recent logs
    recent_logs = conn.execute('''
        SELECT * FROM daily_logs WHERE user_id = ? 
        ORDER BY log_date DESC LIMIT 7
    ''', (user_id,)).fetchall()
    conn.close()

    # Calculate current cycle info
    cycle_day = calculate_cycle_day(user_id)
    next_period = predict_next_period(user_id)
    current_phase = get_cycle_phase(cycle_day)
    recommendations = get_phase_recommendations(current_phase)

    return render_template('dashboard.html',
                           username=session['username'],
                           user_stats=user_stats,
                           recent_cycles=recent_cycles,
                           recent_logs=recent_logs,
                           cycle_day=cycle_day,
                           next_period=next_period,
                           current_phase=current_phase,
                           recommendations=recommendations)


@app.route('/track-period', methods=['GET', 'POST'])
@login_required
def track_period():
    """Track period start and end dates"""
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        notes = request.form.get('notes', '')

        if not start_date or not end_date:
            flash('Please provide both start and end dates', 'error')
            return render_template('track.html')

        # Validate dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        if end < start:
            flash('End date cannot be before start date', 'error')
            return render_template('track.html')

        conn = get_db_connection()

        # Calculate cycle length from previous cycle
        previous_cycle = conn.execute('''
            SELECT start_date FROM cycles 
            WHERE user_id = ? AND start_date < ? 
            ORDER BY start_date DESC LIMIT 1
        ''', (session['user_id'], start_date)).fetchone()

        cycle_length = None
        if previous_cycle:
            prev_start = datetime.strptime(
                previous_cycle['start_date'], '%Y-%m-%d')
            cycle_length = (start - prev_start).days

        # Insert cycle
        conn.execute('''
            INSERT INTO cycles (user_id, start_date, end_date, cycle_length, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], start_date, end_date, cycle_length, notes))

        conn.commit()
        conn.close()

        flash('Period tracked successfully! 🌸', 'success')
        return redirect(url_for('dashboard'))

    return render_template('track.html')


@app.route('/daily-log', methods=['GET', 'POST'])
@login_required
def daily_log():
    """Log daily symptoms and mood"""
    if request.method == 'POST':
        log_date = request.form.get('log_date')
        mood = request.form.get('mood')
        energy_level = request.form.get('energy_level')
        symptoms = request.form.getlist('symptoms')
        notes = request.form.get('notes', '')

        if not log_date or not mood or not energy_level:
            flash('Please fill in all required fields', 'error')
            return render_template('log.html')

        # Convert symptoms to JSON
        symptoms_json = json.dumps(symptoms)

        conn = get_db_connection()

        # Insert or update log
        try:
            conn.execute('''
                INSERT INTO daily_logs (user_id, log_date, mood, energy_level, symptoms, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], log_date, mood, int(energy_level), symptoms_json, notes))
        except sqlite3.IntegrityError:
            conn.execute('''
                UPDATE daily_logs 
                SET mood = ?, energy_level = ?, symptoms = ?, notes = ?
                WHERE user_id = ? AND log_date = ?
            ''', (mood, int(energy_level), symptoms_json, notes, session['user_id'], log_date))

        conn.commit()
        conn.close()

        flash('Daily log saved! Thank you for tracking. 💕', 'success')
        return redirect(url_for('dashboard'))

    return render_template('log.html')


@app.route('/insights')
@login_required
def insights():
    """Detailed insights and analytics"""
    user_id = session['user_id']
    conn = get_db_connection()

    # Get all cycles
    cycles = conn.execute('''
        SELECT * FROM cycles WHERE user_id = ? 
        ORDER BY start_date DESC
    ''', (user_id,)).fetchall()

    # Get logs for last 90 days
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')

    logs = conn.execute('''
        SELECT * FROM daily_logs 
        WHERE user_id = ? AND log_date BETWEEN ? AND ?
        ORDER BY log_date
    ''', (user_id, start_date, end_date)).fetchall()

    # Calculate statistics
    cycle_lengths = [c['cycle_length'] for c in cycles if c['cycle_length']]
    period_lengths = []

    for cycle in cycles:
        start = datetime.strptime(cycle['start_date'], '%Y-%m-%d')
        end = datetime.strptime(cycle['end_date'], '%Y-%m-%d')
        period_lengths.append((end - start).days + 1)

    stats = {
        'total_cycles': len(cycles),
        'avg_cycle': round(sum(cycle_lengths) / len(cycle_lengths), 1) if cycle_lengths else None,
        'avg_period': round(sum(period_lengths) / len(period_lengths), 1) if period_lengths else None,
        'total_logs': len(logs)
    }

    # Analyze mood patterns
    mood_counts = {'happy': 0, 'neutral': 0,
                   'sad': 0, 'anxious': 0, 'irritable': 0}
    for log in logs:
        if log['mood'] in mood_counts:
            mood_counts[log['mood']] += 1

    total_moods = sum(mood_counts.values())
    mood_percentages = {k: round((v / total_moods) * 100, 1)
                        for k, v in mood_counts.items()} if total_moods > 0 else {}

    # Analyze symptoms
    symptom_counts = {}
    for log in logs:
        if log['symptoms']:
            try:
                symptoms = json.loads(log['symptoms'])
                for symptom in symptoms:
                    symptom_counts[symptom] = symptom_counts.get(
                        symptom, 0) + 1
            except:
                pass

    top_symptoms = sorted(symptom_counts.items(),
                          key=lambda x: x[1], reverse=True)[:5]

    conn.close()

    return render_template('insights.html',
                           username=session['username'],
                           stats=stats,
                           mood_percentages=mood_percentages,
                           top_symptoms=top_symptoms,
                           cycles=cycles)


if __name__ == '__main__':
    app.run(debug=True)
