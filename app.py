import streamlit as st
from passlib.hash import pbkdf2_sha256
from ultralytics import YOLO
import cv2
import math
import cvzone
import tempfile
import numpy as np
import sqlite3
import smtplib
import os
from dotenv import load_dotenv
s = smtplib.SMTP('smtp.gmail.com', 587)
s.starttls()
s.login("praveenjana6@gmail.com", "nljjrcmxbstkacar")


# Security improvements
load_dotenv()



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



def load_animal_model():
    return YOLO('main.pt')

def create_connection(db_file):
    try:
        return sqlite3.connect(db_file)
    except Exception as e:
        st.error(f"Database error: {e}")

def create_table(conn):
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
                    username text PRIMARY KEY,
                    password text NOT NULL
                 );''')
    except Exception as e:
        st.error(f"Table creation error: {e}")

def signup(username, password, conn):
    try:
        hashed_password = pbkdf2_sha256.hash(password)
        conn.cursor().execute("INSERT INTO users VALUES (?,?)", (username, hashed_password))
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
        return user_data and pbkdf2_sha256.verify(password, user_data[0])
    except Exception as e:
        st.error(f"Login error: {e}")
        return False



def process_frame(frame, model, classes):
    frame = cv2.resize(frame, (640, 480))
    results = model(frame, stream=True)
    animal_detected = False
    detected_animal = ""
    for result in results:
        boxes = result.boxes
        for box in boxes:
            confidence = math.ceil(box.conf[0] * 100)
            if confidence < 50:
                continue
                
            class_id = int(box.cls[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cvzone.putTextRect(frame, f'{classes[class_id]} {confidence}%', 
                             (x1 + 8, y1 - 20), scale=1, thickness=1)
            if classes[class_id] in ANIMAL_CLASSES:
                    animal_detected = True
                    detected_animal = classes[class_id]   
            if animal_detected:
                subject = "Animal Detected Alert!"
                message = f"Subject: {subject}\n\nAn animal ({detected_animal}) has been detected."
                s.sendmail("praveenjana6@gmail.com", "ismailrockz111@gmail.com", message) 
    return frame

# UI functions
def main_app():
    st.title('Animal Detection System 🔥🐾')
    
    
    # Load appropriate model
    model = YOLO('main.pt')
    classes = ['antelope', 'badger', 'bat', 'bear', 'bee', 'beetle', 'bison', 'boar',
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
    'turtle', 'whale', 'wolf', 'wombat', 'woodpecker', 'zebra']

    # Input type selection
    input_option = st.radio("Choose input type", 
                           ('🖼️ Image', '🎥 Video', '@Webcam 📹'))
    
    # Logout button
    st.sidebar.button('🚪 Logout', on_click=lambda: st.session_state.update({'logged_in': False}))

    # Image upload
    if input_option == '🖼️ Image':
        uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png"])
        if uploaded_file:
            image = cv2.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), 1)
            processed_image = process_frame(image, model, classes)
            st.image(processed_image, channels="BGR", use_column_width=True)

    # Video upload
    elif input_option == '🎥 Video':
        uploaded_file = st.file_uploader("Upload a video", type=["mp4", "avi"])
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False) as tfile:
                tfile.write(uploaded_file.read())
                cap = cv2.VideoCapture(tfile.name)
                frame_placeholder = st.empty()
                
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    processed_frame = process_frame(frame, model, classes)
                    frame_placeholder.image(processed_frame, channels="BGR")
                cap.release()

    # Live stream
    elif input_option == '@Webcam 📹':
        stop = st.button('🛑 Stop Streaming')
        frame_placeholder = st.empty()
        cap = cv2.VideoCapture(0)
        
        while not stop:
            ret, frame = cap.read()
            if not ret:
                break
            processed_frame = process_frame(frame, model, classes)
            frame_placeholder.image(processed_frame, channels="BGR")
        cap.release()

# Authentication flow
def main():
    conn = create_connection('user_database.db')
    create_table(conn)
    
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        st.sidebar.title("Authentication 🔐")
        auth_option = st.sidebar.radio("Choose Option", ["Login", "Signup"])
        
        if auth_option == "Signup":
            with st.form("signup_form"):
                st.subheader("Create New Account")
                username = st.text_input("Username 🧑💻")
                password = st.text_input("Password 🔒", type="password")
                submit = st.form_submit_button("Signup 🚀")
                
                if submit:
                    if signup(username, password, conn):
                        st.success("✅ Signup successful! Please login.")
                    else:
                        st.error("❌ Username already exists")
        
        else:
            with st.form("login_form"):
                st.subheader("Login to Your Account")
                username = st.text_input("Username 🧑💻")
                password = st.text_input("Password 🔒", type="password")
                submit = st.form_submit_button("Login 🚀")
                
                if submit:
                    if validate_login(username, password, conn):
                        st.session_state['logged_in'] = True
                        st.success("✅ Login successful!")
                    else:
                        st.error("❌ Invalid credentials")
    else:
        main_app()

if __name__ == "__main__":
    main()