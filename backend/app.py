from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- MODELS ---------------- #

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    role = db.Column(db.String(50))  # admin / member


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    username = db.Column(db.String(100))
    project_id = db.Column(db.Integer)
    deadline = db.Column(db.String(50))
    status = db.Column(db.String(50), default="pending")


# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    return render_template("dashboard.html")


# CREATE PROJECT
@app.route("/create_project", methods=["POST"])
def create_project():
    data = request.json

    project = Project(name=data["name"])
    db.session.add(project)
    db.session.commit()

    return jsonify({"message": "Project created"})


# ADD MEMBER (FIXED 🔥)
@app.route("/add_member", methods=["POST"])
def add_member():
    data = request.json

    username = data.get("username")
    project_name = data.get("project_id")

    user = User.query.filter_by(username=username).first()
    project = Project.query.filter_by(name=project_name).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    if not project:
        return jsonify({"message": "Project not found"}), 404

    return jsonify({"message": "Member added successfully"})


# CREATE TASK (FIXED 🔥)
@app.route("/create_task", methods=["POST"])
def create_task():
    data = request.json

    title = data.get("title")
    username = data.get("username")
    project_name = data.get("project_id")
    deadline = data.get("deadline")

    user = User.query.filter_by(username=username).first()
    project = Project.query.filter_by(name=project_name).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    if not project:
        return jsonify({"message": "Project not found"}), 404

    task = Task(
        title=title,
        username=username,
        project_id=project.id,
        deadline=deadline
    )

    db.session.add(task)
    db.session.commit()

    return jsonify({"message": "Task created"})


# GET TASKS (FOR DISPLAY)
@app.route("/tasks")
def get_tasks():
    tasks = Task.query.all()

    data = []
    for t in tasks:
        data.append({
            "title": t.title,
            "username": t.username,
            "deadline": t.deadline,
            "status": t.status
        })

    return jsonify(data)


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # default admin user (only once)
        if not User.query.filter_by(username="admin").first():
            db.session.add(User(username="admin", role="admin"))
            db.session.add(User(username="user1", role="member"))
            db.session.add(User(username="kishan", role="member"))
            db.session.commit()

    app.run(debug=True)