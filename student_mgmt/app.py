from __future__ import annotations

import sqlite3
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from flask import Flask, g, redirect, render_template, request, url_for, flash

BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / "app.db"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(SECRET_KEY="dev-secret-key", DATABASE=str(DATABASE_PATH))

    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON;")
        return g.db

    @app.teardown_appcontext
    def close_db(_exc: Optional[BaseException]) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def query(sql: str, params: Iterable = ()):  # simple helper
        return get_db().execute(sql, params)

    @app.route("/")
    def index():
        cur = query(
            """
            SELECT s.id, s.roll_no, s.name, s.email,
                   COUNT(CASE WHEN a.status='Present' THEN 1 END) as presents,
                   COUNT(a.id) as total_attendance
            FROM students s
            LEFT JOIN attendance a ON a.student_id = s.id
            GROUP BY s.id
            ORDER BY s.roll_no
            """
        )
        students = cur.fetchall()
        return render_template("index.html", students=students)

    # Students CRUD
    @app.route("/students/new", methods=["GET", "POST"])
    def student_new():
        if request.method == "POST":
            roll_no = request.form.get("roll_no", "").strip()
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            if not roll_no or not name:
                flash("Roll No and Name are required", "error")
            else:
                try:
                    query(
                        "INSERT INTO students (roll_no, name, email) VALUES (?, ?, ?)",
                        (roll_no, name, email or None),
                    )
                    get_db().commit()
                    flash("Student added", "success")
                    return redirect(url_for("index"))
                except sqlite3.IntegrityError:
                    flash("Roll number already exists", "error")
        return render_template("student_form.html", student=None)

    @app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
    def student_edit(student_id: int):
        student = query("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
        if not student:
            flash("Student not found", "error")
            return redirect(url_for("index"))
        if request.method == "POST":
            roll_no = request.form.get("roll_no", "").strip()
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            if not roll_no or not name:
                flash("Roll No and Name are required", "error")
            else:
                try:
                    query(
                        "UPDATE students SET roll_no=?, name=?, email=? WHERE id=?",
                        (roll_no, name, email or None, student_id),
                    )
                    get_db().commit()
                    flash("Student updated", "success")
                    return redirect(url_for("index"))
                except sqlite3.IntegrityError:
                    flash("Roll number must be unique", "error")
        return render_template("student_form.html", student=student)

    @app.route("/students/<int:student_id>/delete", methods=["POST"])
    def student_delete(student_id: int):
        query("DELETE FROM students WHERE id=?", (student_id,))
        get_db().commit()
        flash("Student deleted", "success")
        return redirect(url_for("index"))

    # Subjects CRUD
    @app.route("/subjects")
    def subjects_list():
        subjects = query("SELECT * FROM subjects ORDER BY code").fetchall()
        return render_template("subjects.html", subjects=subjects)

    @app.route("/subjects/new", methods=["GET", "POST"])
    def subject_new():
        if request.method == "POST":
            code = request.form.get("code", "").strip()
            name = request.form.get("name", "").strip()
            if not code or not name:
                flash("Code and Name are required", "error")
            else:
                try:
                    query("INSERT INTO subjects (code, name) VALUES (?, ?)", (code, name))
                    get_db().commit()
                    flash("Subject added", "success")
                    return redirect(url_for("subjects_list"))
                except sqlite3.IntegrityError:
                    flash("Subject code must be unique", "error")
        return render_template("subject_form.html", subject=None)

    @app.route("/subjects/<int:subject_id>/edit", methods=["GET", "POST"])
    def subject_edit(subject_id: int):
        subject = query("SELECT * FROM subjects WHERE id=?", (subject_id,)).fetchone()
        if not subject:
            flash("Subject not found", "error")
            return redirect(url_for("subjects_list"))
        if request.method == "POST":
            code = request.form.get("code", "").strip()
            name = request.form.get("name", "").strip()
            if not code or not name:
                flash("Code and Name are required", "error")
            else:
                try:
                    query("UPDATE subjects SET code=?, name=? WHERE id=?", (code, name, subject_id))
                    get_db().commit()
                    flash("Subject updated", "success")
                    return redirect(url_for("subjects_list"))
                except sqlite3.IntegrityError:
                    flash("Subject code must be unique", "error")
        return render_template("subject_form.html", subject=subject)

    @app.route("/subjects/<int:subject_id>/delete", methods=["POST"])
    def subject_delete(subject_id: int):
        query("DELETE FROM subjects WHERE id=?", (subject_id,))
        get_db().commit()
        flash("Subject deleted", "success")
        return redirect(url_for("subjects_list"))

    # Attendance
    @app.route("/attendance", methods=["GET", "POST"])
    def attendance_page():
        db = get_db()
        subjects = query("SELECT * FROM subjects ORDER BY code").fetchall()
        students = query("SELECT * FROM students ORDER BY roll_no").fetchall()

        selected_subject_id = request.args.get("subject_id") or request.form.get("subject_id")
        selected_date = request.args.get("date") or request.form.get("date")

        if request.method == "POST" and selected_subject_id and selected_date:
            for student in students:
                status_value = request.form.get(f"status_{student['id']}") or "Absent"
                try:
                    db.execute(
                        """
                        INSERT INTO attendance (student_id, subject_id, date, status)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(student_id, subject_id, date)
                        DO UPDATE SET status=excluded.status
                        """,
                        (student["id"], int(selected_subject_id), selected_date, status_value),
                    )
                except Exception:
                    flash("Failed to save some records", "error")
            db.commit()
            flash("Attendance saved", "success")
            return redirect(url_for("attendance_page", subject_id=selected_subject_id, date=selected_date))

        records = []
        if selected_subject_id and selected_date:
            cur = query(
                """
                SELECT student_id, status FROM attendance
                WHERE subject_id=? AND date=?
                """,
                (int(selected_subject_id), selected_date),
            )
            records = {row["student_id"]: row["status"] for row in cur.fetchall()}

        return render_template(
            "attendance.html",
            subjects=subjects,
            students=students,
            selected_subject_id=selected_subject_id,
            selected_date=selected_date,
            records=records,
        )

    # Marks
    @app.route("/marks", methods=["GET", "POST"])
    def marks_page():
        db = get_db()
        subjects = query("SELECT * FROM subjects ORDER BY code").fetchall()
        students = query("SELECT * FROM students ORDER BY roll_no").fetchall()

        selected_subject_id = request.args.get("subject_id") or request.form.get("subject_id")
        selected_exam = request.args.get("exam") or request.form.get("exam")

        if request.method == "POST" and selected_subject_id and selected_exam:
            for student in students:
                marks_obtained = request.form.get(f"marks_{student['id']}")
                max_marks = request.form.get("max_marks")
                if not marks_obtained or not max_marks:
                    continue
                try:
                    db.execute(
                        """
                        INSERT INTO marks (student_id, subject_id, exam, marks_obtained, max_marks)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(student_id, subject_id, exam)
                        DO UPDATE SET marks_obtained=excluded.marks_obtained, max_marks=excluded.max_marks
                        """,
                        (student["id"], int(selected_subject_id), selected_exam, float(marks_obtained), float(max_marks)),
                    )
                except Exception:
                    flash("Failed to save some records", "error")
            db.commit()
            flash("Marks saved", "success")
            return redirect(url_for("marks_page", subject_id=selected_subject_id, exam=selected_exam))

        records = {}
        if selected_subject_id and selected_exam:
            cur = query(
                "SELECT student_id, marks_obtained, max_marks FROM marks WHERE subject_id=? AND exam=?",
                (int(selected_subject_id), selected_exam),
            )
            records = {row["student_id"]: (row["marks_obtained"], row["max_marks"]) for row in cur.fetchall()}

        # Simple report: average per subject/exam
        report = None
        if selected_subject_id and selected_exam:
            cur = query(
                "SELECT AVG(marks_obtained) as avg_marks, MAX(max_marks) as max_marks FROM marks WHERE subject_id=? AND exam=?",
                (int(selected_subject_id), selected_exam),
            )
            report = cur.fetchone()

        return render_template(
            "marks.html",
            subjects=subjects,
            students=students,
            selected_subject_id=selected_subject_id,
            selected_exam=selected_exam,
            records=records,
            report=report,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    if not DATABASE_PATH.exists():
        print("Initializing database...")
        import init_db  # local module

        init_db.main()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
