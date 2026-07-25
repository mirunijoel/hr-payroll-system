from flask import Flask, jsonify

from database import init_db


def create_app(seed_db=True):
    app = Flask(__name__)

    init_db(seed=seed_db)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
