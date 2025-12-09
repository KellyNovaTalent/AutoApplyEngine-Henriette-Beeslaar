from flask import Flask, render_template, request, redirect, url_for, session
from apscheduler.schedulers.background import BackgroundScheduler
from database import init_db
from jobs import scheduled_job_search
from email_checker import scheduled_email_check

app = Flask(__name__)
app.secret_key = "your_secret_key_here"   # Replace with something secure


# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def index():
    if "logged_in" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    password = request.form.get("password")

    # Change this to your actual password
    if password == "yourpassword":
        session["logged_in"] = True
        return redirect(url_for("dashboard"))

    return render_template("login.html", error="Incorrect password")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if "logged_in" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html")


# -----------------------------
# STARTUP (DB + Scheduler)
# -----------------------------
def start_scheduler():
    scheduler = BackgroundScheduler()

    # email check job
    scheduler.add_job(
        func=scheduled_email_check,
        trigger="interval",
        minutes=30,
        id="email_check_job",
        replace_existing=True
    )

    # auto job search job
    scheduler.add_job(
        func=scheduled_job_search,
        trigger="interval",
        hours=3,
        id="auto_search_job",
        replace_existing=True
    )

    scheduler.start()
    print("Scheduler started.")


# -----------------------------
# MAIN ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    print("Initializing database…")
    init_db()     # <-- this creates the tables on Render

    print("Starting background jobs…")
    start_scheduler()

    print("Starting Flask app…")
    app.run(host="0.0.0.0", port=5000)
