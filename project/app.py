import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, abort
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, teacher_required, not_teacher, get_db
import secrets
import uuid
from datetime import datetime
import os
import random

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "exams.db")


def query_db(query, args=(), one=False, commit=False):
    db = get_db()
    cur = db.execute(query, args)
    if commit:
        db.commit()
        return None
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv
# =================================


@app.route("/index")
@app.route("/")
@login_required
def index():
    color = f"rgb({random.randint(0,255)}, {random.randint(0,255)}, {random.randint(0,255)})"
    role = query_db("SELECT role FROM users WHERE id = ?", (session["user_id"],), one=True)
    name = query_db("SELECT username FROM users WHERE id = ?", (session["user_id"],), one=True)
    return render_template(
        "index.html",
        role="teacher" if role["role"].lower() == "teacher" else role["role"].lower(),
        username=name["username"],
        color=color
    )


@app.route("/new_ex", methods=["GET", "POST"])
@login_required
@teacher_required
def new_ex():
    if request.method == "POST":
        q_name = request.form.get("quez_name")
        time = request.form.get("time")
        token = str(uuid.uuid4())
        if not q_name:
            return render_template("new_ex.html", state="Enter Exam Name!")

        query_db(
            "INSERT INTO exams (name, created_by, time_limit, token) VALUES (?, ?, ?, ?)",
            (q_name, session["user_id"], float(time) if time else None, token),
            commit=True
        )
        exam_id = query_db("SELECT id FROM exams WHERE token = ?", (token,), one=True)
        return redirect(f"send_q/{exam_id['id']}")

    return render_template("new_ex.html")


@app.route("/statistics")
@login_required
@not_teacher
def statistics():
    exams = query_db("SELECT exam_id, score, ex_co FROM results WHERE student_id = ?", (session["user_id"],))
    if exams:
        labels, data = [], []
        score, total = 0, 0
        for row in exams:
            name = query_db("SELECT name FROM exams WHERE id = ?", (row["exam_id"],))
            labels.append(name[0]["name"])
            data.append(row["score"])
            if row["ex_co"]:
                total += row["ex_co"]
            score += row["score"]
        percentage = round((score / total * 100)) if total else 0
        return render_template("statistics.html", total=percentage, labels=labels, data=data)


@app.route("/send_q/link/<token>", methods=["POST", "GET"])
@login_required
@teacher_required
def link(token):
    if request.method == "GET":
        link = f"https://abdo1232.pythonanywhere.com/exam/take/{token}"
        return render_template("link.html", link=link, token=token)
    else:
        flash("All questions saved successfully!", "success")
        return redirect("/")


