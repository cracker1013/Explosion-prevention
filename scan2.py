import cv2
import mediapipe as mp
import numpy as np
import time

# MediaPipe の初期化
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)
    return np.degrees(angle)

last_print = time.time()
interval = 0.5  # 秒（0.5秒ごとに表示）

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # BGR→RGB に変換
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # 姿勢推定
    results = pose.process(rgb_frame)

    # 骨格を描画
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame, 
            results.pose_landmarks, 
            mp_pose.POSE_CONNECTIONS
        )
        landmarks = results.pose_landmarks.landmark
        # 右肩,右肘,右手首
        r_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                      landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
        r_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                   landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
        r_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                   landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
        # 左肩,左肘,左手首
        l_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                      landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        l_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                   landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        l_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                   landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
        # 右肘角度
        elbow_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
        # 右肩角度（腰,肩,肘）
        r_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                 landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
        shoulder_angle = calculate_angle(r_hip, r_shoulder, r_elbow)
        # 左肘角度
        l_elbow_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
        # 左肩角度（腰,肩,肘）
        l_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                 landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        l_shoulder_angle = calculate_angle(l_hip, l_shoulder, l_elbow)
        if time.time() - last_print > interval:
            print(f'右肘角度: {elbow_angle:.2f}度')
            print(f'右肩角度: {shoulder_angle:.2f}度')
            print(f'左肘角度: {l_elbow_angle:.2f}度')
            print(f'左肩角度: {l_shoulder_angle:.2f}度')
            if (shoulder_angle - l_shoulder_angle)**2 > 500:
                print("左右の肘が非対称。")
            if (shoulder_angle > 80 or l_shoulder_angle > 80):
                print("肘上がりすぎ。")
            print("\n\n")
            last_print = time.time()

    cv2.imshow("Pose Estimation", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
