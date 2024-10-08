from flask import Flask, request, jsonify, abort, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
import os
import functools

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///memos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)

# ユーザーモデル
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# メモモデル
class Memo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# データベースの初期化
with app.app_context():
    db.create_all()

# JWTトークンを生成する関数
def create_token(user):
    payload = {
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow(),
        'sub': user.id
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

# JWTトークンを検証するデコレータ
def token_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(" ")[1]  # "Bearer <token>" の形式を処理
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['sub'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated_function

# ユーザー登録
@app.route('/api/users/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 409
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({
        'id': new_user.id,
        'username': new_user.username
    }), 201

# ログイン
@app.route('/api/users/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Login failed!'}), 401
    token = create_token(user)
    return jsonify({'token': token}), 200

# メモの作成
@app.route('/api/memos', methods=['POST'])
@token_required
def create_memo(current_user):
    data = request.get_json()
    new_memo = Memo(
        title=data['title'],
        content=data['content'],
        user_id=current_user.id
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
@token_required
def get_memo(current_user, id):
    memo = Memo.query.filter_by(id=id, user_id=current_user.id).first()
    if not memo:
        return jsonify({'message': 'Memo not found!'}), 404
    return jsonify({
        "id": memo.id,
        "title": memo.title,
        "content": memo.content,
        "createdAt": memo.created_at,
        "updatedAt": memo.updated_at
    })

# メモの更新
@app.route('/api/memos/<int:id>', methods=['PUT'])
@token_required
def update_memo(current_user, id):
    memo = Memo.query.filter_by(id=id, user_id=current_user.id).first()
    if not memo:
        return jsonify({'message': 'Memo not found!'}), 404
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
@token_required
def delete_memo(current_user, id):
    memo = Memo.query.filter_by(id=id, user_id=current_user.id).first()
    if not memo:
        return jsonify({'message': 'Memo not found!'}), 404
    db.session.delete(memo)
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
