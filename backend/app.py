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

    user = User.query.get(data['user_id'])

    if user.role != "admin":
        return jsonify({"message": "Only admin can create project"}), 403

    project = Project(
        name=data['name'],
        created_by=user.id
    )

    db.session.add(project)
    db.session.commit()

    return jsonify({"message": "Project created"})


@app.route('/add_member', methods=['POST'])
def add_member():
    data = request.json

    admin = User.query.get(data['admin_id'])

    if admin.role != "admin":
        return jsonify({"message": "Only admin can add members"}), 403

    project = Project.query.get(data['project_id'])
    member = User.query.filter_by(username=data['username']).first()

    if not member:
        return jsonify({"message": "User not found"}), 404

    project.members.append(member)
    db.session.commit()

    return jsonify({"message": "Member added"})


# ================= TASK =================

@app.route('/create_task', methods=['POST'])
def create_task():
    data = request.json

    user = User.query.filter_by(username=data['username']).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    try:
        deadline = datetime.strptime(data['deadline'], "%Y-%m-%d")
    except:
        deadline = datetime.strptime(data['deadline'], "%m/%d/%Y")

    task = Task(
        title=data['title'],
        status="pending",
        assigned_to=user.id,
        project_id=data['project_id'],
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
        overdue = False

        if t.deadline and t.deadline < now and t.status != "completed":
            overdue = True

        result.append({
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "deadline": t.deadline.strftime("%Y-%m-%d"),
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


# ================= STATS =================

@app.route('/stats', methods=['GET'])
def stats():
    total = Task.query.count()
    completed = Task.query.filter_by(status="completed").count()
    pending = Task.query.filter_by(status="pending").count()

    now = datetime.now()

    overdue = Task.query.filter(
        Task.deadline < now,
        Task.status != "completed"
    ).count()

    return jsonify({
        "total": total,
        "completed": completed,
        "pending": pending,
        "overdue": overdue
    })


# ================= RUN =================

if __name__ == "__main__":
   if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)