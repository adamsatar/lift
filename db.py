import sqlite3
import pandas as pd

def get_connection():
    return sqlite3.connect("lift.db", check_same_thread=False)

conn = get_connection()
c = conn.cursor()

def create_tables():
    c.execute('''
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        exercise TEXT,
        set_number INTEGER,
        weight REAL,
        reps INTEGER,
        duration INTEGER,
        rest INTEGER,
        note TEXT,
        side TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS exercise_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise TEXT UNIQUE,
        equipment TEXT,
        weight REAL,
        sides TEXT DEFAULT 'Bilateral',
        measured_by TEXT DEFAULT 'reps'
    )
    ''')

    conn.commit()
    initialize_default_catalog_if_empty()

def insert_exercise(date, exercise, set_number, total_weight, reps, duration, rest, note="", side=None):
    c.execute('''
    INSERT INTO exercises (date, exercise, set_number, weight, reps, duration, rest, note, side)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (date, exercise, set_number, total_weight, reps, duration, rest, note, side))
    conn.commit()

def get_exercise_log():
    return pd.read_sql_query('''
        SELECT id, date AS Date, exercise AS Exercise, set_number AS "Set",
               side AS Side, weight AS Weight, reps AS Reps, duration AS Duration,
               rest AS Rest, note AS Note
        FROM exercises
        ORDER BY date DESC, set_number ASC
    ''', conn)

def update_exercise_row(row):
    c.execute('''
        UPDATE exercises 
        SET exercise = ?, set_number = ?, side = ?, weight = ?, reps = ?, duration = ?, rest = ?, note = ?
        WHERE id = ?
    ''', (row["Exercise"], int(row["Set"]), row["Side"], row["Weight"], row.get("Reps"), row.get("Duration"), row["Rest"], row["Note"], int(row["id"])))
    conn.commit()

def get_exercise_catalog():
    return pd.read_sql_query('SELECT * FROM exercise_catalog ORDER BY exercise ASC', conn)

def get_catalog_entry(exercise_name):
    return pd.read_sql_query('SELECT * FROM exercise_catalog WHERE exercise = ?', conn, params=(exercise_name,)).iloc[0]

def insert_catalog_entry(exercise, equipment, weight, sides="Bilateral", measured_by="Reps"):
    c.execute('''
    INSERT OR IGNORE INTO exercise_catalog (exercise, equipment, weight, sides, measured_by)
    VALUES (?, ?, ?, ?, ?)
    ''', (exercise, equipment, weight, sides, measured_by))
    conn.commit()

def update_catalog_entry(entry):
    c.execute('''
    UPDATE exercise_catalog
    SET exercise = ?, equipment = ?, weight = ?, sides = ?, measured_by = ?
    WHERE id = ?
    ''', (entry["exercise"], entry["equipment"], entry["weight"], entry["sides"], entry["measured_by"], entry["id"]))
    conn.commit()

def initialize_default_catalog_if_empty():
    result = c.execute('SELECT COUNT(*) FROM exercise_catalog').fetchone()
    if result[0] == 0:
        default_exercises = [
            ("Barbell Back Squat", "Barbell", 45.0, "Bilateral", "Reps"),
            ("Barbell Bench Press", "Barbell", 45.0, "Bilateral", "Reps"),
            ("Barbell Deadlift", "Barbell", 45.0, "Bilateral", "Reps"),
            ("Barbell Overhead Press", "Barbell", 45.0, "Bilateral", "Reps"),
            ("Barbell Row", "Barbell", 45.0, "Bilateral", "Reps"),
            ("Dumbbell Bulgarian Split Squat", "Dumbbell", 0.0, "Unilateral", "Reps"),
            ("Dumbbell Calf Raise", "Dumbbell", 0.0, "Bilateral", "Reps"),
            ("Dumbbell Farmer Carry", "Dumbbell", 0.0, "Bilateral", "Duration"),
            ("Dumbbell Hammer Curl", "Dumbbell", 0.0, "Unilateral", "Reps"),
            ("Dumbbell Incline Bench Press", "Dumbbell", 0.0, "Bilateral", "Reps"),
            ("Dumbbell Lateral Raise", "Dumbbell", 0.0, "Unilateral", "Reps"),
            ("Dumbbell One Arm Row", "Dumbbell", 0.0, "Unilateral", "Reps"),
            ("Dumbbell Reverse Lunge", "Dumbbell", 0.0, "Unilateral", "Reps"),
            ("Dumbbell Skull Crusher", "Dumbbell", 0.0, "Bilateral", "Reps"),
            ("Dumbbell Shrug", "Dumbbell", 0.0, "Bilateral", "Duration"),
            ("Dumbbell Side Bend", "Dumbbell", 0.0, "Bilateral", "Reps"),
            ("Glute Bridge", "Bodyweight", 0.0, "Bilateral", "Reps"),
            ("Plank", "Bodyweight", 0.0, "Bilateral", "Duration"),
            ("Pull Up", "Bodyweight", 0.0, "Bilateral", "Reps")
        ]
        for ex in default_exercises:
            insert_catalog_entry(*ex)