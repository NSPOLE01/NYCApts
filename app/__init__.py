import json
from flask import Flask
from .storage import db
import config


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["SECRET_KEY"] = config.FLASK_SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Add fromjson filter so templates can parse JSON strings
    app.jinja_env.filters["fromjson"] = lambda s: json.loads(s) if s else []

    with app.app_context():
        db.create_all()

    from .web import bp
    app.register_blueprint(bp)

    return app
