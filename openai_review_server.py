import os
import openai
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

USE_FAKE_OPENAI = False  # Trueでテスト用総評、FalseでOpenAI API
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/review', methods=['POST'])
def review():
    # 角度・表情・加速度などをPOSTで受け取る
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
    # 環境変数USE_FAKE_OPENAIがtrueなら仮アドバイスを返す
    if USE_FAKE_OPENAI:
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
