import os
import uuid
import re
from datetime import datetime
from functools import wraps
from html import escape
from html.parser import HTMLParser

from flask import (
    Flask, render_template, request, jsonify, session
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, text, inspect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


# ============================================================
# CONFIGURATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "minimal-dev-secret-change-in-production"
)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///minimal.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

db = SQLAlchemy(app)

ARTICLE_UPLOAD_FOLDER = os.path.join(
    app.static_folder,
    "uploads",
    "articles"
)

AVATAR_UPLOAD_FOLDER = os.path.join(
    app.static_folder,
    "uploads",
    "avatars"
)

os.makedirs(AVATAR_UPLOAD_FOLDER, exist_ok=True)

os.makedirs(ARTICLE_UPLOAD_FOLDER, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {
    "png", "jpg", "jpeg", "webp", "gif"
}

ALLOWED_MEDIA_EXTENSIONS = {
    "png", "jpg", "jpeg", "webp", "gif",
    "mp4", "webm", "mp3", "wav", "ogg", "m4a"
}


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

    # Данные публичного профиля
    avatar = db.Column(db.String(500), nullable=True)
    bio = db.Column(db.String(500), nullable=False, default="")
    telegram = db.Column(db.String(32), nullable=True)

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
            "avatar": self.avatar,
            "bio": self.bio or "",
            "telegram": self.telegram,
            "points": get_user_points(self.id),
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
# AUDIT LOG MODEL
# ============================================================

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)

    actor_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    actor_name = db.Column(db.String(100), nullable=False)
    actor_email = db.Column(db.String(120), nullable=True)

    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.String(1000), nullable=False, default="")

    ip_address = db.Column(db.String(64), nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        index=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "actor_email": self.actor_email,
            "action": self.action,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() + "Z"
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
            "submission": submission.to_dict() if submission else None
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

def get_user_points(user_id):
    total = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(CTFSubmission.score),
                0
            )
        )
        .filter(
            CTFSubmission.user_id == user_id,
            CTFSubmission.status == "graded"
        )
        .scalar()
    )

    return int(total or 0)

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
# ARTICLES MODEL
# ============================================================

class Article(db.Model):
    __tablename__ = "articles"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    excerpt = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)

    preview = db.Column(db.String(500), nullable=True)
    author = db.Column(db.String(120), nullable=False)

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
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

    is_published = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    def to_dict(self):
        user = db.session.get(User, self.created_by)

        return {
            "id": self.id,
            "title": self.title,
            "excerpt": self.excerpt,
            "content": self.content,
            "preview": self.preview,
            "author": self.author,
            "created_by": self.created_by,
            "creator_name": user.name if user else "Неизвестный",
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
            "is_published": self.is_published
        }


# ============================================================
# ARTICLE HTML SANITIZER
# ============================================================

ARTICLE_TAGS = {
    "p", "br",
    "h2", "h3", "h4",
    "strong", "b",
    "em", "i",
    "u", "s",
    "code", "pre",
    "ol", "ul", "li",
    "blockquote",
    "small",
    "img",
    "video", "audio", "source"
}

VOID_TAGS = {"br", "img"}


class ArticleHTMLSanitizer(HTMLParser):

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.result = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in ARTICLE_TAGS:
            return

        attrs = dict(attrs)
        safe_attrs = []

        if tag == "img":
            src = attrs.get("src", "")

            if not src.startswith("/static/uploads/articles/"):
                return

            safe_attrs.append(("src", src))
            safe_attrs.append((
                "alt",
                attrs.get("alt", "")[:300]
            ))

        elif tag in ("video", "audio", "source"):
            src = attrs.get("src", "")

            if not src.startswith("/static/uploads/articles/"):
                return

            safe_attrs.append(("src", src))

            if tag in ("video", "audio"):
                safe_attrs.append(("controls", "controls"))

            if tag == "video":
                safe_attrs.append(("preload", "metadata"))

            if tag == "source":
                media_type = attrs.get("type", "")

                if media_type.startswith(("video/", "audio/")):
                    safe_attrs.append(("type", media_type))

        attr_text = "".join(
            f' {name}="{escape(value, quote=True)}"'
            for name, value in safe_attrs
        )

        self.result.append(f"<{tag}{attr_text}>")

        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag not in self.stack:
            return

        while self.stack:
            current = self.stack.pop()
            self.result.append(f"</{current}>")

            if current == tag:
                break

    def handle_data(self, data):
        self.result.append(escape(data))

    def get_html(self):
        while self.stack:
            self.result.append(f"</{self.stack.pop()}>")

        return "".join(self.result)