@app.route("/send_q/<id_u>", methods=["POST", "GET"])
@login_required
@teacher_required
def send_q(id_u):
    if request.method == "GET":
        return render_template("add_ques.html", exam_id=id_u, id=id_u)

    exam_id = id_u
    teacher_id = session["user_id"]
    questions = request.form.getlist("question_text[]")

    for i, q_text in enumerate(questions):
        choice_a = request.form.get(f"ans1_{i}")
        choice_b = request.form.get(f"ans2_{i}")
        choice_c = request.form.get(f"ans3_{i}")
        choice_d = request.form.get(f"ans4_{i}")
        correct_choice = request.form.get(f"q{i}")
        if not all([q_text, choice_a, choice_b, choice_c, choice_d, correct_choice]):
            return render_template("add_ques.html", state=f"Missing data in question {i+1}", exam_id=exam_id)

        query_db("""
            INSERT INTO questions
            (exam_id, teacher_id, text, choice_a, choice_b, choice_c, choice_d, correct_choice)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (exam_id, teacher_id, q_text, choice_a, choice_b, choice_c, choice_d, correct_choice), commit=True)

    token = query_db("SELECT token FROM exams WHERE id = ?", (exam_id,), one=True)
    return redirect(f"link/{token['token']}")


@app.route("/past", methods=["GET", "POST"])
@login_required
@teacher_required
def past():
    exam = query_db("SELECT * FROM exams WHERE created_by = ?", (session["user_id"],))
    return render_template("past.html", exam=exam)


@app.route("/my_exams", methods=["GET", "POST"])
@login_required
@not_teacher
def my_exams():
    results = query_db("SELECT * FROM results WHERE student_id = ?", (session["user_id"],))
    if not results:
        return render_template("my_past_exams_stu.html", my_past="You haven't taken any exams yet.")

    list_exams, correct, count, date = [], [], [], []
    for i in results:
        exams_name = query_db("SELECT name FROM exams WHERE id = ?", (i["exam_id"],), one=True)
        list_exams.append(exams_name["name"])
        correct.append(i["score"])
        date.append(i["date_taken"])
        ques_count = query_db("SELECT COUNT(text) as total FROM questions WHERE exam_id = ?", (i["exam_id"],), one=True)
        count.append(ques_count["total"])

    return render_template("my_past_exams_stu.html", exam=list_exams, ques_count=count, correct=correct, date=date)


@app.route("/exam/take/<token>", methods=["GET", "POST"])
@login_required
@not_teacher
def take_exam(token):
    if request.method == "GET":
        exam = query_db("SELECT * FROM exams WHERE token = ?", (token,), one=True)
        if not exam:
            abort(404)
        who_took = query_db("SELECT student_id FROM results WHERE exam_id = ?", (exam["id"],))
        if any(str(session["user_id"]) == str(row["student_id"]) for row in who_took):
            flash("YOU CANNOT !", "danger")
            return redirect("/")
        in_out = query_db("SELECT now FROM cheat WHERE exam_id = ?", (exam["id"],))
        if in_out and in_out[0]["now"] == "IN":
            return redirect(f"/submit/{token}")
        query_db("INSERT INTO cheat (student_id, exam_id, now) VALUES(?,?,?) ", (session["user_id"], exam["id"], "IN"), commit=True)
        questions = query_db("SELECT * FROM questions WHERE exam_id = ?", (exam["id"],))
        return render_template("take-exam.html", time=exam["time_limit"], name=exam["name"], questions=questions, count=0, token=token, role="stu")


@app.route("/exam/preview/<token>", methods=["GET", "POST"])
@login_required
@teacher_required
def preview_exam(token):
    exam = query_db("SELECT * FROM exams WHERE token = ?", (token,), one=True)
    if not exam:
        abort(404)
    questions = query_db("SELECT * FROM questions WHERE exam_id = ?", (exam["id"],))
    return render_template("take-exam.html", time=exam["time_limit"], name=exam["name"], questions=questions, count=0, token=token, role="teacher")


@app.route("/submit/<token>", methods=["POST", "GET"])
@login_required
@not_teacher
def get_student_ans(token):
    exam = query_db("SELECT * FROM exams WHERE token = ?", (token,), one=True)
    if not exam:
        abort(404)

    ids = query_db("SELECT * FROM questions WHERE exam_id = ?", (exam["id"],))
    correct = query_db("SELECT correct_choice FROM questions WHERE exam_id = ?", (exam["id"],))
    ques_count = query_db("SELECT COUNT(text) as total FROM questions WHERE exam_id = ?", (exam["id"],), one=True)["total"]

    ans, corr_ans_stu = {}, 0
    date_today = datetime.today().date()
    for idx, q in enumerate(ids):
        ans[f"q{q['id']}"] = request.form.get(f"q{q['id']}")
        if ans[f"q{q['id']}"] == correct[idx]["correct_choice"]:
            corr_ans_stu += 1

    query_db("INSERT INTO results (student_id, exam_id, score, date_taken, ex_co) VALUES(?, ?, ?, ?, ?)",
             (session["user_id"], exam["id"], corr_ans_stu, date_today, ques_count), commit=True)
    query_db("UPDATE cheat SET now = ? WHERE student_id = ? AND exam_id = ?", ("out", session["user_id"], exam["id"]), commit=True)
    flash(f"تم التسليم. الدرجة: {corr_ans_stu}/{ques_count}", "warning")
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username, password = request.form.get("username"), request.form.get("password")
        if not username:
            return render_template("login.html", state="Enter username!", return_usr_nam="")
        elif not password:
            return render_template("login.html", state="Enter password!", return_usr_nam=username)

        user = query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
        if not user:
            return render_template("login.html", state="invalid username ", return_usr_nam="")
        elif not check_password_hash(user["password"], password):
            return render_template("login.html", state="invalid password", return_usr_nam=username)

        session["user_id"] = user["id"]
        return redirect("/")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return render_template("login.html", success="Logged out successfully!")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user_name = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        co_pass = request.form.get("co_password")
        role = request.form.get("role")

        if not (user_name and co_pass and password and email and role):
            return render_template("register.html", state="Please complete all fields.")
        elif "@" not in email:
            return render_template("register.html", state="Please enter a valid email address.")
        elif co_pass != password:
            return render_template("register.html", state="The password does not match.")

        hashed_password = generate_password_hash(password)
        query_db("INSERT INTO users (username, email, password, role) VALUES(?, ?, ?, ?)",
                 (user_name, email, hashed_password, role), commit=True)
        return render_template("login.html", success="Registration Successful!")

    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)
