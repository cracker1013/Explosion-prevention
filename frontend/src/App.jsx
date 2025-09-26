import { useEffect, useState } from 'react';
import './App.css';

function App() {
  const [summary, setSummary] = useState(null);
  const [angles, setAngles] = useState(null);

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
      advices.push('世界の危機。落ち着いてください。');
    } else if (summary.explosion_probability < 50 && summary.explosion_probability >= 15) {
      advices.push('注意：肩や肘の角度、笑顔度を意識しましょう。');
    } else {
      advices.push('安全です。今の状態をキープしましょう。');
    }
    // 笑顔度
    if (angles.smile_score < 30) {
      advices.push('表情が硬い状況です。あなたの笑顔を観たいです。');
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
      advices.push('肩の左右差が大きいです。両肩の高さを揃えるよう意識しましょう。');
    }
    // 肩の上げ具合
    if (
      angles.right_shoulder > 80 || angles.left_shoulder > 80
    ) {
      advices.push('肩の角度が高いです。肩を下げてリラックスしましょう。');
    }
    return advices;
  };

  const advices = getAdvice();

  return (
    <div style={{height: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center'}}>
      <h1 style={{fontSize: '3rem', marginBottom: '2vh'}}>確率</h1>
      <div style={{fontSize: '2rem', margin: '2rem'}}>
        {summary ? `${summary.explosion_probability.toFixed(2)}%` : '---'}
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
    </div>
  );
}

export default App;
