from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///memos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# メモモデル
class Memo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

# データベースの初期化
with app.app_context():
    db.create_all()

# メモの作成
@app.route('/api/memos', methods=['POST'])
def create_memo():
    data = request.get_json()
    new_memo = Memo(
        title=data['title'],
        content=data['content'],
    )
    db.session.add(new_memo)
    db.session.commit()
    return jsonify({
        "id": new_memo.id,
        "title": new_memo.title,
        "content": new_memo.content,
        "createdAt": new_memo.created_at,
        "updatedAt": new_memo.updated_at
    }), 201

# メモの取得
@app.route('/api/memos/<int:id>', methods=['GET'])
def get_memo(id):
    memo = Memo.query.get_or_404(id)
    return jsonify({
        "id": memo.id,
        "title": memo.title,
        "content": memo.content,
        "createdAt": memo.created_at,
        "updatedAt": memo.updated_at
    })

# メモの更新
@app.route('/api/memos/<int:id>', methods=['PUT'])
def update_memo(id):
    memo = Memo.query.get_or_404(id)
    data = request.get_json()
    memo.title = data['title']
    memo.content = data['content']
    db.session.commit()
    return jsonify({
        "id": memo.id,
        "title": memo.title,
        "content": memo.content,
        "createdAt": memo.created_at,
        "updatedAt": memo.updated_at
    })

# メモの削除
@app.route('/api/memos/<int:id>', methods=['DELETE'])
def delete_memo(id):
    memo = Memo.query.get_or_404(id)
    db.session.delete(memo)
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
