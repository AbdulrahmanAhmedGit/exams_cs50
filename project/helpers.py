import requests
from flask import redirect, render_template, session, flash
from functools import wraps
from cs50 import SQL

db = SQL("sqlite:///exams.db")

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
        who = db.execute("SELECT role FROM users WHERE id = ?", session.get("user_id"))
        who = who[0]["role"]
        if who.lower() == "student":
            return redirect("/index")
        return f(*args, **kwargs)

    return decorated_function

def not_teacher(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        who = db.execute("SELECT role FROM users WHERE id = ?", session.get("user_id"))
        who = who[0]["role"]
        if who.lower() == "teacher":
            flash("""This page is for students only""", "warning")
            return redirect("/index")
        return f(*args, **kwargs)

    return decorated_function
