# xls2xlsx セキュリティ監査レポート

**監査実施日**: 2025-11-20  
**プロジェクトバージョン**: 1.0.0  
**監査者**: Automated Security Scanner

---

## 🔒 総合評価: 良好（一部改善推奨）

### スコア: 8.5/10

**主要セキュリティ項目:**
- ✅ 認証・認可: 良好
- ✅ 機密情報管理: 良好
- ⚠️ 入力検証: 改善推奨
- ✅ エラーハンドリング: 良好
- ⚠️ ファイル名サニタイズ: 改善推奨
- ✅ SASトークン管理: 良好

---

## ✅ セキュリティ強度（良好な項目）

### 1. 認証・認可 ✅

**HTTPトリガー認証設定:**
```json
"authLevel": "function"
```

- ✅ 関数キー認証が有効
- ✅ 匿名アクセス不可
- ✅ POSTメソッドのみ許可

**推奨事項:**
- Azure AD認証への移行を検討（エンタープライズ環境向け）
- IP制限の設定（本番環境）

### 2. 機密情報管理 ✅

**.gitignore設定:**
```
# Local settings (contains secrets)
local.settings.json
```

- ✅ `local.settings.json`がGit除外対象
- ✅ 接続文字列がソースコードにハードコードされていない
- ✅ 環境変数経由で取得: `os.environ.get('AzureWebJobsStorage')`

**現在の接続文字列管理:**
```python
connection_string = os.environ.get('AzureWebJobsStorage', 'UseDevelopmentStorage=true')
```

### 3. SASトークン管理 ✅

**有効期限設定:**
```python
expiry=datetime.utcnow() + timedelta(hours=1)
```

- ✅ 1時間の短い有効期限
- ✅ 読み取り専用権限: `BlobSasPermissions(read=True)`
- ✅ ローカル環境ではSAS生成をスキップ

### 4. エラーハンドリング ✅

**適切なエラーメッセージ:**
```python
except Exception as e:
    logging.error(f"変換エラー: {str(e)}")
    return func.HttpResponse(
        f"変換中にエラーが発生しました: {str(e)}",
        status_code=500
    )
```

- ✅ エラーログ記録
- ✅ 500エラーレスポンス
- ⚠️ 詳細なエラーメッセージ（本番環境では情報漏洩リスク）

### 5. ファイルサイズ制限 ✅

**最大リクエストサイズ:**
```json
"maxRequestBodySize": 209715200  // 200MB
```

- ✅ DoS攻撃対策として上限設定済み
- ✅ Azure Functionsの制限内（210MB）

---

## ⚠️ セキュリティリスク（改善推奨）

### 1. 入力検証の不足 ⚠️ 【中リスク】

**現在の実装:**
```python
file_data = req.get_body()
if not file_data:
    return func.HttpResponse(
        "リクエストボディにXLSファイルが含まれていません。",
        status_code=400
    )
```

**問題点:**
- ファイルサイズの検証なし（リクエストボディサイズのみ）
- ファイル形式の検証なし（マジックナンバーチェック不在）
- 悪意のあるファイルの検出機能なし

**推奨修正案:**
```python
# ファイルサイズ検証
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
if len(file_data) > MAX_FILE_SIZE:
    return func.HttpResponse(
        "ファイルサイズが上限を超えています（最大50MB）",
        status_code=413
    )

# XLS形式検証（マジックナンバー）
XLS_MAGIC = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
if not file_data[:8].startswith(b'\xd0\xcf\x11\xe0'):
    return func.HttpResponse(
        "有効なXLSファイルではありません",
        status_code=400
    )
```

### 2. ファイル名サニタイズの不足 ⚠️ 【中リスク】

**現在の実装:**
```python
filename = req.headers.get('X-Filename', 'converted')
if filename.lower().endswith('.xls'):
    filename = filename[:-4]
```

**問題点:**
- パストラバーサル攻撃の可能性: `../../etc/passwd.xls`
- 特殊文字の未検証
- ファイル名長の制限なし

**推奨修正案:**
```python
import re
import os.path

def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    ファイル名をサニタイズ
    
    Args:
        filename: 元のファイル名
        max_length: 最大文字数
        
    Returns:
        サニタイズされたファイル名
    """
    # パス区切り文字を除去
    filename = os.path.basename(filename)
    
    # 危険な文字を除去（英数字、ハイフン、アンダースコア、ドットのみ許可）
    filename = re.sub(r'[^\w\-.]', '_', filename)
    
    # 連続するドットを単一に
    filename = re.sub(r'\.+', '.', filename)
    
    # 先頭と末尾のドット・スペースを除去
    filename = filename.strip('. ')
    
    # 長さ制限
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    # 空の場合はデフォルト
    if not filename:
        filename = 'converted'
    
    return filename

# 使用例
filename = sanitize_filename(req.headers.get('X-Filename', 'converted'))
```

### 3. エラーメッセージの詳細化 ⚠️ 【低リスク】

**現在の実装:**
```python
return func.HttpResponse(
    f"変換中にエラーが発生しました: {str(e)}",
    status_code=500
)
```

**問題点:**
- 内部エラー詳細が外部に漏洩する可能性
- スタックトレース情報の漏洩リスク

**推奨修正案:**
```python
# 本番環境では詳細を隠す
is_production = os.environ.get('AZURE_FUNCTIONS_ENVIRONMENT') == 'Production'

if is_production:
    error_message = "ファイルの変換中にエラーが発生しました。"
else:
    error_message = f"変換中にエラーが発生しました: {str(e)}"

return func.HttpResponse(
    error_message,
    status_code=500
)
```

### 4. リソース制限 ⚠️ 【低リスク】

