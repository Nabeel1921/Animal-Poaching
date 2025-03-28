import streamlit as st
from passlib.hash import pbkdf2_sha256
from ultralytics import YOLO
import cv2
import math
import cvzone
import tempfile
import numpy as np
import base64
import sqlite3
import smtplib
from playsound import playsound

# Security improvements: Use environment variables for credentials
# Replace these with your actual credentials using environment variables
# Create a .env file with:
# EMAIL_USER="your_email@gmail.com"
# EMAIL_PASS="your_app_password"
# ALERT_EMAIL="recipient@example.com"

import os
from dotenv import load_dotenv
load_dotenv()

# Configuration
FIRE_CLASSES = ['fire']
ANIMAL_CLASSES = [
    'antelope', 'badger', 'bat', 'bear', 'bee', 'beetle', 'bison', 'boar',
    'butterfly', 'cat', 'caterpillar', 'chimpanzee', 'cockroach', 'cow',
    'coyote', 'crab', 'cranefly', 'crow', 'deer', 'dog', 'dolphin', 'donkey',
    'dragonfly', 'duck', 'eagle', 'elephant', 'flamingo', 'fly', 'fox', 'goat',
    'goldfish', 'goose', 'gorilla', 'grasshopper', 'hamster', 'hare', 'hedgehog',
    'hippopotamus', 'hornbill', 'horse', 'hummingbird', 'hyena', 'jellyfish',
    'kangaroo', 'koala', 'ladybug', 'leopard', 'lion', 'lizard', 'lobster',
    'mosquito', 'moth', 'mouse', 'octopus', 'okapi', 'orangutan', 'otter',
    'owl', 'ox', 'oyster', 'panda', 'parrot', 'pelecaniformes', 'penguin',
    'pig', 'pigeon', 'porcupine', 'possum', 'raccoon', 'rat', 'reindeer',
    'rhinoceros', 'sandpiper', 'seahorse', 'seal', 'shark', 'sheep', 'snake',
    'sparrow', 'squid', 'squirrel', 'starfish', 'swan', 'tiger', 'turkey',
    'turtle', 'whale', 'wolf', 'wombat', 'woodpecker', 'zebra'
]

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
PORT = 587
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")

# Load models
@st.cache_resource
def load_fire_model():
    return YOLO('best.pt')

@st.cache_resource
def load_animal_model():
    return YOLO('main.pt')

# Database functions
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        st.error(f"Database error: {e}")
    return conn

def create_table(conn):
    try:
        sql = '''CREATE TABLE IF NOT EXISTS users (
                    username text PRIMARY KEY,
                    password text NOT NULL
                 );'''
        conn.execute(sql)
    except Exception as e:
        st.error(f"Table creation error: {e}")

# Authentication functions
def signup(username, password, conn):
    try:
        hashed_password = pbkdf2_sha256.hash(password)
        sql = '''INSERT INTO users(username, password) VALUES(?,?)'''
        cur = conn.cursor()
        cur.execute(sql, (username, hashed_password))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Signup error: {e}")
        return False

def validate_login(username, password, conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = ?", (username,))
        user_data = cur.fetchone()
        if user_data and pbkdf2_sha256.verify(password, user_data[0]):
            return True
        return False
    except Exception as e:
        st.error(f"Login error: {e}")
        return False

# Detection functions
def send_alert():
    try:
        with smtplib.SMTP(SMTP_SERVER, PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, ALERT_EMAIL, "FIRE DETECTED!")
        playsound('alert.wav')
    except Exception as e:
        st.error(f"Alert system error: {e}")

def process_frame(frame, model, classes, detection_type):
    frame = cv2.resize(frame, (640, 480))
    results = model(frame, stream=True)
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            confidence = math.ceil(box.conf[0] * 100)
            if confidence < 50:
                continue
                
            class_id = int(box.cls[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cvzone.putTextRect(frame, f'{classes[class_id]} {confidence}%', 
                             (x1 + 8, y1 - 20), scale=1, thickness=1)
            
            # Fire alert system
            if detection_type == 'Fire' and classes[class_id] == 'fire':
                send_alert()
    
    return frame

# UI functions
def main_app():
    st.title('Multi-Object Detection System')
    
    # Detection type selection
    detection_type = st.radio("Select Detection Type", 
                             ('Fire Detection', 'Animal Detection'))
    
    # Load appropriate model
    if detection_type == 'Fire Detection':
        model = load_fire_model()
        classes = FIRE_CLASSES
    else:
        model = load_animal_model()
        classes = ANIMAL_CLASSES

    # Input type selection
    input_option = st.radio("Choose input type", 
                           ('Image', 'Video', 'Live Stream'))
    
    # Logout button
    st.sidebar.button('Logout', on_click=lambda: st.session_state.update({'logged_in': False}))

    # Image upload
    if input_option == 'Image':
        uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png"])
        if uploaded_file is not None:
            image = cv2.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), 1)
            processed_image = process_frame(image, model, classes, detection_type)
            st.image(processed_image, channels="BGR", use_column_width=True)

    # Video upload
    elif input_option == 'Video':
        uploaded_file = st.file_uploader("Upload a video", type=["mp4", "avi"])
        if uploaded_file is not None:
            with tempfile.NamedTemporaryFile(delete=False) as tfile:
                tfile.write(uploaded_file.read())
                cap = cv2.VideoCapture(tfile.name)
                frame_placeholder = st.empty()
                
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    processed_frame = process_frame(frame, model, classes, detection_type)
                    frame_placeholder.image(processed_frame, channels="BGR")
                cap.release()

    # Live stream
    elif input_option == 'Live Stream':
        stop = st.button('Stop Streaming')
        frame_placeholder = st.empty()
        cap = cv2.VideoCapture(0)
        
        while not stop:
            ret, frame = cap.read()
            if not ret:
                break
            processed_frame = process_frame(frame, model, classes, detection_type)
            frame_placeholder.image(processed_frame, channels="BGR")
        cap.release()

# Authentication flow
def main():
    # Initialize database
    conn = create_connection('user_database.db')
    create_table(conn)
    
    # Session state initialization
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    # Authentication pages
    if not st.session_state['logged_in']:
        st.sidebar.title("Authentication")
        auth_option = st.sidebar.radio("Choose Option", ["Login", "Signup"])
        
        if auth_option == "Signup":
            with st.form("signup_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Signup")
                
                if submit:
                    if signup(username, password, conn):
                        st.success("Signup successful! Please login.")
                    else:
                        st.error("Username already exists")
        
        else:  # Login
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    if validate_login(username, password, conn):
                        st.session_state['logged_in'] = True
                        st.success("Logged in successfully!")
                    else:
                        st.error("Invalid credentials")
    else:
        main_app()

if __name__ == "__main__":
    main()