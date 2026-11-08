
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify, session
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from werkzeug.security import generate_password_hash, check_password_hash


# ============================================================
# CONFIGURATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = "minimal-dev-secret-change-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///minimal.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ============================================================
# ROLES
# ============================================================

ROLES = ("member", "moderator", "admin")

ROLE_LABELS = {
    "member": "Участник",
    "moderator": "Модератор",
    "admin": "Администратор",
}


# ============================================================
# USER MODEL
# ============================================================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    activities = db.relationship(
        "Activity",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "role_label": ROLE_LABELS.get(self.role, self.role),
            "created_at": self.created_at.isoformat() + "Z",
        }

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_moderator(self):
        return self.role in ("moderator", "admin")


# ============================================================
# ACTIVITY MODEL
# ============================================================

class Activity(db.Model):
    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    text = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "text": self.text,
            "date": self.created_at.isoformat() + "Z",
        }


# ============================================================
# CTF MODELS
# ============================================================

class CTFChallenge(db.Model):
    __tablename__ = "ctf_challenges"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)

    difficulty = db.Column(
        db.String(30),
        nullable=False,
        default="Средняя"
    )

    max_points = db.Column(
        db.Integer,
        nullable=False,
        default=100
    )

    is_published = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self, submission=None):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty,
            "max_points": self.max_points,
            "is_published": self.is_published,
            "created_at": self.created_at.isoformat() + "Z",
            "submission": (
                submission.to_dict()
                if submission else None
            )
        }


class CTFSubmission(db.Model):
    __tablename__ = "ctf_submissions"

    id = db.Column(db.Integer, primary_key=True)

    challenge_id = db.Column(
        db.Integer,
        db.ForeignKey("ctf_challenges.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="in_progress"
    )

    score = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    feedback = db.Column(db.Text, nullable=True)

    reviewed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "challenge_id",
            "user_id",
            name="unique_user_challenge"
        ),
    )

    def to_dict(self):
        user = db.session.get(User, self.user_id)

        return {
            "id": self.id,
            "challenge_id": self.challenge_id,
            "user_id": self.user_id,
            "username": user.name if user else "Неизвестный",
            "status": self.status,
            "score": self.score,
            "feedback": self.feedback,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
        }