**現在の設定:**
```json
"functionTimeout": "00:05:00"
```

**推奨事項:**
- メモリ使用量のモニタリング設定
- 大容量ファイル処理時のタイムアウト調整
- 並列処理数の制限確認

---

## 🛡️ 追加セキュリティ推奨事項

### 1. セキュリティヘッダーの追加

```python
def add_security_headers(response: func.HttpResponse) -> func.HttpResponse:
    """セキュリティヘッダーを追加"""
    response.headers.update({
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'"
    })
    return response
```

### 2. レート制限の実装

本番環境では以下を検討：
- Azure API Managementでレート制限
- Application Gatewayでのトラフィック制御
- カスタムミドルウェアでのリクエスト制限

### 3. ログとモニタリング

**現在の実装:**
```python
logging.info('HTTP trigger function processed a request.')
logging.error(f"変換エラー: {str(e)}")
```

**推奨追加事項:**
- Application Insightsの有効化（本番環境）
- セキュリティイベントの記録
- 異常検知アラートの設定
- アクセスログの保存と監視

### 4. Blob Storage セキュリティ

**推奨設定:**
```python
# コンテナのパブリックアクセスを無効化
container_client.set_container_access_policy(
    signed_identifiers={},
    public_access=None  # プライベート
)

# HTTPS強制
blob_service_client = BlobServiceClient.from_connection_string(
    connection_string,
    require_encryption=True
)
```

---

## 📋 セキュリティチェックリスト

### 実装済み ✅

- [x] 関数キー認証有効
- [x] 機密情報のGit除外
- [x] SASトークン期限設定（1時間）
- [x] 読み取り専用SAS権限
- [x] エラーハンドリング実装
- [x] ファイルサイズ上限設定
- [x] ログ記録実装
- [x] POSTメソッド限定

### 要改善 ⚠️

- [ ] ファイル形式検証（マジックナンバー）
- [ ] ファイル名サニタイズ
- [ ] ファイルサイズの個別検証
- [ ] 本番環境でのエラーメッセージ制御
- [ ] セキュリティヘッダーの追加

### 推奨（本番環境） 📌

- [ ] Azure AD認証への移行
- [ ] IP制限の設定
- [ ] Application Insights有効化
- [ ] レート制限の実装
- [ ] セキュリティスキャンの定期実行
- [ ] 脆弱性診断の実施
- [ ] アンチマルウェアスキャン

---

## 🔍 依存パッケージのセキュリティ

### 使用パッケージ

```txt
azure-functions
pandas
openpyxl
xlrd
azure-storage-blob
```

**推奨事項:**
- 定期的な脆弱性スキャン（`pip-audit`、`safety`）
- パッケージの最新版への更新
- セキュリティアドバイザリの監視

**スキャンコマンド:**
```bash
# pip-auditのインストールと実行
pip install pip-audit
pip-audit

# safetyのインストールと実行
pip install safety
safety check
```

---

## 🚨 既知の脆弱性

### xlrd パッケージ

**注意事項:**
- xlrd 2.0以降は`.xls`形式のみサポート
- `.xlsx`ファイルのサポート終了（セキュリティ向上）
- 旧バージョンには脆弱性の可能性

**現在の使用:** ✅ 適切（.xls専用として使用）

---

## 📝 セキュリティ改善計画

### Phase 1: 即時対応（優先度：高）

1. **ファイル名サニタイズの実装**
   - パストラバーサル対策
   - 特殊文字の除去

2. **ファイル形式検証の追加**
   - マジックナンバーチェック
   - ファイルサイズ個別検証

### Phase 2: 短期対応（1-2週間）

3. **エラーメッセージの改善**
   - 本番/開発環境の分離
   - 詳細情報の隠蔽

4. **セキュリティヘッダーの追加**
   - 標準的なセキュリティヘッダー実装

### Phase 3: 中期対応（1ヶ月）

5. **モニタリングとログの強化**
   - Application Insights統合
   - セキュリティイベント記録

6. **依存パッケージの監査**
   - 自動スキャンの設定
   - 定期更新プロセス

### Phase 4: 長期対応（本番運用時）

7. **認証強化**
   - Azure AD統合
   - IP制限設定

8. **レート制限**
   - API Management導入検討

---

## 🎯 セキュリティ実装例

実装サンプルファイルを作成：

```bash
# セキュリティ強化版の実装例
# convert_http/security_utils.py
```

---

## 📞 セキュリティインシデント対応

### 発見した場合の対応手順

1. **即座に対応**
   - 該当機能の無効化
   - アクセスログの確認

2. **影響範囲の調査**
   - 不正アクセスの有無
   - データ漏洩の確認

3. **修正とデプロイ**
   - セキュリティパッチ適用
   - 緊急デプロイ

4. **報告**
   - 管理者への報告
   - 必要に応じて関係者へ通知

---

## ✅ 結論

### 総合評価: 良好（8.5/10）

xls2xlsxプロジェクトは基本的なセキュリティ要件を満たしていますが、以下の改善を推奨します：

**優先度 高:**
1. ファイル名サニタイズの実装
2. ファイル形式検証の追加

**優先度 中:**
3. エラーメッセージの本番環境対応
4. セキュリティヘッダーの追加

**優先度 低（本番環境で必須）:**
5. Application Insightsの統合
6. IP制限とレート制限
7. Azure AD認証への移行

現状でも**開発・テスト環境としては十分なセキュリティレベル**ですが、
**本番環境へのデプロイ前に優先度高の項目の対応を強く推奨**します。

---

**次回監査予定**: 2025-12-20  
**監査責任者**: Security Team  
**承認者**: Project Manager
