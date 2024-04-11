import os
import hashlib
import schedule
import time
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, func, Sequence
from httpx import AsyncClient
from smtplib import SMTP_SSL
from email.mime.text import MIMEText

Base = declarative_base()

class FileModel(Base):
    __tablename__ = "files"

    id = Column(Integer, Sequence('file_id_seq'), primary_key=True, nullable=False)
    file_path = Column(String(200), unique=True, nullable=False)
    checksum = Column(String(64), nullable=False)

    def __repr__(self):
        return f"<FileModel(id='{self.id}', file_path='{self.file_path}', checksum='{self.checksum}')>"

    @classmethod
    def from_path_and_checksum(cls, file_path, checksum):
        return cls(file_path=file_path, checksum=checksum)

def calculate_checksum(file_path):
    """Calculates the SHA-256 hash of a file."""
    with open(file_path, "rb") as f:
        file_data = f.read()
        return hashlib.sha256(file_data).hexdigest()

async def send_email_notification_async(file_path):
    """Sends an email notification asynchronously."""
    async with AsyncClient() as client:
        await client.post(f"http://localhost:8000/send-email-notification", json={"file_path": file_path, "recipient_email": "recipient@example.com"})

async def notify_file_change(file_path):
    await send_email_notification_async(file_path)

def scan_file(file_path, session):
    """Checks if the checksum of a file has changed and updates the database."""
    current_checksum = calculate_checksum(file_path)

    existing_file = session.query(FileModel).filter_by(file_path=file_path).first()

    if not existing_file:
        new_file = FileModel.from_path_and_checksum(file_path, current_checksum)
        session.add(new_file)
        session.commit()

    elif existing_file.checksum != current_checksum:
        existing_file.checksum = current_checksum

        print(f"Change detected in file: {file_path}")
        asyncio.run(notify_file_change(file_path))

    session.commit()

def scan_directory(directory_path, session):
    """Scans a directory and checks for file changes."""
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            scan_file(file_path, session)

def init_file_integrity_monitoring():
    engine = create_engine('sqlite:///my_file_monitoring.db')
    Base.metadata.create_all(engine, checkfirst=True)

    # Create the sequence if it doesn't exist
    engine.execute('CREATE SEQUENCE IF NOT EXISTS file_id_seq')

    Session = sessionmaker(bind=engine)
    session = Session()

    # Initial scan for the baseline
    directory_to_monitor = r"C:\Users\asus\Desktop\research"
    scan_directory(directory_to_monitor, session)

    # Scheduled scan every 30 seconds for demonstration
    schedule.every(30).seconds.do(scan_directory, directory_to_monitor, session)

    def background_task():
        schedule.run_pending()

    schedule.every(30).seconds.do(background_task)

    while True:
        time.sleep(1)

def send_email_notification(file_path, recipient_email="recipient@example.com"):
    """Sends an email notification."""
    sender_email = "your_email@example.com"  # Replace with your actual email address
    password = "your_email_password"      # Replace with your actual email password

    message = MIMEText(f"File '{file_path}' has been modified.", "plain")
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = "File Integrity Monitoring Alert"

    with SMTP_SSL("smtp.example.com", 465) as server:  # Replace with your SMTP server details
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient_email, message.as_string())

if __name__ == "__main__":
    init_file_integrity_monitoring()