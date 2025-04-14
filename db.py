import sqlite3
import pandas as pd
import yaml

COLUMN_LABELS = {
    "date": "Date",
    "exercise": "Exercise",
    "set_number": "Set",
    "weight": "Weight",
    "reps": "Reps",
    "duration": "Duration",
    "rest": "Rest",
    "note": "Note",
    "equipment": "Equipment",
    "measured_by": "Measured By",
    "muscle_groups": "Muscle Groups",
    "name": "Name",  # for equipment or muscle group listings
    "default_weight": "Default Weight",
    "track_weight": "Track Weight",
    "has_resistance_levels": "Has Resistance Levels"
}

def get_user_conn():
    return sqlite3.connect("user_log.db", check_same_thread=False)

def get_system_conn():
    return sqlite3.connect("system.db", check_same_thread=False)

user_conn = get_user_conn()
system_conn = get_system_conn()
user_c = user_conn.cursor()
system_c = system_conn.cursor()

def create_tables():
    user_c.execute('''
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        exercise TEXT,
        set_number INTEGER,
        weight REAL,
        reps INTEGER,
        duration INTEGER,
        rest INTEGER,
        note TEXT
    )
    ''')

    system_c.execute('''
    CREATE TABLE IF NOT EXISTS exercise_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise TEXT UNIQUE,
        equipment_id INTEGER,
        weight REAL,
        measured_by TEXT DEFAULT 'reps',
        FOREIGN KEY (equipment_id) REFERENCES equipment(id)
    )
    ''')

    system_c.execute('''
    CREATE TABLE IF NOT EXISTS muscle_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')

    system_c.execute('''
    CREATE TABLE IF NOT EXISTS exercise_muscle_map (
        exercise_id INTEGER NOT NULL,
        muscle_group_id INTEGER NOT NULL,
        FOREIGN KEY (exercise_id) REFERENCES exercise_catalog(id),
        FOREIGN KEY (muscle_group_id) REFERENCES muscle_groups(id),
        PRIMARY KEY (exercise_id, muscle_group_id)
    )
    ''')

    user_conn.commit()  # Commit user-related changes
    system_conn.commit()  # Commit system-related changes
    initialize_muscle_groups()
    initialize_equipment()
    initialize_default_catalog_if_empty()

def insert_exercise(date, exercise, set_number, total_weight, reps, duration, rest, note=""):
    user_c.execute('''
    INSERT INTO exercises (date, exercise, set_number, weight, reps, duration, rest, note)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (date, exercise, set_number, total_weight, reps, duration, rest, note))
    user_conn.commit()

def update_exercise_row(row):
    user_c.execute('''
        UPDATE exercises 
        SET date = ?, exercise = ?, set_number = ?, weight = ?, reps = ?, duration = ?, rest = ?, note = ?
        WHERE id = ?
    ''', (
        str(row["Date"]),
        str(row["Exercise"]),
        int(row["Set"]),
        None if pd.isna(row.get("Weight")) else float(row["Weight"]),
        None if pd.isna(row.get("Reps")) else int(row["Reps"]),
        None if pd.isna(row.get("Duration")) else int(row["Duration"]),
        None if pd.isna(row.get("Rest")) else int(row["Rest"]),
        str(row["Note"]),
        int(row["id"])
    ))
    user_conn.commit()

def delete_exercise_row(row_id):
    user_c.execute("DELETE FROM exercises WHERE id = ?", (row_id,))
    user_conn.commit()

def get_catalog_entry(exercise_name):
    query = '''
    SELECT ec.id, ec.exercise, eq.name AS equipment, ec.weight, ec.measured_by
    FROM exercise_catalog ec
    JOIN equipment eq ON ec.equipment_id = eq.id
    WHERE ec.exercise = ?
    '''
    return pd.read_sql_query(query, system_conn, params=(exercise_name,)).iloc[0]

