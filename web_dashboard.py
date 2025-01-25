from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

# Set up Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flashing messages

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(BASE_DIR, 'data/twitch_bot.db')

# Helper function to query the database
def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# Routes
@app.route("/")
def index():
    users = query_db("SELECT username, points FROM users ORDER BY points DESC")
    commands = query_db("SELECT command, response FROM commands")
    return render_template("index.html", users=users, commands=commands)

@app.route("/edit_user/<username>", methods=["GET", "POST"])
def edit_user(username):
    if request.method == "POST":
        new_points = request.form.get("points")
        if new_points and new_points.isdigit():
            query_db("UPDATE users SET points = ? WHERE username = ?", (int(new_points), username))
            flash(f"Updated {username}'s points to {new_points}.", "success")
        else:
            flash("Invalid points value. Please enter a number.", "error")
        return redirect(url_for("index"))

    user = query_db("SELECT username, points FROM users WHERE username = ?", [username], one=True)
    if user:
        return render_template("edit_user.html", user=user)
    flash("User not found.", "error")
    return redirect(url_for("index"))

@app.route("/edit_command/<command>", methods=["GET", "POST"])
def edit_command(command):
    if request.method == "POST":
        new_response = request.form.get("response")
        if new_response:
            query_db("UPDATE commands SET response = ? WHERE command = ?", (new_response, command))
            flash(f"Updated command '{command}' response.", "success")
        else:
            flash("Response cannot be empty.", "error")
        return redirect(url_for("index"))

    command_data = query_db("SELECT command, response FROM commands WHERE command = ?", [command], one=True)
    if command_data:
        return render_template("edit_command.html", command_data=command_data)
    flash("Command not found.", "error")
    return redirect(url_for("index"))

@app.route("/add_command", methods=["GET", "POST"])
def add_command():
    if request.method == "POST":
        command = request.form.get("command")
        response = request.form.get("response")
        if command and response:
            # Check if the command already exists
            existing_command = query_db("SELECT command FROM commands WHERE command = ?", [command], one=True)
            if existing_command:
                flash(f"Command '{command}' already exists.", "error")
            else:
                query_db("INSERT INTO commands (command, response) VALUES (?, ?)", (command, response))
                flash(f"Added new command '{command}'.", "success")
            return redirect(url_for("index"))
        else:
            flash("Both command and response are required.", "error")
    return render_template("add_command.html")

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)