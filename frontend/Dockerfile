# フロントエンドDockerfile
FROM node:20-alpine

WORKDIR /app

# パッケージファイルをコピー
COPY package*.json ./

# 依存関係インストール
RUN npm ci

# ソースコードをコピー
COPY . .

EXPOSE 5173

# 開発サーバー起動（host指定でコンテナ外からアクセス可能に）
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