class CTFMessage(db.Model):
    __tablename__ = "ctf_messages"

    id = db.Column(db.Integer, primary_key=True)

    submission_id = db.Column(
        db.Integer,
        db.ForeignKey("ctf_submissions.id"),
        nullable=False,
        index=True
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    text = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        sender = db.session.get(User, self.sender_id)

        return {
            "id": self.id,
            "submission_id": self.submission_id,
            "sender_id": self.sender_id,
            "sender_name": sender.name if sender else "Неизвестный",
            "text": self.text,
            "created_at": self.created_at.isoformat() + "Z",
        }


# ============================================================
# AUTH HELPERS
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = current_user()

        if not user:
            return jsonify({
                "error": "Требуется авторизация"
            }), 401

        return f(*args, **kwargs)

    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = current_user()

            if not user:
                return jsonify({
                    "error": "Требуется авторизация"
                }), 401

            if user.role not in roles:
                return jsonify({
                    "error": "Недостаточно прав"
                }), 403

            return f(*args, **kwargs)

        return decorated

    return decorator


def current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    return db.session.get(User, user_id)


def add_activity(user, text):
    activity = Activity(
        user_id=user.id,
        text=text
    )

    db.session.add(activity)
    db.session.commit()


# ============================================================
# CTF HELPERS
# ============================================================

def get_or_create_submission(challenge_id, user_id):
    submission = CTFSubmission.query.filter_by(
        challenge_id=challenge_id,
        user_id=user_id
    ).first()

    if not submission:
        submission = CTFSubmission(
            challenge_id=challenge_id,
            user_id=user_id
        )

        db.session.add(submission)
        db.session.commit()

    return submission


def get_submission_messages(submission_id):
    return CTFMessage.query.filter_by(
        submission_id=submission_id
    ).order_by(
        CTFMessage.created_at.asc()
    ).all()


def validate_message(data):
    text = data.get("text", "")

    if not isinstance(text, str):
        return None, "Сообщение должно быть текстом"

    text = text.strip()

    if not text:
        return None, "Сообщение не может быть пустым"

    if len(text) > 20000:
        return None, "Сообщение слишком длинное"

    return text, None


# ============================================================
# MAIN PAGE
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


# ============================================================
# AUTH API
# ============================================================

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if len(name) < 2:
        return jsonify({"error": "Имя слишком короткое"}), 400

    if not email or "@" not in email:
        return jsonify({"error": "Некорректный email"}), 400

    if len(password) < 6:
        return jsonify({
            "error": "Пароль должен быть не менее 6 символов"
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({
            "error": "Этот email уже зарегистрирован"
        }), 409

    is_first = User.query.count() == 0
    role = "admin" if is_first else "member"

    user = User(
        name=name,
        email=email,
        role=role
    )

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    add_activity(user, "Регистрация аккаунта")

    if is_first:
        add_activity(
            user,
            "Назначена роль Администратор (первый пользователь)"
        )

    session["user_id"] = user.id
    session.permanent = True

    return jsonify({
        "user": user.to_dict()
    }), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({
            "error": "Неверный email или пароль"
        }), 401

    session["user_id"] = user.id
    session.permanent = True

    add_activity(user, "Вход в аккаунт")

    return jsonify({
        "user": user.to_dict()
    })


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({"ok": True})


@app.route("/api/me", methods=["GET"])
def me():
    user = current_user()

    if not user:
        return jsonify({"user": None})

    return jsonify({
        "user": user.to_dict()
    })


# ============================================================
# PROFILE API
# ============================================================

@app.route("/api/profile", methods=["PUT"])
@login_required
def update_profile():
    user = current_user()

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if len(name) < 2:
        return jsonify({
            "error": "Имя слишком короткое"
        }), 400

    if len(name) > 100:
        return jsonify({
            "error": "Имя слишком длинное"
        }), 400

    user.name = name
    db.session.commit()

    add_activity(user, "Обновление профиля")

    return jsonify({
        "user": user.to_dict()
    })


@app.route("/api/activities", methods=["GET"])
@login_required
def get_activities():
    user = current_user()

    items = (
        Activity.query
        .filter_by(user_id=user.id)
        .order_by(Activity.created_at.desc())
        .limit(10)
        .all()
    )

    return jsonify({
        "activities": [a.to_dict() for a in items]
    })


# ============================================================
# ADMIN: USERS AND ROLES
# ============================================================

@app.route("/api/users", methods=["GET"])
@role_required("admin", "moderator")
def list_users():
    users = User.query.order_by(
        User.created_at.desc()
    ).all()

    return jsonify({
        "users": [u.to_dict() for u in users]
    })


@app.route("/api/users/<int:user_id>/role", methods=["PUT"])
@role_required("admin")
def set_user_role(user_id):
    data = request.get_json(silent=True) or {}

    role = (data.get("role") or "").strip().lower()

    if role not in ROLES:
        return jsonify({
            "error": f"Допустимые роли: {', '.join(ROLES)}"
        }), 400

    target = db.session.get(User, user_id)

    if not target:
        return jsonify({
            "error": "Пользователь не найден"
        }), 404

    admin = current_user()

    if target.id == admin.id and role != "admin":
        return jsonify({
            "error": "Нельзя снять с себя роль администратора"
        }), 400

    old_role = target.role
    target.role = role

    db.session.commit()

    add_activity(
        admin,
        f"Сменил роль {target.email}: "
        f"{ROLE_LABELS.get(old_role, old_role)} → "
        f"{ROLE_LABELS.get(role, role)}"
    )

    add_activity(
        target,
        f"Роль изменена на «{ROLE_LABELS.get(role, role)}»"
    )

    return jsonify({
        "user": target.to_dict()
    })


# ============================================================
# CTF: CHALLENGE LIST
# ============================================================

@app.route("/api/ctf", methods=["GET"])
@login_required
def get_ctf_challenges():
    user = current_user()

    challenges = CTFChallenge.query.filter_by(
        is_published=True
    ).order_by(
        CTFChallenge.created_at.desc()
    ).all()

    result = []

    for challenge in challenges:
        submission = CTFSubmission.query.filter_by(
            challenge_id=challenge.id,
            user_id=user.id
        ).first()

        result.append(
            challenge.to_dict(submission)
        )

    return jsonify({
        "success": True,
        "challenges": result
    })

# ============================================================
# CTF: LEADERBOARD
# ============================================================

@app.route("/api/ctf/leaderboard", methods=["GET"])
@login_required
def get_ctf_leaderboard():
    rows = (
        db.session.query(
            User.id.label("user_id"),
            User.name.label("name"),
            db.func.sum(CTFSubmission.score).label("total_points"),
            db.func.count(CTFSubmission.id).label("completed")
        )
        .join(
            CTFSubmission,
            CTFSubmission.user_id == User.id
        )
        .filter(CTFSubmission.status == "graded")
        .group_by(User.id, User.name)
        .order_by(
            db.func.sum(CTFSubmission.score).desc(),
            User.name.asc()
        )
        .all()
    )

    leaderboard = []
    previous_points = None
    current_rank = 0

    for position, row in enumerate(rows, start=1):
        points = int(row.total_points or 0)

        if points != previous_points:
            current_rank = position
            previous_points = points

        leaderboard.append({
            "rank": current_rank,
            "user_id": row.user_id,
            "name": row.name,
            "points": points,
            "completed": row.completed
        })

    return jsonify({
        "success": True,
        "leaderboard": leaderboard
    })

# ============================================================
# CTF: CREATE CHALLENGE
# ============================================================

@app.route("/api/ctf", methods=["POST"])
@role_required("admin")
def create_ctf_challenge():
    user = current_user()
    data = request.get_json(silent=True) or {}

    title = data.get("title", "")
    description = data.get("description", "")
    difficulty = data.get("difficulty", "Средняя")

    if not isinstance(title, str) or not isinstance(description, str):
        return jsonify({
            "success": False,
            "error": "Название и описание должны быть текстом"
        }), 400

    title = title.strip()
    description = description.strip()

    if not title or not description:
        return jsonify({
            "success": False,
            "error": "Заполните название и описание"
        }), 400

    if len(title) > 150 or len(description) > 20000:
        return jsonify({
            "success": False,
            "error": "Превышена допустимая длина текста"
        }), 400

    allowed_difficulties = (
        "Лёгкая",
        "Средняя",
        "Сложная",
        "Экспертная"
    )

    if difficulty not in allowed_difficulties:
        return jsonify({
            "success": False,
            "error": "Некорректная сложность"
        }), 400

    try:
        max_points = int(data.get("max_points", 100))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "error": "Некорректное количество баллов"
        }), 400

    if not 1 <= max_points <= 100000:
        return jsonify({
            "success": False,
            "error": "Количество баллов должно быть от 1 до 100000"
        }), 400

    challenge = CTFChallenge(
        title=title,
        description=description,
        difficulty=difficulty,
        max_points=max_points,
        is_published=True,
        created_by=user.id
    )

    db.session.add(challenge)
    db.session.commit()

    add_activity(
        user,
        f"Опубликовано CTF-задание: {title}"
    )

    return jsonify({
        "success": True,
        "message": "CTF опубликован",
        "challenge": challenge.to_dict()
    }), 201


# ============================================================
# CTF: GET PERSONAL SUBMISSION AND CHAT
# ============================================================

@app.route(
    "/api/ctf/<int:challenge_id>/submission",
    methods=["GET"]
)
@login_required
def get_ctf_submission(challenge_id):
    user = current_user()

    challenge = db.session.get(
        CTFChallenge,
        challenge_id
    )

    if not challenge or not challenge.is_published:
        return jsonify({
            "success": False,
            "error": "CTF не найден"
        }), 404

    submission = get_or_create_submission(
        challenge_id,
        user.id
    )

    messages = get_submission_messages(
        submission.id
    )

    return jsonify({
        "success": True,
        "challenge": {
            "id": challenge.id,
            "title": challenge.title,
            "description": challenge.description,
            "difficulty": challenge.difficulty,
            "max_points": challenge.max_points
        },
        "submission": submission.to_dict(),
        "messages": [
            message.to_dict()
            for message in messages
        ]
    })


# ============================================================
# CTF: SEND MESSAGE / SUBMIT SOLUTION
# ============================================================

@app.route(
    "/api/ctf/<int:challenge_id>/messages",
    methods=["POST"]
)
@login_required
def send_ctf_message(challenge_id):
    user = current_user()
    data = request.get_json(silent=True) or {}

    challenge = db.session.get(
        CTFChallenge,
        challenge_id
    )

    if not challenge or not challenge.is_published:
        return jsonify({
            "success": False,
            "error": "CTF не найден"
        }), 404

    text, error = validate_message(data)

    if error:
        return jsonify({
            "success": False,
            "error": error
        }), 400

    submit = data.get("submit", False)

    if not isinstance(submit, bool):
        return jsonify({
            "success": False,
            "error": "Некорректный параметр submit"
        }), 400

    submission = get_or_create_submission(
        challenge_id,
        user.id
    )

    if submission.status == "graded":
        return jsonify({
            "success": False,
            "error": "Работа уже оценена"
        }), 400

    message = CTFMessage(
        submission_id=submission.id,
        sender_id=user.id,
        text=text
    )

    db.session.add(message)

    if submit:
        submission.status = "pending"

    db.session.commit()

    add_activity(
        user,
        f"Сообщение в CTF: {challenge.title}"
    )

    return jsonify({
        "success": True,
        "message": message.to_dict(),
        "submission": submission.to_dict()
    }), 201


# ============================================================
# CTF MOD: MODERATION QUEUE
# ============================================================

@app.route(
    "/api/mod/ctf/submissions",
    methods=["GET"]
)
@role_required("moderator", "admin")
def get_ctf_moderation_queue():
    status = request.args.get("status")

    allowed_statuses = (
        "in_progress",
        "pending",
        "graded"
    )

    query = CTFSubmission.query

    if status:
        if status not in allowed_statuses:
            return jsonify({
                "success": False,
                "error": "Некорректный статус"
            }), 400

        query = query.filter_by(status=status)

    submissions = query.order_by(
        CTFSubmission.updated_at.desc()
    ).all()

    result = []

    for submission in submissions:
        challenge = db.session.get(
            CTFChallenge,
            submission.challenge_id
        )

        item = submission.to_dict()

        item["challenge_title"] = (
            challenge.title
            if challenge
            else "Удалённое задание"
        )

        result.append(item)

    return jsonify({
        "success": True,
        "submissions": result
    })


# ============================================================
# CTF MOD: GET SUBMISSION DETAILS AND CHAT
# ============================================================

@app.route(
    "/api/mod/ctf/submissions/<int:submission_id>",
    methods=["GET"]
)
@role_required("moderator", "admin")
def get_ctf_submission_for_moderator(submission_id):
    submission = db.session.get(
        CTFSubmission,
        submission_id
    )

    if not submission:
        return jsonify({
            "success": False,
            "error": "Работа не найдена"
        }), 404

    challenge = db.session.get(
        CTFChallenge,
        submission.challenge_id
    )

    messages = get_submission_messages(
        submission.id
    )

    return jsonify({
        "success": True,
        "submission": submission.to_dict(),
        "challenge": (
            {
                "id": challenge.id,
                "title": challenge.title,
                "description": challenge.description,
                "difficulty": challenge.difficulty,
                "max_points": challenge.max_points
            }
            if challenge else None
        ),
        "messages": [
            message.to_dict()
            for message in messages
        ]
    })


# ============================================================
# CTF MOD: SEND MODERATOR MESSAGE
# ============================================================

@app.route(
    "/api/mod/ctf/submissions/<int:submission_id>/messages",
    methods=["POST"]
)
@role_required("moderator", "admin")
def send_ctf_moderator_message(submission_id):
    user = current_user()

    submission = db.session.get(
        CTFSubmission,
        submission_id
    )

    if not submission:
        return jsonify({
            "success": False,
            "error": "Работа не найдена"
        }), 404

    data = request.get_json(silent=True) or {}

    text, error = validate_message(data)

    if error:
        return jsonify({
            "success": False,
            "error": error
        }), 400

    message = CTFMessage(
        submission_id=submission.id,
        sender_id=user.id,
        text=text
    )

    db.session.add(message)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": message.to_dict()
    }), 201


