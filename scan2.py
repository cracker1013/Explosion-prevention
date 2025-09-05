import cv2
import mediapipe as mp

# MediaPipe の初期化
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

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

    cv2.imshow("Pose Estimation", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
