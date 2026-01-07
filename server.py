import os
import json
import threading

import cv2
import mediapipe as mp
import numpy as np
import serial
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

app = Flask(__name__)
CORS(app)

# 設定値
SERIAL_PORT = os.getenv('SERIAL_PORT', 'COM3')
SERIAL_BAUD_RATE = int(os.getenv('SERIAL_BAUD_RATE', '115200'))
CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', '0'))
POSE_SERVER_PORT = int(os.getenv('POSE_SERVER_PORT', '5000'))
SIMULATION_MODE = os.getenv('SIMULATION_MODE', 'false').lower() == 'true'

# シリアルポート初期化（シミュレーションモード時はスキップ）
ser = None
mpu_data = {}
if not SIMULATION_MODE:
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD_RATE, timeout=1)
        print(f"Connected to serial port: {SERIAL_PORT}")
    except serial.SerialException:
        print(f"Warning: Could not open serial port {SERIAL_PORT}. MPU data will be unavailable.")

# グローバル変数で最新の角度を保持
angle_data = {
    'right_elbow': None,
    'right_shoulder': None,
    'left_elbow': None,
    'left_shoulder': None,
    'shoulder_diff': None,
    'shoulder_warning': False,
    'elbow_warning': False,
    'accel': None
}

angle_data_lock = threading.Lock()


def read_mpu_thread():
    """MPU加速度センサーからデータを読み取るスレッド"""
    global mpu_data
    import time
    while True:
        if ser is None:
            time.sleep(1)
            continue
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                try:
                    mpu_data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                with angle_data_lock:
                    if all(k in mpu_data for k in ['ax', 'ay', 'az']):
                        try:
                            a = (mpu_data['ax']**2 + mpu_data['ay']**2 + mpu_data['az']**2) ** 0.5
                            angle_data['accel'] = round(a, 2)
                        except Exception:
                            angle_data['accel'] = None
                    else:
                        angle_data['accel'] = None
        except Exception:
            pass
        time.sleep(0.1)


def calculate_angle(a, b, c):
    """3点から角度を計算する"""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)
    return np.degrees(angle)