def sanitize_article_html(content):
    if not isinstance(content, str):
        return ""

    parser = ArticleHTMLSanitizer()
    parser.feed(content)
    return parser.get_html()


# ============================================================
# AUTH HELPERS
# ============================================================

def current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    return db.session.get(User, user_id)


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


def add_activity(user, text):
    activity = Activity(
        user_id=user.id,
        text=text
    )

    db.session.add(activity)
    db.session.commit()

# ============================================================
# AUDIT LOGGER
# ============================================================

@app.after_request
def write_audit_log(response):

    if (
        request.path.startswith("/api/")
        and request.method in ("POST", "PUT", "PATCH", "DELETE")
        and response.status_code < 400
    ):
        try:
            user_id = session.get("user_id")
            user = db.session.get(User, user_id) if user_id else None

            action_names = {
                "POST": "Создание / действие",
                "PUT": "Изменение",
                "PATCH": "Изменение",
                "DELETE": "Удаление"
            }

            entry = AuditLog(
                actor_id=user.id if user else None,
                actor_name=user.name if user else "Гость",
                actor_email=user.email if user else None,
                action=action_names.get(
                    request.method,
                    request.method
                ),
                details=(
                    f"{request.method} {request.path}"
                ),
                ip_address=request.remote_addr
            )

            db.session.add(entry)
            db.session.commit()

        except Exception:
            db.session.rollback()

    return response

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
    message_text = data.get("text", "")

    if not isinstance(message_text, str):
        return None, "Сообщение должно быть текстом"

    message_text = message_text.strip()

    if not message_text:
        return None, "Сообщение не может быть пустым"

    if len(message_text) > 20000:
        return None, "Сообщение слишком длинное"

    return message_text, None


# ============================================================
# ARTICLE HELPERS
# ============================================================

def article_upload(file, image_only=False):
    if not file or not file.filename:
        return None, "Файл не выбран"

    filename = secure_filename(file.filename)

    if "." not in filename:
        return None, "Некорректный файл"

    extension = filename.rsplit(".", 1)[1].lower()

    allowed = (
        ALLOWED_IMAGE_EXTENSIONS
        if image_only
        else ALLOWED_MEDIA_EXTENSIONS
    )

    if extension not in allowed:
        return None, "Неподдерживаемый формат файла"

    unique_name = f"{uuid.uuid4().hex}.{extension}"
    path = os.path.join(ARTICLE_UPLOAD_FOLDER, unique_name)

    try:
        file.save(path)
    except OSError:
        return None, "Не удалось сохранить файл"

    return f"/static/uploads/articles/{unique_name}", None


