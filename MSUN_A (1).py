import cv2
import mediapipe as mp
import time
import ctypes
from plyer import notification
import tkinter as tk
from tkinter import filedialog
#import pygame 


count=0

# Constants for movement detection
MOVEMENT_THRESHOLD = 0.01
MIN_STILL_DURATION = 1.0
SLEEPING_DISPLAY_DURATION = 6
ZOOM_OUT_SCALE = 0.7

# Function to calculate movement
def calculate_movement(previous_landmarks, current_landmarks):
    total_movement = 0.0
    for pb, cb in zip(previous_landmarks, current_landmarks):
        dx = cb.x - pb.x
        dy = cb.y - pb.y
        movement = (dx ** 2) + (dy ** 2)
        total_movement += movement
    return total_movement

# Function to check if the person is still or moving
def is_person_still(previous_landmarks, current_landmarks):
    movement = calculate_movement(previous_landmarks, current_landmarks)
    if movement < MOVEMENT_THRESHOLD:
        return True
    return False

# Function to detect sleeping posture
def detect_sleeping(results):
    try:
        left_eye = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_EYE]
        right_eye = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_EYE]
        nose = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.NOSE]
        left_hip = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_HIP]
        right_hip = results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_HIP]

        eye_distance = abs(right_eye.y - left_eye.y)
        nose_distance = abs(nose.y - left_eye.y)
        hip_distance = abs(right_hip.y - left_hip.y)

        if nose_distance < eye_distance * 0.8 and hip_distance > eye_distance * 2:
            return True
    except:
        pass
    return False

# Function to detect if a person is uneasy
def detect_uneasy(pose_results):
    try:
        left_shoulder = pose_results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = pose_results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
        left_elbow = pose_results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_ELBOW]
        right_elbow = pose_results.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_ELBOW]

        shoulder_distance = abs(right_shoulder.y - left_shoulder.y)
        elbow_distance = abs(right_elbow.y - left_elbow.y)

        if elbow_distance > shoulder_distance*2 :
            return True
    except:
        pass
    return False

# MediaPipe Pose Detection
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose_detection = mp_pose.Pose(static_image_mode=False, model_complexity=2)

# Create a tkinter window
root = tk.Tk()
root.title("Pose Detection Application")

# Maximize the tkinter window
root.state('zoomed')

# Fill the window with a mild background color
root.configure(bg='lightgray')

# Function to start the application
def start_application():
    global use_live_video, video_path
    use_live_video = live_video_var.get()
    if use_live_video == 'n':
        video_path = filedialog.askopenfilename()  # Ask the user to select a local video
    root.destroy()

# Create a label to explain the options
label = tk.Label(root, text="Choose video source:", bg='lightgray')
label.pack()

# Create radio buttons for live video and local video options
live_video_var = tk.StringVar(value="n")
live_video_radio = tk.Radiobutton(root, text="Live Video", variable=live_video_var, value="y", bg='lightgray')
local_video_radio = tk.Radiobutton(root, text="Local Video", variable=live_video_var, value="n", bg='lightgray')

live_video_radio.pack()
local_video_radio.pack()

# Create a button to start the application
start_button = tk.Button(root, text="Start", command=start_application, bg='lightblue')
start_button.pack()

# Start the tkinter main loop
root.mainloop()

# Choose video source based on user's choice
if use_live_video == 'y':
    # Webcam Opening
    cap = cv2.VideoCapture(0)
else:
    cap = cv2.VideoCapture(video_path)

# Variables for movement detection
previous_landmarks = None
is_still = False
still_start_time = 0.0
sleeping_detected_time = 0.0

# Get screen resolution
user32 = ctypes.windll.user32
screen_width = user32.GetSystemMetrics(0)
screen_height = user32.GetSystemMetrics(1)

# Reduce screen size by 40%
window_width = int(screen_width * 0.6)
window_height = int(screen_height * 0.6)

# Create a window
cv2.namedWindow("Pose Detection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Pose Detection", window_width, window_height)

uneasy_detected = False

# Function to show a desktop notification and play alarm sound
def show_notification(message):
    notification_title = "Immediate Attention Required"
    notification_message = "Patient is very uncomfortable\nSituation may be critical"
    notification.notify(
        title=notification_title,
        message=notification_message,
        app_name="Pose Detection App",
    )
    play_alarm_sound()

# Function to play the alarm sound
def play_alarm_sound():
    pygame.mixer.init()
    pygame.mixer.music.load(r'C:\Users\DELL\OneDrive\Desktop\Human-project\mixkit-critical-alarm-1004.wav')
    pygame.mixer.music.play()

# Initialize the notification flag and the timer
notification_timer = None
notification_shown = False
sleeping_display_timer = None
sleeping_detected = False

while True:
    ret, frame = cap.read()

    if not ret:
        break

    frame = cv2.flip(frame, 1)

    frame = cv2.resize(frame, (int(frame.shape[1] * ZOOM_OUT_SCALE), int(frame.shape[0] * ZOOM_OUT_SCALE)))

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    pose_results = pose_detection.process(rgb_frame)

    mp_drawing.draw_landmarks(
        frame,
        pose_results.pose_landmarks,
        mp_pose.POSE_CONNECTIONS,
        mp_drawing.DrawingSpec(
            color=(0, 255, 0), thickness=2, circle_radius=2),
        mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=2)
    )

    current_landmarks = []
    if pose_results.pose_landmarks:
        for landmark in pose_results.pose_landmarks.landmark:
            current_landmarks.append(landmark)

    if previous_landmarks is not None and current_landmarks:
        if is_person_still(previous_landmarks, current_landmarks):
            if not is_still:
                still_start_time = cv2.getTickCount()
            is_still = True
        else:
            is_still = False

    movement_status = "Person is moving" if not is_still else "Person is still"
    cv2.putText(frame, movement_status, (
20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    if is_still and detect_sleeping(pose_results):
        if not sleeping_detected:
            sleeping_detected_time = time.time()
            sleeping_detected = True
            sleeping_display_timer = time.time()
        elif time.time() - sleeping_display_timer <= SLEEPING_DISPLAY_DURATION:
            cv2.putText(frame, "Sleeping Detected", (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)  # Orange color

    if detect_uneasy(pose_results) or uneasy_detected:
        cv2.putText(frame, ".", (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        if not notification_shown and notification_timer is None:
            notification_timer = time.time()
            notification_shown = True
            count=count+1

    if notification_timer is not None and time.time() - notification_timer >= 6.5:
        show_notification("Immediate Attention Required\nPatient is in trouble\nSituation may be critical")
        notification_timer = None

    previous_landmarks = current_landmarks

    cv2.imshow("Pose Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()