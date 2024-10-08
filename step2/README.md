# メモ管理APIシステム - ユーザー認証機能の追加と解説

このプロジェクトでは、前回のメモ管理APIに加えて、ユーザー認証機能を追加しました。このREADMEでは、ユーザー認証機能の実装方法や、初心者が理解しづらいポイントを解説します。

## 課題の概要

新たに追加された機能は以下の通りです：

1. **ユーザー登録**: 新しいユーザーをデータベースに登録します。
2. **ログイン**: 既存ユーザーの認証を行い、JWTトークンを発行します。
3. **認証付きメモ操作**: 認証されたユーザーのみがメモの作成、取得、更新、削除を行えます。

これにより、認証済みのユーザーのみが自分のメモを操作できるようになります。

## JWT認証の仕組み

### JWTとは？

JWT（JSON Web Token）は、認証情報を安全にやり取りするためのトークンフォーマットです。サーバーがユーザーを認証すると、JWTを生成してクライアントに渡します。このJWTは、ユーザーが後続のリクエストで自分を認証するために使用されます。

### JWTトークンの生成

JWTトークンは、ユーザーのIDなどの情報を含むペイロード部分と、署名部分から成り立っています。署名にはサーバーの秘密鍵が使われ、トークンの改ざんを防ぎます。

```
def create_token(user):
    payload = {
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow(),
        'sub': user.id
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
```

- **exp**: トークンの有効期限（ここでは1日）。
- **iat**: トークンが発行された時刻。
- **sub**: トークンのサブジェクト（ここではユーザーID）。

### JWTトークンの検証

クライアントがリクエストを送る際、JWTトークンをヘッダーに含めます。サーバーはそのトークンを検証し、ユーザーが認証されているか確認します。

```
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
```

このデコレータ関数 `token_required` は、JWTトークンを持たないリクエストや無効なトークンを持つリクエストを拒否し、認証済みのユーザーにのみ処理を許可します。

## 新しいエンドポイントの解説

### 1. ユーザー登録 (`/api/users/register`)

新しいユーザーを登録するエンドポイントです。ユーザー名が既に存在する場合、`409 Conflict` を返します。パスワードはハッシュ化されて保存されます。

```
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
```

### 2. ログイン (`/api/users/login`)

既存ユーザーがログインすると、JWTトークンが返されます。このトークンを使用して、後続のリクエストで自分を認証します。

```
@app.route('/api/users/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Login failed!'}), 401
    token = create_token(user)
    return jsonify({'token': token}), 200
```

### 3. 認証付きメモ操作

ユーザーの認証を要求するメモのCRUD操作です。各操作は `@token_required` デコレータを使用して保護されており、認証されていないリクエストは拒否されます。

- **メモの作成** (`/api/memos`)

```
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
```

- **メモの取得** (`/api/memos/<int:id>`)

```
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
```

- **メモの更新** (`/api/memos/<int:id>`)

```
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
```

- **メモの削除** (`/api/memos/<int:id>`)

```
@app.route('/api/memos/<int:id>', methods=['DELETE'])
@token_required
def delete_memo(current_user, id):
    memo = Memo.query.filter_by(id=id, user_id=current_user.id).first()
    if not memo:
        return jsonify({'message': 'Memo not found!'}), 404
    db.session.delete(memo)
    db.session.commit()
    return '', 204
```

## 注意点

### 1. **エンドポイントの衝突防止**

`token_required` デコレータを適用するとき、Flaskのエンドポイント名が重複してエラーが発生することがあります。この問題を回避するために、`functools.wraps` を使って元の関数名を保持するようにしています。

### 2. **トークンの有効期限**

トークンはデフォルトで1日間有効です。必要に応じて `exp`（有効期限）を調整することで、トークンの有効期間を変更できます。

### 3. **セキュリティ**

パスワードはハッシュ化して保存し、トークンは秘密鍵で署名されています。これにより、ユーザー情報が外部に漏れるリスクを低減しています。

## まとめ

このプロジェクトでは、メモ管理APIにユーザー認証機能を追加しました。JWTを使った認証システムにより、ユーザーごとのメモ操作が可能になりました。認証やセキュリティの基本を学ぶことができたかと思います。

このREADMEを参考にして、プロジェクトを理解し、さらなる開発に挑戦してください！