def article_form_data():
    title = request.form.get("title", "").strip()
    excerpt = request.form.get("excerpt", "").strip()
    author = request.form.get("author", "").strip()
    content = request.form.get("content", "")

    if not all((title, excerpt, author, content.strip())):
        return None, "Заполните все обязательные поля"

    if len(title) > 200:
        return None, "Название слишком длинное"

    if len(excerpt) > 500:
        return None, "Описание слишком длинное"

    if len(author) > 120:
        return None, "Имя автора слишком длинное"

    if len(content) > 500000:
        return None, "Содержимое статьи слишком большое"

    return {
        "title": title,
        "excerpt": excerpt,
        "author": author,
        "content": sanitize_article_html(content)
    }, None


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

    role = "member"

    user = User(
        name=name,
        email=email,
        role=role
    )

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    add_activity(user, "Регистрация аккаунта")


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

    raw_name = data.get("name", "")
    bio = data.get("bio", "")
    raw_telegram = data.get("telegram", "")

    if not isinstance(raw_name, str):
        return jsonify({"error": "Имя должно быть текстом"}), 400

    if not isinstance(bio, str):
        return jsonify({"error": "Биография должна быть текстом"}), 400

    if not isinstance(raw_telegram, str):
        return jsonify({"error": "Telegram должен быть текстом"}), 400

    name = raw_name.strip()
    telegram = raw_telegram.strip()

    if len(name) < 2:
        return jsonify({
            "error": "Имя слишком короткое"
        }), 400

    if len(name) > 100:
        return jsonify({
            "error": "Имя слишком длинное"
        }), 400

    if not isinstance(bio, str):
        return jsonify({
            "error": "Биография должна быть текстом"
        }), 400

    bio = bio.strip()

    if len(bio) > 500:
        return jsonify({
            "error": "Биография не должна превышать 500 символов"
        }), 400

    # Разрешаем ввод как с @, так и без него
    telegram = telegram.lstrip("@")

    if telegram and not re.fullmatch(r"[A-Za-z0-9_]{5,32}", telegram):
        return jsonify({
            "error": "Некорректный Telegram username"
        }), 400

    user.name = name
    user.bio = bio
    user.telegram = telegram or None

    db.session.commit()

    add_activity(user, "Обновление профиля")

    return jsonify({
        "user": user.to_dict()
    })

@app.route("/api/users/<int:user_id>/profile", methods=["GET"])
def get_public_profile(user_id):
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            "error": "Пользователь не найден"
        }), 404

    completed_count = CTFSubmission.query.filter_by(
        user_id=user.id,
        status="graded"
    ).count()

    return jsonify({
        "user": {
            "id": user.id,
            "name": user.name,
            "role": user.role,
            "role_label": ROLE_LABELS.get(user.role, user.role),
            "avatar": user.avatar,
            "bio": user.bio or "",
            "telegram": user.telegram,
            "points": get_user_points(user.id),
            "completed_count": completed_count,
            "created_at": (
                user.created_at.isoformat() + "Z"
                if user.created_at else None
            )
        }
    })