# ============================================================
# CTF MOD: GRADE SUBMISSION
# ============================================================

@app.route(
    "/api/mod/ctf/submissions/<int:submission_id>/grade",
    methods=["POST"]
)
@role_required("moderator", "admin")
def grade_ctf_submission(submission_id):
    user = current_user()

    submission = db.session.get(
        CTFSubmission,
        submission_id
    )

    if not submission:
        return jsonify({
            "success": False,
            "error": "Работа не найдена"
        }), 404

    challenge = db.session.get(
        CTFChallenge,
        submission.challenge_id
    )

    if not challenge:
        return jsonify({
            "success": False,
            "error": "Задание не найдено"
        }), 404

    data = request.get_json(silent=True) or {}

    try:
        score = int(data.get("score"))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "error": "Некорректное количество баллов"
        }), 400

    feedback = data.get("feedback", "")

    if not isinstance(feedback, str):
        return jsonify({
            "success": False,
            "error": "Комментарий должен быть текстом"
        }), 400

    feedback = feedback.strip()

    if not 0 <= score <= challenge.max_points:
        return jsonify({
            "success": False,
            "error": (
                f"Баллы должны быть от 0 до {challenge.max_points}"
            )
        }), 400

    if len(feedback) > 10000:
        return jsonify({
            "success": False,
            "error": "Комментарий слишком длинный"
        }), 400

    submission.score = score
    submission.feedback = feedback
    submission.reviewed_by = user.id
    submission.status = "graded"

    db.session.commit()

    add_activity(
        user,
        f"Проверена работа пользователя ID {submission.user_id}"
    )

    return jsonify({
        "success": True,
        "message": "Работа проверена",
        "submission": submission.to_dict()
    })


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

with app.app_context():
    db.create_all()

    from sqlalchemy import text, inspect

    inspector = inspect(db.engine)

    cols = [
        column["name"]
        for column in inspector.get_columns("users")
    ]

    if "role" not in cols:
        with db.engine.connect() as conn:
            conn.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN role VARCHAR(20) DEFAULT 'member'"
                )
            )
            conn.commit()

        first = User.query.order_by(User.id).first()

        if first:
            first.role = "admin"
            db.session.commit()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5001
    )
