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
    if (summary.explosion_probability < 30) {
      advices.push('世界滅亡の危機です。アドバイス');
    } else if (summary.explosion_probability >= 50) {
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
    // 肩・肘
    if (angles.right_shoulder > 80 || angles.left_shoulder > 80) {
      advices.push('肩の角度が高いです。リラックスしましょう。');
    }
    if (angles.right_elbow > 120 || angles.left_elbow > 120) {
      advices.push('肘の角度が大きいです。腕を下げてみましょう。');
    }
    return advices;
  };

  const advices = getAdvice();

  return (
    <div style={{height: '100vh', display: 'flex', flexDirection: 'row', justifyContent: 'center', alignItems: 'center'}}>
      {/* 中央：確率・値一覧 */}
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '340px'}}>
        <h1 style={{fontSize: '3rem', marginBottom: '2vh'}}>確率</h1>
        <div style={{fontSize: '2rem', margin: '2rem'}}>
          {summary ? `${summary.explosion_probability.toFixed(2)}%` : '---'}
        </div>
  <div style={{fontSize: '1.7rem', marginBottom: '2vh'}}>
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
      </div>
      {/* 右側：アドバイス一覧を一つの吹き出しにまとめて表示 */}
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start', marginLeft: '4vw', minWidth: '320px'}}>
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
    </div>
  );
}

export default App;
