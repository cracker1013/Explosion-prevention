import { useEffect, useState } from 'react';
import './App.css';

function App() {
  const [summary, setSummary] = useState(null);
  const [angles, setAngles] = useState(null);
  const [accel, setAccel] = useState('---');
  const [accelAdvice, setAccelAdvice] = useState(false);
  const [review, setReview] = useState('');

  // MPU加速度のみ0.1秒ごとに取得
  useEffect(() => {
    const fetchAccel = () => {
      fetch('http://127.0.0.1:5000/angle')
        .then(res => res.json())
        .then(data => {
          if (data.accel !== undefined && data.accel !== null) {
            const accelValue = Math.max(Math.floor(Number(data.accel) / 100) - 100, 0);
            setAccel(accelValue);
            // 加速度が300を超えたら1秒間アドバイス表示
            if (accelValue > 300) {
              setAccelAdvice(true);
              setTimeout(() => setAccelAdvice(false), 2000);
            }
          } else {
            setAccel('---');
          }
        });
    };
    fetchAccel();
    const interval = setInterval(fetchAccel, 100);
    return () => clearInterval(interval);
  }, []);

  // 角度・確率は従来通り0.5秒ごと
  useEffect(() => {
    const fetchData = () => {
      fetch('http://127.0.0.1:5000/summary')
        .then(res => res.json())
        .then(data => setSummary(data));
      fetch('http://127.0.0.1:5000/angle')
        .then(res => res.json())
        .then(data => setAngles(data));
    };
    fetchData();
    const interval = setInterval(fetchData, 500);
    return () => clearInterval(interval);
  }, []);

  const formatAngle = (value) => {
    if (value == null || isNaN(Number(value))) return '---';
    return Number(value).toFixed(1);
  };

  // アドバイス生成関数
  const getAdvice = () => {
    if (!summary || !angles) return null;
    const advices = [];

    // 爆発確率
    if (summary.explosion_probability >= 90) {
      advices.push('世界の危機。どうか落ち着いてください。');
    } else if (summary.explosion_probability < 50 && summary.explosion_probability >= 15) {
      advices.push('もう少し確率を下げるための行動をしてください。');
    } else {
      advices.push('安全です。皆さん期待してください。');
    }
    // 笑顔度
    if (angles.smile_score < 30) {
      advices.push('表情が硬いです。もっと笑顔を見せてください。。');
    }
    else if (angles.smile_score >= 30 && angles.smile_score < 70) {
      advices.push('良い笑顔になってきました。世界平和のためにはまだ笑顔になれます。');
    }
    else if (angles.smile_score >= 70) {
      advices.push('明らかな笑顔ですね！世界が安全になりました！');
    }
    // 肩の左右差
    if (
      angles.right_shoulder !== null && angles.left_shoulder !== null &&
      Math.abs(Number(angles.right_shoulder) - Number(angles.left_shoulder)) > 20
    ) {
      advices.push('左右の腕がアンバランスです。揃えましょう。');
    }
    // 肩の上げ具合
    if (
      angles.right_shoulder > 80 || angles.left_shoulder > 80
    ) {
      advices.push('気張りすぎです。肩を下げましょう');
    }
    return advices;
  };

  const advices = getAdvice();
  // 加速度アドバイスを追加
  if (accelAdvice) {
    advices.push('落ち着いてください！もう少しゆっくり引きましょう。');
  }

  // スペースキーでOpenAI総評取得
  useEffect(() => {
    const handleSpace = (e) => {
      if (e.code === 'Space') {
        if (!summary || !angles) return;
        const payload = {
          right_elbow: angles.right_elbow,
          right_shoulder: angles.right_shoulder,
          left_elbow: angles.left_elbow,
          left_shoulder: angles.left_shoulder,
          smile_score: angles.smile_score,
          accel: angles.accel,
          explosion_probability: summary.explosion_probability,
          advices: advices // 現在表示しているアドバイス一覧も送信
        };
        fetch('http://127.0.0.1:5001/review', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
          .then(res => res.json())
          .then(data => {
            setReview(data.review || '');
          })
          .catch(() => setReview('総評取得エラー'));
      }
    };
    window.addEventListener('keydown', handleSpace);
    return () => window.removeEventListener('keydown', handleSpace);
  }, [summary, angles, advices]);

  return (
    <div style={{height: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center'}}>
      <h1 style={{fontSize: '3rem', marginBottom: '0vh'}}>確率</h1>
      <div style={{fontSize: '2.4rem', margin: '1rem'}}>
        {accelAdvice ? '100.00%' : (summary ? `${summary.explosion_probability.toFixed(2)}%` : '---')}
      </div>
      <div style={{fontSize: '1.8rem', marginBottom: '2vh'}}>
        {angles && (
          <>
            <div>右肘角度: {formatAngle(angles.right_elbow)}度</div>
            <div>右肩角度: {formatAngle(angles.right_shoulder)}度</div>
            <div>左肘角度: {formatAngle(angles.left_elbow)}度</div>
            <div>左肩角度: {formatAngle(angles.left_shoulder)}度</div>
            <div>笑顔度: {formatAngle(angles.smile_score)}</div>
          </>
        )}
        <div>MPU加速度: {accel}</div>
      </div>
      {/* アドバイス一覧を値項目の下に表示 */}
      {advices && advices.length > 0 && (
        <div className="advice-balloon">
          <ul style={{margin: 0, paddingLeft: '1.2em'}}>
            {advices.map((advice, idx) => (
              <li key={idx} style={{marginBottom: '0.7em'}}>{advice}</li>
            ))}
          </ul>
        </div>
      )}
      {/* 総評表示 */}
      <div style={{marginTop: '2rem', fontSize: '1.5rem', color: '#333', maxWidth: '600px', textAlign: 'center'}}>
        {review && (
          <div>OpenAI総評: {review}</div>
        )}
      </div>
    </div>
  );
}

export default App;
