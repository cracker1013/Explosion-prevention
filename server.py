from flask import Flask, jsonify
from flask_cors import CORS
import cv2
import mediapipe as mp
import numpy as np
import threading
import random

app = Flask(__name__)
CORS(app)

# グローバル変数で最新の角度を保持
angle_data = {
    'right_elbow': None,
    'right_shoulder': None,
    'left_elbow': None,
    'left_shoulder': None,
    'shoulder_diff': None,
    'shoulder_warning': False,
    'elbow_warning': False
}

angle_data_lock = threading.Lock()

def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)
    return np.degrees(angle)

def pose_thread():
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)
        # カメラ映像を別ウィンドウで表示
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            # 主要ランドマーク（肩・肘・手首・腰）に点を描画
            points = [
                mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
                mp_pose.PoseLandmark.RIGHT_ELBOW.value,
                mp_pose.PoseLandmark.RIGHT_WRIST.value,
                mp_pose.PoseLandmark.LEFT_SHOULDER.value,
                mp_pose.PoseLandmark.LEFT_ELBOW.value,
                mp_pose.PoseLandmark.LEFT_WRIST.value,
                mp_pose.PoseLandmark.RIGHT_HIP.value,
                mp_pose.PoseLandmark.LEFT_HIP.value,
                mp_pose.PoseLandmark.RIGHT_KNEE.value,
                mp_pose.PoseLandmark.LEFT_KNEE.value,
                mp_pose.PoseLandmark.RIGHT_ANKLE.value,
                mp_pose.PoseLandmark.LEFT_ANKLE.value,
                mp_pose.PoseLandmark.NOSE.value
            ]
            h, w = frame.shape[:2]
            for idx in points:
                x = int(landmarks[idx].x * w)
                y = int(landmarks[idx].y * h)
                cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)
            # 各部位を線で結ぶ
            body_landmarks = [
                (mp_pose.PoseLandmark.RIGHT_SHOULDER.value, 'shoulder'),
                (mp_pose.PoseLandmark.LEFT_SHOULDER.value, 'shoulder'),
                (mp_pose.PoseLandmark.RIGHT_ELBOW.value, 'right_arm'),
                (mp_pose.PoseLandmark.LEFT_ELBOW.value, 'left_arm'),
                (mp_pose.PoseLandmark.RIGHT_WRIST.value, 'right_arm'),
                (mp_pose.PoseLandmark.LEFT_WRIST.value, 'left_arm'),
                (mp_pose.PoseLandmark.RIGHT_HIP.value, 'hip'),
                (mp_pose.PoseLandmark.LEFT_HIP.value, 'hip'),
                (mp_pose.PoseLandmark.RIGHT_KNEE.value, 'right_leg'),
                (mp_pose.PoseLandmark.LEFT_KNEE.value, 'left_leg'),
                (mp_pose.PoseLandmark.RIGHT_ANKLE.value, 'right_leg'),
                (mp_pose.PoseLandmark.LEFT_ANKLE.value, 'left_leg'),
                (mp_pose.PoseLandmark.NOSE.value, 'nose')
            ]
            h, w = frame.shape[:2]
            # プロット（点）は赤で統一
            for idx, part in body_landmarks:
                x = int(landmarks[idx].x * w)
                y = int(landmarks[idx].y * h)
                cv2.circle(frame, (x, y), 10, (0, 0, 255), -1)
            # 線は白で統一
            def draw_line(a_idx, b_idx):
                ax = int(landmarks[a_idx].x * w)
                ay = int(landmarks[a_idx].y * h)
                bx = int(landmarks[b_idx].x * w)
                by = int(landmarks[b_idx].y * h)
                cv2.line(frame, (ax, ay), (bx, by), (255,255,255), 4)
            # 右腕
            draw_line(mp_pose.PoseLandmark.RIGHT_SHOULDER.value, mp_pose.PoseLandmark.RIGHT_ELBOW.value)
            draw_line(mp_pose.PoseLandmark.RIGHT_ELBOW.value, mp_pose.PoseLandmark.RIGHT_WRIST.value)
            # 左腕
            draw_line(mp_pose.PoseLandmark.LEFT_SHOULDER.value, mp_pose.PoseLandmark.LEFT_ELBOW.value)
            draw_line(mp_pose.PoseLandmark.LEFT_ELBOW.value, mp_pose.PoseLandmark.LEFT_WRIST.value)
            # 右脚
            draw_line(mp_pose.PoseLandmark.RIGHT_HIP.value, mp_pose.PoseLandmark.RIGHT_KNEE.value)
            draw_line(mp_pose.PoseLandmark.RIGHT_KNEE.value, mp_pose.PoseLandmark.RIGHT_ANKLE.value)
            # 左脚
            draw_line(mp_pose.PoseLandmark.LEFT_HIP.value, mp_pose.PoseLandmark.LEFT_KNEE.value)
            draw_line(mp_pose.PoseLandmark.LEFT_KNEE.value, mp_pose.PoseLandmark.LEFT_ANKLE.value)
            # 肩同士
            draw_line(mp_pose.PoseLandmark.RIGHT_SHOULDER.value, mp_pose.PoseLandmark.LEFT_SHOULDER.value)
            # 腰同士
            draw_line(mp_pose.PoseLandmark.RIGHT_HIP.value, mp_pose.PoseLandmark.LEFT_HIP.value)
            # 鼻-両肩
            draw_line(mp_pose.PoseLandmark.NOSE.value, mp_pose.PoseLandmark.RIGHT_SHOULDER.value)
            draw_line(mp_pose.PoseLandmark.NOSE.value, mp_pose.PoseLandmark.LEFT_SHOULDER.value)
            # 角度計算
            with angle_data_lock:
                angle_data['right_elbow'] = round(calculate_angle(
                    [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y],
                    [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y],
                    [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                ), 2)
                angle_data['right_shoulder'] = round(calculate_angle(
                    [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y],
                    [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y],
                    [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                ), 2)
                angle_data['left_elbow'] = round(calculate_angle(
                    [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y],
                    [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y],
                    [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                ), 2)
                angle_data['left_shoulder'] = round(calculate_angle(
                    [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y],
                    [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y],
                    [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                ), 2)
                angle_data['shoulder_diff'] = round((angle_data['right_shoulder'] - angle_data['left_shoulder']) ** 2, 2)
                angle_data['shoulder_warning'] = angle_data['shoulder_diff'] > 500
                angle_data['elbow_warning'] = (angle_data['right_shoulder'] > 80 or angle_data['left_shoulder'] > 80)
                #print(f"angle_data: {angle_data}")
        cv2.imshow("Camera View", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

@app.route('/angle')
def angle():
    import numpy as np
    def to_native(val):
        import numpy as np
        if val is None:
            return None
        if isinstance(val, np.generic):
            return float(val)
        if isinstance(val, (float, int)):
            return float(val)
        if isinstance(val, bool):
            return val
        return None
    with angle_data_lock:
        native_angle_data = {k: to_native(v) for k, v in angle_data.items()}
    return jsonify(native_angle_data)

@app.route('/summary')
def summary():
    #カメラからの情報結果
    angleresult = 0
    #肩の上げ具合
    angleresult = ((angle_data['left_shoulder']/150 * 100) + (angle_data['right_shoulder']/150 * 100))/2
    angleresult = min(angleresult, 99.99)
    #左右差の割合
    angleresult = ((angleresult)+((angle_data['left_shoulder']-angle_data['right_shoulder'])**2/(80**2)*100)+((angle_data['left_elbow']-angle_data['right_elbow'])**2/(80**2)*100))
    angleresult = min(angleresult, 99.99)
    #すべての要素の平均値を計算
    probability = (angleresult + 0)/1
    return jsonify({'explosion_probability': probability})

if __name__ == '__main__':
    t = threading.Thread(target=pose_thread, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000, debug=False)
