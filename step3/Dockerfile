# Pythonベースのイメージを使用
FROM python:3.9-slim

# 作業ディレクトリを作成
WORKDIR /app

# アプリケーションの依存関係をインストール
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードをコピー
COPY . .

# ポート5000を公開
EXPOSE 5000

# アプリケーションを起動
CMD ["python", "app.py"]
