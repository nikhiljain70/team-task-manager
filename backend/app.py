from flask import Flask, request, jsonify, render_template
from models import db, User, Project, Task
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taskmanager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
CORS(app)

with app.app_context():
    db.create_all()

# ================= FRONTEND =================

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/signup_page')
def signup_page():
    return render_template('signup.html')

@app.route('/dashboard_page')
def dashboard_page():
    return render_template('dashboard.html')


# ================= AUTH =================

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "User already exists"})

    user = User(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        role=data['role']
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Signup successful"})


@app.route('/login', methods=['POST'])
def login():
    data = request.json

    user = User.query.filter_by(
        email=data['email'],
        password=data['password']
    ).first()

    if user:
        return jsonify({
            "user_id": user.id,
            "role": user.role
        })

    return jsonify({"message": "Invalid credentials"}), 401


# ================= PROJECT =================

@app.route('/create_project', methods=['POST'])
def create_project():
    data = request.json

    project = Project(name=data.get('name'))

    # admin ko auto add karo
    user = User.query.get(data.get("user_id"))
    if user:
        project.members.append(user)

    db.session.add(project)
    db.session.commit()

    return jsonify({"message": "Project created"})


@app.route('/projects/<int:user_id>', methods=['GET'])
def get_projects(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify([])

    projects = user.projects

    result = []
    for p in projects:
        result.append({
            "id": p.id,
            "name": p.name
        })

    return jsonify(result)


# ================= ADD MEMBER =================

@app.route('/add_member', methods=['POST'])
def add_member():
    data = request.json

    username = data.get('username')
    project_name = data.get('project_name')

    user = User.query.filter_by(username=username).first()
    project = Project.query.filter_by(name=project_name).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    if not project:
        return jsonify({"message": "Project not found"}), 404

    project.members.append(user)
    db.session.commit()

    return jsonify({"message": "Member added"})


# ================= TASK =================

@app.route('/create_task', methods=['POST'])
def create_task():
    data = request.json

    user = User.query.filter_by(username=data.get('username')).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    try:
        deadline = datetime.strptime(data.get('deadline'), "%Y-%m-%d")
    except:
        deadline = datetime.strptime(data.get('deadline'), "%m/%d/%Y")

    task = Task(
        title=data.get('title'),
        status="pending",
        assigned_to=user.id,
        deadline=deadline
    )

    db.session.add(task)
    db.session.commit()

    return jsonify({"message": "Task created"})


@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    now = datetime.now()

    result = []

    for t in tasks:
        user = User.query.get(t.assigned_to)

        overdue = False
        if t.deadline and t.deadline < now and t.status != "completed":
            overdue = True

        result.append({
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "deadline": t.deadline.strftime("%Y-%m-%d"),
            "username": user.username if user else "unknown",
            "overdue": overdue
        })

    return jsonify(result)


@app.route('/update_task/<int:id>', methods=['PUT'])
def update_task(id):
    task = Task.query.get(id)

    if not task:
        return jsonify({"message": "Task not found"}), 404

    task.status = "completed"
    db.session.commit()

    return jsonify({"message": "Task updated"})