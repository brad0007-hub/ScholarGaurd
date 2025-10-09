import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name('app.db')
SCHEMA_PATH = Path(__file__).with_name('schema.sql')

SAMPLE_STUDENTS = [
    ("S001", "Alice Johnson", "alice@example.com"),
    ("S002", "Bob Smith", "bob@example.com"),
    ("S003", "Charlie Brown", "charlie@example.com"),
]

SAMPLE_SUBJECTS = [
    ("MATH101", "Mathematics I"),
    ("PHY101", "Physics I"),
    ("CS101", "Introduction to CS"),
]

SAMPLE_ATTENDANCE = [
    # (roll_no, subject_code, date, status)
    ("S001", "MATH101", "2025-01-10", "Present"),
    ("S002", "MATH101", "2025-01-10", "Absent"),
    ("S003", "MATH101", "2025-01-10", "Present"),
]

SAMPLE_MARKS = [
    # (roll_no, subject_code, exam, marks_obtained, max_marks)
    ("S001", "MATH101", "Midterm", 42, 50),
    ("S002", "MATH101", "Midterm", 35, 50),
    ("S003", "MATH101", "Midterm", 48, 50),
]


def run_script(cursor, path: Path) -> None:
    with path.open('r', encoding='utf-8') as f:
        cursor.executescript(f.read())


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('PRAGMA foreign_keys = ON;')
        cur = conn.cursor()
        run_script(cur, SCHEMA_PATH)

        cur.executemany(
            "INSERT INTO students (roll_no, name, email) VALUES (?, ?, ?)",
            SAMPLE_STUDENTS,
        )
        cur.executemany(
            "INSERT INTO subjects (code, name) VALUES (?, ?)",
            SAMPLE_SUBJECTS,
        )

        # Map roll_no and subject_code to ids
        cur.execute("SELECT id, roll_no FROM students")
        student_map = {roll: sid for sid, roll in cur.fetchall()}
        cur.execute("SELECT id, code FROM subjects")
        subject_map = {code: sid for sid, code in cur.fetchall()}

        # Insert attendance
        for roll_no, sub_code, date, status in SAMPLE_ATTENDANCE:
            cur.execute(
                """
                INSERT INTO attendance (student_id, subject_id, date, status)
                VALUES (?, ?, ?, ?)
                """,
                (student_map[roll_no], subject_map[sub_code], date, status),
            )

        # Insert marks
        for roll_no, sub_code, exam, marks_obtained, max_marks in SAMPLE_MARKS:
            cur.execute(
                """
                INSERT INTO marks (student_id, subject_id, exam, marks_obtained, max_marks)
                VALUES (?, ?, ?, ?, ?)
                """,
                (student_map[roll_no], subject_map[sub_code], exam, marks_obtained, max_marks),
            )

        conn.commit()


if __name__ == '__main__':
    main()
