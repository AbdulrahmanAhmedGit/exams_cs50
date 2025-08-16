from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, abort
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, teacher_required, not_teacher
import random
import secrets
import uuid
from datetime import datetime
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db = SQL("sqlite:///exams.db")


@app.route("/index")
@app.route("/")
@login_required
def index():
    role = db.execute("SELECT role FROM users WHERE id = ?", session["user_id"])
    name = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
    role = role[0]["role"]
    if role.lower() =="teacher":
        return render_template("index.html", role="teacher", username=name[0]["username"])
    else:
        return render_template("index.html", role=role.lower(), username=name[0]["username"])

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

        exam_id= db.execute(
        "INSERT INTO exams (name, created_by, time_limit, token) VALUES (?, ?, ?, ?)",
        q_name, session["user_id"], float(time) if time else None, token
        )

        return redirect(url_for("send_q", exam_id=exam_id))

    return render_template("new_ex.html")


@app.route("/link", methods=["POST", "GET"])
@login_required
@teacher_required
def link():
    if request.method == "GET":
        exam_id = request.args.get("exam_id")
        token = db.execute("SELECT token FROM exams WHERE id = ?", exam_id)
        link = f"/exam/take/{token[0]["token"]}"
        return render_template("link.html", link=link)
    flash("All questions saved successfully!", "success")
    return redirect("/")

@app.route("/send_q", methods=["POST", "GET"])
@login_required
@teacher_required
def send_q():
    if request.method == "GET":
        exam_id = request.args.get("exam_id")
        return render_template("add_ques.html", exam_id=exam_id)

    exam_id = request.values.get("exam_id")
    teacher_id = session["user_id"]
    questions = request.form.getlist("question_text[]")
    print("Exam ID received:", exam_id)
    print("Questions received:", questions)
    for i, q_text in enumerate(questions):
        choice_a = request.form.get(f"ans1_{i}")
        choice_b = request.form.get(f"ans2_{i}")
        choice_c = request.form.get(f"ans3_{i}")
        choice_d = request.form.get(f"ans4_{i}")
        correct_choice = request.form.get(f"q{i}")
        if not all([q_text, choice_a, choice_b, choice_c, choice_d, correct_choice]):
            return render_template("add_ques.html", state=f"Missing data in question {i+1}", exam_id=exam_id)

        db.execute("""
            INSERT INTO questions
            (exam_id, teacher_id, text, choice_a, choice_b, choice_c, choice_d, correct_choice)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, exam_id, teacher_id, q_text, choice_a, choice_b, choice_c, choice_d, correct_choice)
    return redirect(url_for("link", exam_id=exam_id))

@app.route("/past", methods=["GET", "POST"])
@login_required
@teacher_required
def past():
    exam = db.execute("SELECT * FROM exams WHERE created_by = ?", session["user_id"])
    return render_template("past.html", exam = exam)

@app.route("/my_exams", methods=["GET", "POST"])
@login_required
@not_teacher
def my_exams():
    results = db.execute("SELECT * FROM results WHERE student_id = ?", session["user_id"])
    if not results:
        return render_template("my_past_exams_stu.html", my_past="You haven't taken any exams yet.")
    list_exams = []
    correct = []
    count = []
    date = []
    for i in results:
        exams_name = db.execute("SELECT name FROM exams WHERE id = ?", i["exam_id"])
        list_exams.append(exams_name[0]["name"])
        correct.append(i["score"])
        date.append(i["date_taken"])
        ques_count = db.execute("SELECT COUNT(text) FROM questions WHERE exam_id = ?", i["exam_id"])
        ques_count = int(ques_count[0]['COUNT(text)'])
        count.append(ques_count)

    return render_template("my_past_exams_stu.html",exam=list_exams[::], ques_count=count.copy(), correct=correct.copy(), date=date.copy())


@app.route("/exam/take/<token>", methods=["GET", "POST"])
@login_required
@not_teacher
def take_exam(token):
    exam = db.execute("SELECT * FROM exams WHERE token = ?", token)
    if not exam:
        abort(404)
    who_took = db.execute("SELECT student_id FROM results WHERE exam_id = ?", exam[0]["id"])
    if not who_took:
        pass
    elif any(str(session["user_id"]) == str(row["student_id"]) for row in who_took):
        flash("YOU CANNOT !", "danger")
        return redirect("/")
    questions = db.execute("SELECT * FROM questions WHERE exam_id = ?", exam[0]["id"])
    return render_template("take-exam.html", time=exam[0]['time_limit'], name= exam[0]['name'], questions=questions, count=0, token=token, role="stu")

@app.route("/exam/preview/<token>", methods=["GET", "POST"])
@login_required
@teacher_required
def preview_exam(token):
    exam = db.execute("SELECT * FROM exams WHERE token = ?", token)
    if not exam:
        abort(404)
    who_took = db.execute("SELECT student_id FROM results WHERE exam_id = ?", exam[0]["id"])
    questions = db.execute("SELECT * FROM questions WHERE exam_id = ?", exam[0]["id"])
    return render_template("take-exam.html", time=exam[0]['time_limit'], name= exam[0]['name'], questions=questions, count=0, token=token, role="teacher")

@app.route("/submit/<token>", methods=["POST"])
@login_required
@not_teacher
def get_student_ans(token):
    exam = db.execute("SELECT * FROM exams WHERE token = ?", token)
    if not exam: abort(404)
    questions = db.execute("SELECT id FROM questions WHERE exam_id = ?", exam[0]["id"])
    ids = db.execute("SELECT * FROM questions WHERE exam_id = ?", exam[0]["id"])
    correct = db.execute("SELECT correct_choice FROM questions WHERE exam_id = ?", exam[0]["id"])
    ques_count = db.execute("SELECT COUNT(text) FROM questions WHERE exam_id = ?", exam[0]["id"])
    ques_count = int(ques_count[0]['COUNT(text)'])
    ans = {}
    corr_ans_stu = 0
    date_today = datetime.today().date()
    for _ in range(ques_count):
        ans[f"q{ids[_]["id"]}"] = request.form.get(f"q{ids[_]["id"]}")
        if ans[f"q{ids[_]["id"]}"] == correct[0]["correct_choice"]:
            corr_ans_stu += 1
    db.execute("INSERT INTO results (student_id, exam_id, score, date_taken) VALUES(?, ?, ?, ?)", session["user_id"], exam[0]["id"], corr_ans_stu, date_today)
    flash(f"تم التسليم. الدرجة: {corr_ans_stu}/{ques_count}", "warning")
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            return render_template("login.html", state="Enter username!")
        elif not request.form.get("password"):
            return render_template("login.html", state="Enter password!")
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return render_template("login.html", state="invalid username and/or password")
        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/register", methods = ["GET", "POST"])
def register():

    if request.method == "POST":
        user_name = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        co_pass = request.form.get("co_password")
        role = request.form.get("role")
        if not (user_name and co_pass and password and email and role):
            return render_template("register.html", state = "Please complete all fields.")
        elif not ("@" in email):
            return render_template("register.html", state = "Please enter a valid email address.")
        elif not (co_pass == password):
            return render_template("register.html", state = "The password does not match.")
        else:
            hashed_password = generate_password_hash(password)
            db.execute("INSERT INTO users (username, email, password, role) VALUES(?, ?, ?, ?)", user_name, email, hashed_password, role)
            return render_template("login.html", success = True)
    else:
        return render_template("register.html")


