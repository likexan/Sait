from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify, session
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "minimal-dev-secret-change-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///minimal.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Роли
ROLES = ("member", "moderator", "admin")
ROLE_LABELS = {
    "member": "Участник",
    "moderator": "Модератор",
    "admin": "Администратор",
}


# ─── Models ───────────────────────────────────────────────

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    activities = db.relationship(
        "Activity", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "role_label": ROLE_LABELS.get(self.role, self.role),
            "created_at": self.created_at.isoformat() + "Z",
        }

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_moderator(self) -> bool:
        return self.role in ("moderator", "admin")


class Activity(db.Model):
    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "date": self.created_at.isoformat() + "Z",
        }


# ─── Helpers ──────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Требуется авторизация"}), 401
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return jsonify({"error": "Требуется авторизация"}), 401
            user = User.query.get(session["user_id"])
            if not user or user.role not in roles:
                return jsonify({"error": "Недостаточно прав"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def current_user():
    if "user_id" not in session:
        return None
    return User.query.get(session["user_id"])


def add_activity(user: User, text: str) -> None:
    activity = Activity(user_id=user.id, text=text)
    db.session.add(activity)
    db.session.commit()


# ─── Pages ────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─── Auth API ─────────────────────────────────────────────

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
        return jsonify({"error": "Пароль должен быть не менее 6 символов"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Этот email уже зарегистрирован"}), 409

    # Первый пользователь становится admin
    is_first = User.query.count() == 0
    role = "admin" if is_first else "member"

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    add_activity(user, "Регистрация аккаунта")
    if is_first:
        add_activity(user, "Назначена роль Администратор (первый пользователь)")

    session["user_id"] = user.id
    session.permanent = True

    return jsonify({"user": user.to_dict()}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Неверный email или пароль"}), 401

    session["user_id"] = user.id
    session.permanent = True

    add_activity(user, "Вход в аккаунт")

    return jsonify({"user": user.to_dict()})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/me", methods=["GET"])
def me():
    user = current_user()
    if not user:
        return jsonify({"user": None})
    return jsonify({"user": user.to_dict()})


# ─── Profile API ──────────────────────────────────────────

@app.route("/api/profile", methods=["PUT"])
@login_required
def update_profile():
    user = current_user()
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if len(name) < 2:
        return jsonify({"error": "Имя слишком короткое"}), 400

    user.name = name
    db.session.commit()

    add_activity(user, "Обновление профиля")

    return jsonify({"user": user.to_dict()})


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
    return jsonify({"activities": [a.to_dict() for a in items]})


# ─── Admin: users & roles ─────────────────────────────────

@app.route("/api/users", methods=["GET"])
@role_required("admin", "moderator")
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({"users": [u.to_dict() for u in users]})


@app.route("/api/users/<int:user_id>/role", methods=["PUT"])
@role_required("admin")
def set_user_role(user_id):
    data = request.get_json(silent=True) or {}
    role = (data.get("role") or "").strip().lower()

    if role not in ROLES:
        return jsonify({"error": f"Допустимые роли: {', '.join(ROLES)}"}), 400

    target = User.query.get(user_id)
    if not target:
        return jsonify({"error": "Пользователь не найден"}), 404

    admin = current_user()
    if target.id == admin.id and role != "admin":
        return jsonify({"error": "Нельзя снять с себя роль администратора"}), 400

    old_role = target.role
    target.role = role
    db.session.commit()

    add_activity(
        admin,
        f"Сменил роль {target.email}: {ROLE_LABELS.get(old_role, old_role)} → {ROLE_LABELS.get(role, role)}"
    )
    add_activity(
        target,
        f"Роль изменена на «{ROLE_LABELS.get(role, role)}»"
    )

    return jsonify({"user": target.to_dict()})


# ─── Init DB ──────────────────────────────────────────────

with app.app_context():
    db.create_all()
    # Миграция: добавить колонку role, если её ещё нет (старая БД)
    from sqlalchemy import text, inspect
    inspector = inspect(db.engine)
    cols = [c["name"] for c in inspector.get_columns("users")]
    if "role" not in cols:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'member'"))
            conn.commit()
        first = User.query.order_by(User.id).first()
        if first:
            first.role = "admin"
            db.session.commit()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)