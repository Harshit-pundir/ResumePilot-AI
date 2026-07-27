from flask import Flask

from config import SECRET_KEY
from extensions import initialize_extensions
from routes.ai import ai_bp
from routes.history import history_bp
from routes.home import home_bp
from routes.report import report_bp
from routes.upload import upload_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    initialize_extensions(app)

    app.register_blueprint(home_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(report_bp)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
