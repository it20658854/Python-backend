from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from file_integrity_monitor import FileModel, calculate_checksum, init_file_integrity_monitoring, send_email_notification, scan_directory
import schedule
import time
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
import smtplib
from email.mime.text import MIMEText

# Initialize FastAPI app
app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Serve static files (e.g., CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./my_file_monitoring.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Call the init_file_integrity_monitoring function
init_file_integrity_monitoring()

# OAuth2PasswordBearer for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")  # Replace with your authentication endpoint

# Function to get current user email (placeholder, replace with your logic)
async def get_current_user_email(token: str = Depends(oauth2_scheme)):
    # Implement your authentication and user retrieval logic here
    return "user@example.com"  # Replace with actual user email

# Function to send email notification asynchronously
async def send_email_notification(file_path, recipient_email):
    """Sends an email notification asynchronously."""
    sender_email = "your_email@example.com"  # Replace with your actual email address
    password = "your_email_password"      # Replace with your actual email password (consider using a secure app password)

    message = MIMEText(f"File '{file_path}' has been modified.", "plain")
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = "File Integrity Monitoring Alert"

    with smtplib.SMTP_SSL("smtp.example.com", 465) as server:  # Replace with your SMTP server details
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient_email, message.as_string())

# API endpoints
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head>
            <title>File Integrity Monitoring Dashboard</title>
            <link href="/static/styles.css" rel="stylesheet" type="text/css">
        </head>
        <body>
            <h1>File Integrity Monitoring Dashboard</h1>
            <form action="/upload/" enctype="multipart/form-data" method="post">
                <input type="file" name="file">
                <input type="submit" value="Upload File">
            </form>
            <button onclick="scan()">Scan</button>
            <script src="/static/scripts.js"></script>
        </body>
    </html>
    """

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    # Process the uploaded file
    contents = await file.read()
    checksum = calculate_checksum(file.filename)  # Calculate the file checksum
    # Save file to disk, calculate checksum, etc.
    # Then, store file metadata in the database
    db = SessionLocal()
    db_file = FileModel.from_path_and_checksum(file.filename, checksum)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    db.close()

    scan_files(file.filename, db)
    return {"filename": file.filename}

@app.get("/files/", response_model=List[FileModel])
async def get_files():
    # Retrieve all files from the database
    db = SessionLocal()
    files = db.query(FileModel).all()
    db.close()
    return files

@app.get("/scan")
async def scan_files():
    directory_to_monitor = r"C:\Users\asus\Desktop\research"  # Replace with the desired directory
    db = SessionLocal()
    scan_directory(directory_to_monitor, db)
    db.close()
    return {"message": "Scan completed"}

@app.post("/send-email-notification")
async def send_notification(background_tasks: BackgroundTasks, file_path: str, recipient_email: str):
    background_tasks.add_task(send_email_notification, file_path, recipient_email)
    return {"message": "Email notification sent"}

@app.get("/dashboard")
async def dashboard(request: Request):
    db = SessionLocal()
    files = db.query(FileModel).all()
    db.close()
    return templates.TemplateResponse("dashboard.html", {"request": request, "files": files})

@app.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

users = {"user1@example.com": "password1", "user2@example.com": "password2"}  # Replace with actual user credentials
@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    if email in users and users[email] == password:
        # Successful login
        return templates.TemplateResponse("dashboard.html", {"request": request, "email": email})
    else:
        # Failed login
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email or password"})

# Example usage in a route where a file change is detected:
@app.get("/file-changed/{file_path}")
async def handle_file_change(file_path: str, background_tasks: BackgroundTasks, user_email: str = Depends(get_current_user_email)):
    # ... perform other actions related to file change

    # Send email notification in the background
    background_tasks.add_task(send_email_notification, file_path, user_email)
    return {"message": "Email notification sent"}

@app.get("/register")
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})