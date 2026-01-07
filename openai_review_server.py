import os

import openai
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

app = Flask(__name__)
CORS(app)

# 設定値
USE_FAKE_OPENAI = os.getenv('USE_FAKE_OPENAI', 'false').lower() == 'true'
REVIEW_SERVER_PORT = int(os.getenv('REVIEW_SERVER_PORT', '5001'))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# OpenAIクライアント初期化
client = openai.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

@app.route('/review', methods=['POST'])
def review():
    """姿勢・表情データを基にAI総評を生成する"""
    data = request.json
    advices = data.get('advices', [])
    advices_text = '\n'.join(advices) if advices else '（アドバイスなし）'
    
    prompt = f"""
You're a versatile advisor.
Evaluate the data and offer advice in 130 Japanese characters.
Speak with emotional urgency.If it's safe, say it's safe, but if it's not, get impatient.
右肘角度: {data.get('right_elbow')}
右肩角度: {data.get('right_shoulder')}
左肘角度: {data.get('left_elbow')}
左肩角度: {data.get('left_shoulder')}
笑顔度: {data.get('smile_score')}
加速度: {data.get('accel')}
爆発確率: {data.get('explosion_probability')}
現在のアドバイス一覧:\n{advices_text}
"""
    # フェイクモードまたはAPIキーがない場合
    if USE_FAKE_OPENAI or client is None:
        advice = "【テスト用総評】爆発確率や加速度、表情・姿勢に注意してください。安全第一で！"
        return jsonify({'review': advice})
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        result = response.choices[0].message.content
        return jsonify({'review': result})
    except Exception as e:
        return jsonify({'review': f'エラー: {str(e)}'}), 500


@app.route('/health', methods=['GET'])
def health():
    """ヘルスチェック用エンドポイント"""
    return jsonify({'status': 'ok', 'fake_mode': USE_FAKE_OPENAI})


if __name__ == '__main__':
    print(f"Starting review server on port {REVIEW_SERVER_PORT}")
    print(f"Fake OpenAI mode: {USE_FAKE_OPENAI}")
    app.run(host='0.0.0.0', port=REVIEW_SERVER_PORT, debug=True)
