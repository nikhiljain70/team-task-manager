from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

# ================= MODELS =================

members = db.Table('members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    role = db.Column(db.String(20))

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    members = db.relationship('User', secondary=members, backref='projects')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    status = db.Column(db.String(20))
    deadline = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

# ================= ROUTES =================

@app.route('/')
def home():
    return render_template("login.html")

@app.route('/dashboard_page')
def dashboard():
    return render_template("dashboard.html")

# ================= AUTH =================

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json

    user = User(
        username=data.get('username'),
        role=data.get('role')
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User created", "user_id": user.id})

@app.route('/login', methods=['POST'])
def login():
    data = request.json

    user = User.query.filter_by(username=data.get('username')).first()

    if user:
        return jsonify({
            "message": "Login success",
            "user_id": user.id,
            "role": user.role
        })
    else:
        return jsonify({"message": "User not found"}), 404


# ================= CREATE PROJECT =================

@app.route('/create_project', methods=['POST'])
def create_project():
    data = request.json

    project = Project(name=data.get('name'))

    db.session.add(project)
    db.session.commit()

    return jsonify({"message": "Project created"})


# ================= ADD MEMBER =================

@app.route('/add_member', methods=['POST'])
def add_member():
    data = request.json
    print("ADD MEMBER DATA:", data)

    admin = User.query.get(data.get('admin_id'))

    if not admin or admin.role != "admin":
        return jsonify({"message": "Only admin can add members"}), 403

    project = Project.query.filter_by(name=data.get('project_id')).first()
    member = User.query.filter_by(username=data.get('username')).first()

    if not project:
        return jsonify({"message": "Project not found"}), 404

    if not member:
        return jsonify({"message": "User not found"}), 404

    project.members.append(member)
    db.session.commit()

    return jsonify({"message": "Member added successfully"})


# ================= CREATE TASK =================

@app.route('/create_task', methods=['POST'])
def create_task():
    data = request.json
    print("CREATE TASK DATA:", data)

    user = User.query.filter_by(username=data.get('username')).first()
    project = Project.query.filter_by(name=data.get('project_id')).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    if not project:
        return jsonify({"message": "Project not found"}), 404

    task = Task(
        title=data.get('title'),
        user_id=user.id,
        project_id=project.id,
        deadline=data.get('deadline'),
        status="pending"
    )

    db.session.add(task)
    db.session.commit()

    return jsonify({"message": "Task created successfully"})


# ================= RUN =================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)