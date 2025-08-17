import sqlite3
import os
from flask import g, redirect, session, flash
from functools import wraps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "exams.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# --- Decorators ---
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
        db = get_db()
        who = db.execute(
            "SELECT role FROM users WHERE id = ?",
            (session.get("user_id"),)
        ).fetchone()
        if not who:
            return redirect("/login")
        if who["role"].lower() == "student":
            return redirect("/index")
        return f(*args, **kwargs)
    return decorated_function


def not_teacher(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        db = get_db()
        who = db.execute(
            "SELECT role FROM users WHERE id = ?",
            (session.get("user_id"),)
        ).fetchone()
        if not who:
            return redirect("/login")
        if who["role"].lower() == "teacher":
            flash("This page is for students only", "warning")
            return redirect("/index")
        return f(*args, **kwargs)
    return decorated_function
