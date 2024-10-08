# メモ管理APIシステム - タグ機能の追加と解説

このプロジェクトでは、メモにタグを追加し、タグを使ってメモをフィルタリングする機能を実装しました。このREADMEでは、タグ機能の実装方法や、初心者が理解しづらいポイントを解説します。

## 課題の概要

新たに追加された機能は以下の通りです：

1. **タグの作成**: 新しいタグをデータベースに追加します。
2. **メモにタグを追加**: 既存のメモにタグを関連付けます。
3. **タグでメモをフィルタリング**: 指定されたタグに関連付けられたメモを取得します。

これにより、メモにタグを付けて整理し、特定のタグに関連するメモのみをフィルタリングできるようになります。

## データベースモデルの設定

### 1. タグモデル (`Tag`)
タグを管理するためのテーブルです。`name` フィールドは一意で、重複するタグ名を防ぎます。

```
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
```

### 2. メモとタグの関係 (`MemoTag`)
メモとタグの多対多の関係を管理するための中間テーブルです。各行は、1つのメモと1つのタグを関連付けます。

```
class MemoTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    memo_id = db.Column(db.Integer, db.ForeignKey('memo.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=False)
```

### 3. メモモデルの変更 (`Memo`)
メモモデルにタグとの関係を追加しました。`secondary` 引数で中間テーブルを指定し、`backref` を使って逆方向のリレーションを定義します。

```
class Memo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tags = db.relationship('Tag', secondary='memo_tags', backref=db.backref('memos', lazy='dynamic'))
```

## 新しいエンドポイントの解説

### タグの作成 (`POST /api/tags`)
ユーザーが新しいタグを作成するエンドポイントです。タグ名が既に存在する場合、`409 Conflict` を返します。

```
@app.route('/api/tags', methods=['POST'])
@token_required
def create_tag(current_user):
    data = request.get_json()
    if Tag.query.filter_by(name=data['name']).first():
        return jsonify({'message': 'Tag already exists'}), 409
    new_tag = Tag(name=data['name'])
    db.session.add(new_tag)
    db.session.commit()
    return jsonify({
        'id': new_tag.id,
        'name': new_tag.name
    }), 201
```

### メモにタグを追加 (`POST /api/memos/<int:id>/tags`)
指定されたメモに既存のタグを追加します。タグが見つからない場合、`404 Not Found` を返します。

```
@app.route('/api/memos/<int:id>/tags', methods=['POST'])
@token_required
def add_tag_to_memo(current_user, id):
    memo = Memo.query.filter_by(id=id, user_id=current_user.id).first()
    if not memo:
        return jsonify({'message': 'Memo not found!'}), 404
    data = request.get_json()
    tag = Tag.query.get(data['tagId'])
    if not tag:
        return jsonify({'message': 'Tag not found!'}), 404
    if tag not in memo.tags:
        memo.tags.append(tag)
    db.session.commit()
    return jsonify({
        'id': memo.id,
        'title': memo.title,
        'content': memo.content,
        'tags': [{'id': tag.id, 'name': tag.name} for tag in memo.tags]
    }), 200
```

### タグでメモをフィルタリング (`GET /api/memos?tag=タグ名`)
指定されたタグ名でメモをフィルタリングし、そのタグが付けられたメモを返します。

```
@app.route('/api/memos', methods=['GET'])
@token_required
def get_memos_by_tag(current_user):
    tag_name = request.args.get('tag')
    if not tag_name:
        return jsonify({'message': 'Tag name is missing!'}), 400
    tag = Tag.query.filter_by(name=tag_name).first()
    if not tag:
        return jsonify({'message': 'Tag not found!'}), 404
    memos = Memo.query.filter(Memo.tags.contains(tag), Memo.user_id == current_user.id).all()
    return jsonify([{
        'id': memo.id,
        'title': memo.title,
        'content': memo.content,
        'tags': [{'id': t.id, 'name': t.name} for t in memo.tags]
    } for memo in memos]), 200
```

## 実装のポイント

- **多対多のリレーション**: メモとタグは多対多の関係にあるため、中間テーブル `memo_tags` を使用して関係を管理します。これにより、1つのメモに複数のタグを付けたり、1つのタグを複数のメモに関連付けたりすることができます。

- **認証の追加**: 各エンドポイントには、認証デコレータ `@token_required` を追加して、認証されたユーザーのみが操作できるようにしています。これにより、ユーザーのメモやタグのプライバシーが保護されます。

- **エラーハンドリング**: タグやメモが見つからない場合に適切なエラーメッセージとステータスコードを返すようにしています。例えば、タグが存在しない場合には `404 Not Found` を返し、クライアントに適切な対応を促します。

この実装により、メモにタグを追加し、タグでメモをフィルタリングする機能が実現できます。ユーザーはメモをタグで分類・整理し、特定のタグに関連するメモを素早く検索できるようになります。
