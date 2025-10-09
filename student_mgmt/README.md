# Student Attendance & Marks Management (Flask + SQLite)

A minimal web app to manage students, subjects, attendance and marks with a simple UI and SQLite database.

## Features
- Manage students (add/edit/delete)
- Manage subjects (add/edit/delete)
- Record daily attendance per subject
- Enter marks per subject and exam; simple average report

## Tech
- Flask 3, SQLite, Jinja2, vanilla CSS

## Setup

1. Create a virtual environment and install deps:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Initialize the database (creates `app.db` with sample data):
```bash
python init_db.py
```

3. Run the app:
```bash
python app.py
```

Then open `http://localhost:5000` in your browser.

## Project Structure
```
student_mgmt/
  app.py
  init_db.py
  schema.sql
  requirements.txt
  templates/
    base.html
    index.html
    student_form.html
    subjects.html
    subject_form.html
    attendance.html
    marks.html
  static/
    styles.css
```