def get_catalog_with_muscle_groups():
    query = """
    SELECT ec.id, ec.exercise, eq.name AS equipment, ec.weight, ec.measured_by,
           GROUP_CONCAT(mg.name, ', ') AS muscle_groups
    FROM exercise_catalog ec
    JOIN equipment eq ON ec.equipment_id = eq.id
    LEFT JOIN exercise_muscle_map em ON ec.id = em.exercise_id
    LEFT JOIN muscle_groups mg ON em.muscle_group_id = mg.id
    GROUP BY ec.id
    ORDER BY ec.exercise ASC
    """
    return pd.read_sql_query(query, system_conn)

def get_exercise_log():
    df = pd.read_sql_query("SELECT * FROM exercises", user_conn)
    if not df.empty:
        df.rename(columns=COLUMN_LABELS, inplace=True)
    return df

def initialize_default_catalog_if_empty():
    result = system_c.execute('SELECT COUNT(*) FROM exercise_catalog').fetchone()
    if result[0] == 0:
        with open("config/default_catalog.yaml", "r") as f:
            default_catalog = yaml.safe_load(f)
        eq_lookup = dict(system_c.execute("SELECT name, id FROM equipment").fetchall())
        mg_lookup = dict(system_c.execute("SELECT name, id FROM muscle_groups").fetchall())
        for entry in default_catalog:
            exercise = entry.get("exercise")
            equipment_name = entry.get("equipment")
            weight = entry.get("weight", 0.0)
            measured_by = entry.get("measured_by", "Reps")

            if not exercise or not equipment_name:
                continue  # Skip invalid entries

            eq_id = eq_lookup.get(equipment_name)
            if eq_id is None:
                continue  # Equipment not found

            system_c.execute(
                "INSERT INTO exercise_catalog (exercise, equipment_id, weight, measured_by) VALUES (?, ?, ?, ?)",
                (exercise, eq_id, weight, measured_by)
            )
            ex_id = system_c.execute("SELECT id FROM exercise_catalog WHERE exercise = ?", (exercise,)).fetchone()[0]

            for mg_name in entry.get("muscle_groups", []):
                mg_id = mg_lookup.get(mg_name)
                if mg_id is not None:
                    system_c.execute(
                        "INSERT OR IGNORE INTO exercise_muscle_map (exercise_id, muscle_group_id) VALUES (?, ?)",
                        (ex_id, mg_id)
                    )

            # Optional: If you reintroduce optional equipment later
            for opt_eq in entry.get("optional_equipment", []):
                opt_eq_id = eq_lookup.get(opt_eq)
                if opt_eq_id is not None:
                    system_c.execute(
                        "INSERT OR IGNORE INTO exercise_optional_equipment (exercise_id, equipment_id) VALUES (?, ?)",
                        (ex_id, opt_eq_id)
                    )

        system_conn.commit()

def initialize_muscle_groups():
    existing = system_c.execute('SELECT COUNT(*) FROM muscle_groups').fetchone()[0]
    if existing == 0:
        with open("config/muscle_groups.yaml", "r") as f:
            groups = yaml.safe_load(f)
        system_c.executemany('INSERT INTO muscle_groups (name) VALUES (?)', [(g,) for g in groups])
        system_conn.commit()

def initialize_equipment():
    system_c.execute('''
    CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        default_weight REAL DEFAULT 0,
        track_weight BOOLEAN DEFAULT 1,
        has_resistance_levels BOOLEAN DEFAULT 0
    )
    ''')
    existing = system_c.execute('SELECT COUNT(*) FROM equipment').fetchone()[0]
    if existing == 0:
        with open("config/equipment.yaml", "r") as f:
            equipment = yaml.safe_load(f)
        for item in equipment:
            if item["name"] != "Resistance Band":  # Skip Resistance Band
                system_c.execute('''
                INSERT INTO equipment (name, default_weight, track_weight, has_resistance_levels)
                VALUES (?, ?, ?, ?)
                ''', (item["name"], item["default_weight"], item["track_weight"], item["has_resistance_levels"]))
        system_conn.commit()

def get_muscle_groups():
    return pd.read_sql("SELECT * FROM muscle_groups", system_conn)

def get_tag_map():
    return pd.read_sql("""
        SELECT em.exercise_id, mg.name AS muscle
        FROM exercise_muscle_map em
        JOIN muscle_groups mg ON em.muscle_group_id = mg.id
    """, system_conn)