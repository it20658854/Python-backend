from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_file_monitoring.db'
db = SQLAlchemy(app)

class FileModel(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    file_path = db.Column(db.String(200), unique=True, nullable=False)
    checksum = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return f"<FileModel(id='{self.id}', file_path='{self.file_path}', checksum='{self.checksum}')>"

# Uncomment this line to create the database schema (run only once)
# with app.app_context():
#     db.create_all()