@app.route("/api/profile/avatar", methods=["POST"])
@login_required
def upload_avatar():
    user = current_user()
    file = request.files.get("avatar")

    if not file or not file.filename:
        return jsonify({
            "error": "Выберите изображение"
        }), 400

    filename = secure_filename(file.filename)

    if "." not in filename:
        return jsonify({
            "error": "Некорректный файл"
        }), 400

    extension = filename.rsplit(".", 1)[1].lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({
            "error": "Разрешены PNG, JPG, JPEG, WEBP и GIF"
        }), 400

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > 5 * 1024 * 1024:
        return jsonify({
            "error": "Максимальный размер аватара — 5 МБ"
        }), 400

    unique_name = f"{uuid.uuid4().hex}.{extension}"
    save_path = os.path.join(
        AVATAR_UPLOAD_FOLDER,
        unique_name
    )

    try:
        file.save(save_path)
    except OSError:
        return jsonify({
            "error": "Не удалось сохранить изображение"
        }), 500

    old_avatar = user.avatar
    user.avatar = f"/static/uploads/avatars/{unique_name}"

    db.session.commit()

    # Удаляем старый аватар только из папки аватаров
    if old_avatar and old_avatar.startswith(
        "/static/uploads/avatars/"
    ):
        old_filename = os.path.basename(old_avatar)
        old_path = os.path.join(
            AVATAR_UPLOAD_FOLDER,
            old_filename
        )

        if os.path.isfile(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

    add_activity(user, "Изменение аватара")

    return jsonify({
        "ok": True,
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
# MODERATION: AUDIT LOG
# ============================================================

@app.route("/api/mod/audit", methods=["GET"])
@role_required("admin", "moderator")
def get_audit_log():

    query = AuditLog.query

    user_id = request.args.get("user_id", "").strip()

    if user_id:
        try:
            query = query.filter(
                AuditLog.actor_id == int(user_id)
            )
        except ValueError:
            return jsonify({
                "success": False,
                "error": "Некорректный ID пользователя"
            }), 400

    action = request.args.get("action", "").strip()

    if action:
        query = query.filter(
            AuditLog.action == action
        )

    try:
        limit = min(
            max(int(request.args.get("limit", 200)), 1),
            500
        )
    except ValueError:
        limit = 200

    entries = query.order_by(
        AuditLog.created_at.desc()
    ).limit(limit).all()

    return jsonify({
        "success": True,
        "entries": [
            entry.to_dict()
            for entry in entries
        ]
    })

# ============================================================
# ARTICLES API
# ============================================================

@app.route("/api/articles", methods=["GET"])
def get_articles():
    user = current_user()

    query = Article.query

    if not user or user.role not in ("admin", "moderator"):
        query = query.filter_by(is_published=True)

    articles = query.order_by(
        Article.created_at.desc()
    ).all()

    return jsonify({
        "success": True,
        "articles": [article.to_dict() for article in articles]
    })


@app.route("/api/articles/<int:article_id>", methods=["GET"])
def get_article(article_id):
    article = db.session.get(Article, article_id)

    if not article:
        return jsonify({
            "success": False,
            "error": "Статья не найдена"
        }), 404

    user = current_user()

    if not article.is_published:
        if not user or user.role not in ("admin", "moderator"):
            return jsonify({
                "success": False,
                "error": "Статья не найдена"
            }), 404

    return jsonify({
        "success": True,
        "article": article.to_dict()
    })


@app.route("/api/articles", methods=["POST"])
@role_required("admin", "moderator")
def create_article():
    user = current_user()

    form_data, error = article_form_data()

    if error:
        return jsonify({
            "success": False,
            "error": error
        }), 400

    preview = None
    preview_file = request.files.get("preview")

    if preview_file and preview_file.filename:
        preview, error = article_upload(
            preview_file,
            image_only=True
        )

        if error:
            return jsonify({
                "success": False,
                "error": error
            }), 400

    article = Article(
        title=form_data["title"],
        excerpt=form_data["excerpt"],
        content=form_data["content"],
        preview=preview,
        author=form_data["author"],
        created_by=user.id,
        is_published=True
    )

    db.session.add(article)
    db.session.commit()

    add_activity(
        user,
        f"Опубликована статья: {article.title}"
    )

    return jsonify({
        "success": True,
        "message": "Статья опубликована",
        "article": article.to_dict()
    }), 201


@app.route("/api/articles/<int:article_id>", methods=["PUT"])
@role_required("admin", "moderator")
def update_article(article_id):
    user = current_user()

    article = db.session.get(Article, article_id)

    if not article:
        return jsonify({
            "success": False,
            "error": "Статья не найдена"
        }), 404

    form_data, error = article_form_data()

    if error:
        return jsonify({
            "success": False,
            "error": error
        }), 400

    preview_file = request.files.get("preview")

    if preview_file and preview_file.filename:
        preview, error = article_upload(
            preview_file,
            image_only=True
        )

        if error:
            return jsonify({
                "success": False,
                "error": error
            }), 400

        article.preview = preview

    article.title = form_data["title"]
    article.excerpt = form_data["excerpt"]
    article.author = form_data["author"]
    article.content = form_data["content"]

    db.session.commit()

    add_activity(
        user,
        f"Изменена статья: {article.title}"
    )

    return jsonify({
        "success": True,
        "message": "Статья обновлена",
        "article": article.to_dict()
    })


@app.route("/api/articles/<int:article_id>", methods=["DELETE"])
@role_required("admin", "moderator")
def delete_article(article_id):
    user = current_user()

    article = db.session.get(Article, article_id)

    if not article:
        return jsonify({
            "success": False,
            "error": "Статья не найдена"
        }), 404

    title = article.title

    db.session.delete(article)
    db.session.commit()

    add_activity(
        user,
        f"Удалена статья: {title}"
    )

    return jsonify({
        "success": True,
        "message": "Статья удалена"
    })


@app.route("/api/articles/upload-media", methods=["POST"])
@role_required("admin", "moderator")
def upload_article_media():
    file = request.files.get("file")

    media_url, error = article_upload(file)

    if error:
        return jsonify({
            "success": False,
            "error": error
        }), 400

    extension = media_url.rsplit(".", 1)[1].lower()

    if extension in ALLOWED_IMAGE_EXTENSIONS:
        media_type = "image"
    elif extension in {"mp4", "webm"}:
        media_type = "video"
    else:
        media_type = "audio"

    return jsonify({
        "success": True,
        "url": media_url,
        "type": media_type
    }), 201


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
@role_required("admin", "moderator")
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
# CTF MANAGEMENT
# ============================================================

@app.route("/api/mod/ctf/challenges", methods=["GET"])
@role_required("admin", "moderator")
def get_manageable_ctf_challenges():

    challenges = CTFChallenge.query.order_by(
        CTFChallenge.created_at.desc()
    ).all()

    return jsonify({
        "success": True,
        "challenges": [
            challenge.to_dict()
            for challenge in challenges
        ]
    })


@app.route("/api/ctf/<int:challenge_id>", methods=["PUT"])
@role_required("admin", "moderator")
def update_ctf_challenge(challenge_id):

    challenge = db.session.get(
        CTFChallenge,
        challenge_id
    )

    if not challenge:
        return jsonify({
            "success": False,
            "error": "CTF-задание не найдено"
        }), 404

    data = request.get_json(silent=True) or {}

    raw_title = data.get("title", "")
    raw_description = data.get("description", "")
    difficulty = data.get("difficulty")
    max_points = data.get("max_points")

    if not isinstance(raw_title, str):
        return jsonify({
            "success": False,
            "error": "Название должно быть текстом"
        }), 400

    if not isinstance(raw_description, str):
        return jsonify({
            "success": False,
            "error": "Описание должно быть текстом"
        }), 400

    title = raw_title.strip()
    description = raw_description.strip()

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
        max_points = int(max_points)
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

    challenge.title = title
    challenge.description = description
    challenge.difficulty = difficulty
    challenge.max_points = max_points

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "CTF-задание обновлено",
        "challenge": challenge.to_dict()
    })


@app.route("/api/ctf/<int:challenge_id>", methods=["DELETE"])
@role_required("admin", "moderator")
def delete_ctf_challenge(challenge_id):

    challenge = db.session.get(
        CTFChallenge,
        challenge_id
    )

    if not challenge:
        return jsonify({
            "success": False,
            "error": "CTF-задание не найдено"
        }), 404

    submission_ids = [
        row[0]
        for row in db.session.query(CTFSubmission.id)
        .filter_by(challenge_id=challenge_id)
        .all()
    ]

    if submission_ids:
        CTFMessage.query.filter(
            CTFMessage.submission_id.in_(submission_ids)
        ).delete(synchronize_session=False)

        CTFSubmission.query.filter(
            CTFSubmission.id.in_(submission_ids)
        ).delete(synchronize_session=False)

    db.session.delete(challenge)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "CTF-задание удалено"
    })

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

    message_text, error = validate_message(data)

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
        text=message_text
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

    message_text, error = validate_message(data)

    if error:
        return jsonify({
            "success": False,
            "error": error
        }), 400

    message = CTFMessage(
        submission_id=submission.id,
        sender_id=user.id,
        text=message_text
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
# ERROR HANDLERS
# ============================================================

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "success": False,
        "error": "Файл слишком большой. Максимальный размер — 25 МБ."
    }), 413


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

with app.app_context():
    db.create_all()

    # Однократное назначение администратора через Render
    admin_email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()

    if admin_email:
        user = User.query.filter(
            db.func.lower(User.email) == admin_email
        ).first()

        if user:
            user.role = "admin"
            db.session.commit()
            print(f"Administrator role assigned to: {admin_email}")
        else:
            print(f"Admin account not found: {admin_email}")

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

    # Миграция полей публичного профиля
    profile_columns = {
        "avatar": "VARCHAR(500)",
        "bio": "VARCHAR(500) NOT NULL DEFAULT ''",
        "telegram": "VARCHAR(32)"
    }

    for column_name, column_type in profile_columns.items():
        if column_name not in cols:
            with db.engine.connect() as conn:
                conn.execute(
                    text(
                        f"ALTER TABLE users "
                        f"ADD COLUMN {column_name} {column_type}"
                    )
                )
                conn.commit()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5001
    )