def pose_thread():
    """姿勢推定・表情解析を行うメインスレッド"""
    import time
    import random
    
    # シミュレーションモード: ハードウェアなしでランダムデータを生成
    if SIMULATION_MODE:
        print("Running in SIMULATION MODE - generating random data")
        while True:
            with angle_data_lock:
                angle_data['right_elbow'] = round(random.uniform(80, 150), 2)
                angle_data['right_shoulder'] = round(random.uniform(20, 80), 2)
                angle_data['left_elbow'] = round(random.uniform(80, 150), 2)
                angle_data['left_shoulder'] = round(random.uniform(20, 80), 2)
                angle_data['shoulder_diff'] = round((angle_data['right_shoulder'] - angle_data['left_shoulder']) ** 2, 2)
                angle_data['shoulder_warning'] = angle_data['shoulder_diff'] > 500
                angle_data['elbow_warning'] = (angle_data['right_shoulder'] > 80 or angle_data['left_shoulder'] > 80)
                angle_data['smile_score'] = round(random.uniform(30, 90), 2)
                angle_data['accel'] = round(random.uniform(900, 1100), 2)
            time.sleep(0.5)
        return
    
    # 通常モード: カメラ + MediaPipe
    try:
        mp_pose = mp.solutions.pose
        mp_face_mesh = mp.solutions.face_mesh
        pose = mp_pose.Pose()
        face_mesh = mp_face_mesh.FaceMesh()
    except AttributeError as e:
        print(f"MediaPipe initialization error: {e}")
        print("Falling back to SIMULATION MODE")
        while True:
            with angle_data_lock:
                angle_data['right_elbow'] = round(random.uniform(80, 150), 2)
                angle_data['right_shoulder'] = round(random.uniform(20, 80), 2)
                angle_data['left_elbow'] = round(random.uniform(80, 150), 2)
                angle_data['left_shoulder'] = round(random.uniform(20, 80), 2)
                angle_data['smile_score'] = round(random.uniform(30, 90), 2)
            time.sleep(0.5)
        return
    
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"Warning: Could not open camera {CAMERA_INDEX}. Falling back to SIMULATION MODE")
        while True:
            with angle_data_lock:
                angle_data['right_elbow'] = round(random.uniform(80, 150), 2)
                angle_data['right_shoulder'] = round(random.uniform(20, 80), 2)
                angle_data['left_elbow'] = round(random.uniform(80, 150), 2)
                angle_data['left_shoulder'] = round(random.uniform(20, 80), 2)
                angle_data['smile_score'] = round(random.uniform(30, 90), 2)
            time.sleep(0.5)
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)
        face_results = face_mesh.process(rgb_frame)
        # ...MPU値取得は専用スレッドで実施...
        # 表情スコア計算
        def get_smile_anger_score(face_landmarks):
            # 使用するランドマーク
            LEFT_BROW_END = 46
            RIGHT_BROW_END = 276
            LEFT_BROW_START = 75  # 眉頭をより内側（顔中心寄り）
            RIGHT_BROW_START = 295
            UPPER_LIP_CENTER = 13
            LOWER_LIP_CENTER = 14
            LEFT_MOUTH = 61
            RIGHT_MOUTH = 291
            NOSE = 1
            BETWEEN_EYES = 168
            try:
                # 眉尻・眉頭・鼻・目と目の間
                left_brow_end = face_landmarks.landmark[LEFT_BROW_END]
                right_brow_end = face_landmarks.landmark[RIGHT_BROW_END]
                left_brow_start = face_landmarks.landmark[LEFT_BROW_START]
                right_brow_start = face_landmarks.landmark[RIGHT_BROW_START]
                nose = face_landmarks.landmark[NOSE]
                between_eyes = face_landmarks.landmark[BETWEEN_EYES]
                # 唇中心・口角
                upper_lip = face_landmarks.landmark[UPPER_LIP_CENTER]
                lower_lip = face_landmarks.landmark[LOWER_LIP_CENTER]
                left_mouth = face_landmarks.landmark[LEFT_MOUTH]
                right_mouth = face_landmarks.landmark[RIGHT_MOUTH]
                # 口の開き　0～0.03
                mouth_open = abs(upper_lip.y - lower_lip.y)
                mouth_open = max(0, min(mouth_open, 0.03))
                #print(f"mouth_open: {mouth_open}", end="")

                # 口端の高さ（口端が口中心より上なら＋）0～0.02
                left_mouth_height = (upper_lip.y + lower_lip.y) / 2 - left_mouth.y
                right_mouth_height = (upper_lip.y + lower_lip.y) / 2 - right_mouth.y
                mouth_corner_up = (left_mouth_height + right_mouth_height) / 2
                mouth_corner_up = max(0, min(mouth_corner_up, 0.02))
                #print(f"mouth_corner_up: {mouth_corner_up}", end="")
                # スコア計算（顔の近さバイアスなし）両値とも0.3,0.7に近づける
                smile_score = (mouth_open * 15 + mouth_corner_up * 50) * 100
                smile_score = max(0, min(smile_score, 100))
                # 怒り度判定は廃止
                return smile_score, None
            except Exception:
                return None, None
        smile_score, _ = None, None
        if face_results.multi_face_landmarks:
            smile_score, _ = get_smile_anger_score(face_results.multi_face_landmarks[0])
        with angle_data_lock:
            angle_data['smile_score'] = smile_score
            #print(f"smile_score: {smile_score}")
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
        # 顔ランドマークの主要点をプロット（眉尻はより外側: 左52, 右282／眉頭はそのまま: 左65, 右295）
        if face_results.multi_face_landmarks:
            face_landmarks = face_results.multi_face_landmarks[0]
            h, w = frame.shape[:2]
            # 眉尻（左: 46, 右: 276）赤
            for idx in [46, 276]:
                x = int(face_landmarks.landmark[idx].x * w)
                y = int(face_landmarks.landmark[idx].y * h)
                cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
            # 眉頭（左: 107, 右: 336）ピンク（より上側に修正）
            for idx in [107, 336]:
                x = int(face_landmarks.landmark[idx].x * w)
                y = int(face_landmarks.landmark[idx].y * h)
                cv2.circle(frame, (x, y), 5, (255, 0, 255), -1)
            # 上唇中心（13）青
            x = int(face_landmarks.landmark[13].x * w)
            y = int(face_landmarks.landmark[13].y * h)
            cv2.circle(frame, (x, y), 5, (255, 0, 0), -1)
            # 下唇中心（14）水色
            x = int(face_landmarks.landmark[14].x * w)
            y = int(face_landmarks.landmark[14].y * h)
            cv2.circle(frame, (x, y), 5, (0, 255, 255), -1)
            # 唇右（右口角: 291）緑
            x = int(face_landmarks.landmark[291].x * w)
            y = int(face_landmarks.landmark[291].y * h)
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
            # 唇左（左口角: 61）黄
            x = int(face_landmarks.landmark[61].x * w)
            y = int(face_landmarks.landmark[61].y * h)
            cv2.circle(frame, (x, y), 5, (255, 255, 0), -1)
            # 鼻（1）オレンジ
            x = int(face_landmarks.landmark[1].x * w)
            y = int(face_landmarks.landmark[1].y * h)
            cv2.circle(frame, (x, y), 5, (0, 128, 255), -1)
            # 目頭（左: 133, 右: 362）青紫
            for idx in [133, 362]:
                x = int(face_landmarks.landmark[idx].x * w)
                y = int(face_landmarks.landmark[idx].y * h)
                cv2.circle(frame, (x, y), 5, (128, 0, 255), -1)
            # 目と目の間（168）紫
            x = int(face_landmarks.landmark[168].x * w)
            y = int(face_landmarks.landmark[168].y * h)
            cv2.circle(frame, (x, y), 5, (128, 0, 128), -1)
        cv2.imshow("Camera View", frame)
        # ...顔ランドマークの主要点プロットは上記で実施済み...
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
    left = angle_data['left_shoulder']
    right = angle_data['right_shoulder']
    left_elbow = angle_data['left_elbow']
    right_elbow = angle_data['right_elbow']
    # Noneチェック
    if None in [left, right, left_elbow, right_elbow]:
        return jsonify({'explosion_probability': None})
    #カメラからの情報結果
    angleresult = 0
    #肩の上げ具合
    angleresult = ((angle_data['left_shoulder']/150 * 100) + (angle_data['right_shoulder']/150 * 100))/2
    angleresult = min(angleresult, 99.99)
    #左右差の割合
    angleresult = ((angleresult)+((angle_data['left_shoulder']-angle_data['right_shoulder'])**2/(80**2)*100)+((angle_data['left_elbow']-angle_data['right_elbow'])**2/(80**2)*100))
    angleresult = min(angleresult, 99.99)
    #すべての要素の平均値を計算（肩・肘・笑顔度）
    with angle_data_lock:
        smile_score = angle_data.get('smile_score')
    values = [angleresult]
    if smile_score is not None:
        smile_inverse = 100 - smile_score
        values.append(smile_inverse)
    probability = sum(values) / len(values)
    return jsonify({'explosion_probability': probability})

if __name__ == '__main__':
    print(f"Starting pose server on port {POSE_SERVER_PORT}")
    print(f"Camera index: {CAMERA_INDEX}")
    print(f"Serial port: {SERIAL_PORT} (baud: {SERIAL_BAUD_RATE})")
    
    t_pose = threading.Thread(target=pose_thread, daemon=True)
    t_pose.start()
    t_mpu = threading.Thread(target=read_mpu_thread, daemon=True)
    t_mpu.start()
    app.run(host='0.0.0.0', port=POSE_SERVER_PORT, debug=False)
