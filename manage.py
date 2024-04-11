from flask import Flask
from flask_migrate import Migrate

app = Flask(__name__)  # Initialize Flask app within manage.py

from file_integrity_monitor import db  # Import db after app initialization

migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():  # Ensure database tables are created
        db.create_all()

    import flask
    flask.cli.main(['db', 'init'])

    