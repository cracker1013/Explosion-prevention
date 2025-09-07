from flask import Flask, jsonify
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

@app.route('/angle')
def angle():
    # 仮の値（実際はscan2.pyの計算結果を返す）
    return jsonify({
        'right_elbow': random.uniform(30, 150),
        'right_shoulder': random.uniform(30, 150),
        'left_elbow': random.uniform(30, 150),
        'left_shoulder': random.uniform(30, 150)
    })

@app.route('/summary')
def summary():
    # 仮の爆発確率（実際は各APIの値を集約して計算）
    probability = random.uniform(0, 1)
    return jsonify({'explosion_probability': probability})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
