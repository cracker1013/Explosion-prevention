# 🍟 袋菓子爆発防止アプリ (Explosion Prevention)

開封時の飛び散り、もう心配なし！姿勢も心も整えるスマート開封トレーナー。

本アプリは、急いで、または力強く袋菓子を開封した際に発生する中身の飛び散りを未然に防ぎ、開封動作を最適化するための総合トレーニングアプリです。

カメラを通じて、ユーザーの開封動作だけでなく、開封時の姿勢（肘の上がり具合、左右対称性）や表情までを詳細に解析。力の入れすぎや急激な動き、さらには不適切な姿勢やストレスの兆候までを検知し、安全かつスマートな開封方法を学習・習得することを目的としています。

## 📦 アーキテクチャ

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│   Pose Server   │────▶│  Review Server  │
│  (React/Vite)   │     │   (Flask/5000)  │     │  (Flask/5001)   │
│    :5173        │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └────────┬────────┘
                                 │                       │
                         ┌───────▼───────┐       ┌───────▼───────┐
                         │    Camera     │       │   OpenAI API  │
                         │  + MediaPipe  │       │               │
                         └───────────────┘       └───────────────┘
                                 │
                         ┌───────▼───────┐
                         │ Arduino/MPU   │
                         │  (加速度)     │
                         └───────────────┘
```

## 🚀 クイックスタート

### 前提条件
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (オプション)
- Webカメラ
- Arduino + MPUセンサー (オプション)

### 1. リポジトリをクローン
```bash
git clone https://github.com/cracker1013/Explosion-prevention.git
cd Explosion-prevention
git checkout develop
```

### 2. 環境変数を設定
```bash
cp .env.example .env
# .envファイルを編集してOPENAI_API_KEYを設定
```

### 3. 起動方法

#### 方法A: ローカル実行（カメラ映像 + 姿勢推定表示）

> ⚠️ **重要**: MediaPipeはWindowsで日本語（非ASCII）パスを処理できません。  
> プロジェクトを **英語のみのパス** （例: `C:\pose_app`）に配置してください。

**セットアップ:**
```powershell
# 1. 英語のみのパスにディレクトリを作成
New-Item -ItemType Directory -Path "C:\pose_app" -Force

# 2. 必要なファイルをコピー
Copy-Item server.py, .env, requirements.txt -Destination "C:\pose_app\"
Copy-Item -Recurse backend -Destination "C:\pose_app\"

# 3. Python 3.11で仮想環境を作成
py -3.11 -m venv "C:\pose_app\.venv"

# 4. 依存パッケージをインストール
& "C:\pose_app\.venv\Scripts\python.exe" -m pip install -r "C:\pose_app\requirements.txt"
```

**実行:**
```powershell
Set-Location "C:\pose_app"
& "C:\pose_app\.venv\Scripts\python.exe" server.py
```

カメラ映像ウィンドウ「Camera View」が表示され、姿勢のランドマークがプロットされます。  
終了するには `q` キーを押してください。

#### 方法B: Docker実行（シミュレーションモード）

**バックエンド:**
```bash
pip install -r requirements.txt
python server.py          # 姿勢推定サーバー (port 5000)
python openai_review_server.py  # レビューサーバー (port 5001)
```

**フロントエンド:**
```bash
cd frontend
npm install
npm run dev               # 開発サーバー (port 5173)
```

#### 方法C: Docker Compose（GUI無し・API提供のみ）
```bash
docker-compose up --build
```

> Docker内ではカメラ映像ウィンドウは表示されません（シミュレーションモードで動作）。

### 4. アクセス
ブラウザで `http://localhost:5173` を開く

## 📁 プロジェクト構成

```
Explosion-prevention/
├── server.py              # メインAPI: 姿勢推定 + MPUセンサー (port 5000)
├── openai_review_server.py # OpenAI総評API (port 5001)
├── requirements.txt       # Python依存関係
├── .env.example           # 環境変数テンプレート
├── docker-compose.yml     # Docker構成
├── Dockerfile.pose        # 姿勢サーバー用Dockerfile
├── Dockerfile.review      # レビューサーバー用Dockerfile
├── frontend/              # React フロントエンド
│   ├── src/
│   │   ├── App.jsx        # メインコンポーネント
│   │   └── App.css        # スタイル
│   ├── Dockerfile
│   └── package.json
└── backend/               # バックエンドパッケージ（将来拡張用）
```

## 🔧 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `OPENAI_API_KEY` | OpenAI APIキー | なし |
| `USE_FAKE_OPENAI` | テストモード（APIを使わない） | `false` |
| `POSE_SERVER_PORT` | 姿勢サーバーのポート | `5000` |
| `REVIEW_SERVER_PORT` | レビューサーバーのポート | `5001` |
| `FRONTEND_PORT` | フロントエンドのポート | `5173` |
| `SERIAL_PORT` | Arduinoシリアルポート | `COM3` |
| `SERIAL_BAUD_RATE` | シリアル通信速度 | `115200` |
| `CAMERA_INDEX` | カメラデバイス番号 | `0` |

## 🎮 使い方

1. アプリを起動してカメラの前に立つ
2. 袋菓子を開封するポーズをとる
3. リアルタイムで以下が表示される：
   - **爆発確率**: 0-100%で安全度を表示
   - **姿勢角度**: 肩・肘の角度
   - **笑顔度**: 表情の緊張度
   - **加速度**: 動きの激しさ（MPUセンサー使用時）
4. **スペースキー**を押すとAI総評を取得

## 🔬 技術スタック

- **Frontend**: React 19, Vite 7
- **Backend**: Flask, Flask-CORS
- **AI/ML**: MediaPipe (姿勢推定・顔認識), OpenAI API
- **Hardware**: Arduino, MPU6050 (加速度センサー)
- **Container**: Docker, Docker Compose

## 📝 ライセンス

MIT License

## 🤝 貢献

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
