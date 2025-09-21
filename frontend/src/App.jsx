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

  return (
    <div style={{height: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'center'}}>
      <h1 style={{fontSize: '3rem', marginTop: '15vh'}}>確率</h1>
      <div style={{fontSize: '2rem', margin: '2rem'}}>
        {summary ? `${summary.explosion_probability.toFixed(2)}%` : '---'}
      </div>
      <div style={{fontSize: '1.2rem'}}>
        {angles && (
          <>
            <div>右肘角度: {formatAngle(angles.right_elbow)}度</div>
            <div>右肩角度: {formatAngle(angles.right_shoulder)}度</div>
            <div>左肘角度: {formatAngle(angles.left_elbow)}度</div>
            <div>左肩角度: {formatAngle(angles.left_shoulder)}度</div>
            <div>笑顔度: {formatAngle(angles.smile_score)}</div>
            <div>怒り度: {formatAngle(angles.anger_score)}</div>
          </>
        )}
      </div>
    </div>
  );
}

export default App;
