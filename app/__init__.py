from flask import Flask


def create_app():
    app = Flask(__name__)

    from app.routes import main
    from app.openai_api import openai_api

    app.register_blueprint(main)
    app.register_blueprint(openai_api)

    return app
