import sqlite3
from flask import redirect, render_template, session, flash
from functools import wraps

conn = sqlite3.connect("exams.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
db = conn.cursor()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        db.execute("SELECT role FROM users WHERE id = ?", (session.get("user_id"),))
        who = db.fetchone()
        if not who:
            return redirect("/login")
        if who["role"].lower() == "student":
            return redirect("/index")
        return f(*args, **kwargs)
    return decorated_function

def not_teacher(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        db.execute("SELECT role FROM users WHERE id = ?", (session.get("user_id"),))
        who = db.fetchone()
        if not who:
            return redirect("/login")
        if who["role"].lower() == "teacher":
            flash("This page is for students only", "warning")
            return redirect("/index")
        return f(*args, **kwargs)
    return decorated_function
