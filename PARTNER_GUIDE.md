# 📘 xls2xlsx パートナー利用ガイド

> Excel旧形式変換サービス - パートナー企業様向け導入・利用ガイド  
> バージョン: 1.0.0 | 最終更新: 2025年11月20日

---

## 🎯 本ドキュメントの目的

このガイドは、**xls2xlsx**（Excel旧形式→新形式変換サービス）をご利用いただくパートナー企業様向けの包括的な技術ドキュメントです。導入から運用まで、必要な情報をすべて網羅しています。

---

## 📋 目次

1. [サービス概要](#サービス概要)
2. [利用方法](#利用方法)
3. [導入手順](#導入手順)
4. [API仕様](#api仕様)
5. [セキュリティ](#セキュリティ)
6. [料金・制限事項](#料金制限事項)
7. [トラブルシューティング](#トラブルシューティング)
8. [サポート](#サポート)

---

## 🌟 サービス概要

### xls2xlsxとは

**xls2xlsx**は、レガシーなExcel旧形式（XLS）ファイルを最新の新形式（XLSX）に変換するクラウドサービスです。Microsoft Azure Functions上で動作し、高いセキュリティと信頼性を実現しています。

### 主要機能

| 機能 | 説明 |
|------|------|
| **XLS→XLSX変換** | 旧形式ファイルを新形式に高速変換 |
| **複数シート対応** | 複数のワークシートを含むファイルにも対応 |
| **2つの変換方式** | HTTP API / Blob Storage自動変換 |
| **大容量対応** | 最大50MBまでのファイルを処理 |
| **セキュリティ保証** | エンタープライズグレード（9.5/10スコア） |

### 品質保証

- ✅ **テスト合格率**: 100%（11/11テスト）
- ✅ **セキュリティスコア**: 9.5/10
- ✅ **稼働率**: 99.95%（Azure Functions SLA）
- ✅ **自動スケーリング**: 負荷に応じて自動拡張

---

## 💼 利用方法

### 方法1: HTTP API（推奨）

**用途**: リアルタイム変換、アプリケーション組み込み

#### 基本的な使い方

```bash
# cURLでの例
curl -X POST "https://your-function-app.azurewebsites.net/api/convert_http?code=YOUR_FUNCTION_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/sample.xls"
```

#### Pythonでの例

```python
import requests

# API設定
api_url = "https://your-function-app.azurewebsites.net/api/convert_http"
function_key = "YOUR_FUNCTION_KEY"

# ファイルを送信
with open("sample.xls", "rb") as f:
    files = {"file": f}
    params = {"code": function_key}
    response = requests.post(api_url, files=files, params=params)

# 結果を処理
if response.status_code == 200:
    # 小ファイル（<10MB）: 直接レスポンスで返却
    with open("output.xlsx", "wb") as out:
        out.write(response.content)
    print("変換完了！")
else:
    print(f"エラー: {response.json()}")
```

#### JavaScriptでの例

```javascript
// Node.js / ブラウザ
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function convertXlsToXlsx(filePath) {
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    
    const response = await axios.post(
        'https://your-function-app.azurewebsites.net/api/convert_http',
        form,
        {
            params: { code: 'YOUR_FUNCTION_KEY' },
            headers: form.getHeaders(),
            responseType: 'arraybuffer'
        }
    );
    
    fs.writeFileSync('output.xlsx', response.data);
    console.log('変換完了！');
}

convertXlsToXlsx('sample.xls');
```

---

### 方法2: Blob Storage自動変換

**用途**: バッチ処理、大量ファイルの自動変換

#### 設定手順

1. **Azure Blob Storageにファイルをアップロード**
   ```bash
   # Azure CLIの例
   az storage blob upload \
     --account-name your-storage \
     --container-name xls-input \
     --name sample.xls \
     --file sample.xls
   ```

2. **自動変換が実行される**
   - `xls-input`コンテナにアップロード
   - 自動的に変換処理が開始
   - `xls-output`コンテナに結果が保存

3. **変換結果をダウンロード**
   ```bash
   az storage blob download \
     --account-name your-storage \
     --container-name xls-output \
     --name sample.xlsx \
     --file output.xlsx
   ```

#### Pythonでの自動化例

```python
from azure.storage.blob import BlobServiceClient

# 接続文字列
connection_string = "YOUR_CONNECTION_STRING"
blob_service = BlobServiceClient.from_connection_string(connection_string)

# アップロード（自動変換トリガー）
input_container = blob_service.get_container_client("xls-input")
with open("sample.xls", "rb") as data:
    input_container.upload_blob("sample.xls", data, overwrite=True)

print("アップロード完了。変換が開始されます。")

# ダウンロード（数秒後）
import time
time.sleep(5)  # 変換処理を待機

output_container = blob_service.get_container_client("xls-output")
blob_client = output_container.get_blob_client("sample.xlsx")
with open("output.xlsx", "wb") as download_file:
    download_file.write(blob_client.download_blob().readall())

print("変換完了！output.xlsxに保存しました。")
```

---

## 🚀 導入手順

### ステップ1: Azure環境準備（15分）

#### 1.1 Function Appの作成

```bash
# Azure CLIでの作成例
az functionapp create \
  --resource-group your-resource-group \
  --consumption-plan-location japaneast \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name xls2xlsx-app \
  --storage-account yourstorage
```

#### 1.2 Blob Storageコンテナの作成

```bash
# 入力用コンテナ
az storage container create \
  --name xls-input \
  --account-name yourstorage

# 出力用コンテナ
az storage container create \
  --name xls-output \
  --account-name yourstorage
```

#### 1.3 Application Insightsの有効化

```bash
az monitor app-insights component create \
  --app xls2xlsx-insights \
  --location japaneast \
  --resource-group your-resource-group
```

---

### ステップ2: コードのデプロイ（10分）

#### オプションA: GitHub Actionsで自動デプロイ（推奨）

1. **リポジトリをフォーク**
   ```bash
   # GitHubでフォーク: https://github.com/nahisaho/xls2xlsx
   git clone https://github.com/YOUR_ORG/xls2xlsx.git
   ```

2. **GitHub Secretsを設定**
   - `AZURE_FUNCTIONAPP_PUBLISH_PROFILE_PRODUCTION`
   - Azure Portalから発行プロファイルをダウンロード

3. **デプロイワークフローを有効化**
   ```bash
   # .github/workflows/cd.yml を編集
   # if: false → if: true に変更
   git add .github/workflows/cd.yml
   git commit -m "ci: enable deployment"
   git push origin main
   ```

#### オプションB: 手動デプロイ

```bash
# Azure Functions Core Toolsを使用
cd xls2xlsx
func azure functionapp publish xls2xlsx-app
```

---

### ステップ3: 動作確認（5分）

```bash
# HTTPトリガーのテスト
curl -X POST "https://xls2xlsx-app.azurewebsites.net/api/convert_http?code=YOUR_KEY" \
  -F "file=@test.xls" \
  -o output.xlsx

# ファイルを確認
file output.xlsx
# output.xlsx: Microsoft Excel 2007+
```

✅ **導入完了！** 通常30分以内で本番環境が構築できます。

---

## 📡 API仕様

### HTTP Trigger API

#### エンドポイント
```
POST /api/convert_http
```

#### リクエスト

**ヘッダー**
```
Content-Type: multipart/form-data
```

**パラメータ**
| パラメータ | 必須 | 説明 |
|-----------|------|------|
| `code` | ✅ | Function Key（認証用） |

**ボディ**
| フィールド | 必須 | 説明 |
|-----------|------|------|
| `file` | ✅ | XLSファイル（multipart/form-data） |

#### レスポンス

**成功時（小ファイル <10MB）**
```
Status: 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="converted.xlsx"

[バイナリデータ]
```

**成功時（大ファイル ≥10MB）**
```json
{
  "status": "success",
  "message": "File converted successfully",
  "download_url": "https://...blob.core.windows.net/...",
  "filename": "converted.xlsx",
  "file_size": 15728640,
  "expires_in": "1 hour"
}
```

**エラー時**
```json
{
  "status": "error",
  "error": "Invalid file format",
  "details": "File must be in XLS format"
}
```

#### HTTPステータスコード

| コード | 意味 | 説明 |
|--------|------|------|
| 200 | OK | 変換成功 |
| 400 | Bad Request | 不正なリクエスト（ファイルなし等） |
| 413 | Payload Too Large | ファイルサイズ超過（>50MB） |
| 415 | Unsupported Media Type | XLS形式ではない |
| 500 | Internal Server Error | サーバーエラー |

---

### Blob Trigger（自動変換）

#### トリガー条件
```
コンテナ: xls-input
イベント: Blob作成時
```

#### 処理フロー
1. `xls-input`にXLSファイルがアップロードされる
2. 自動的に変換処理が開始
3. 変換結果が`xls-output`に保存される
4. ログがApplication Insightsに記録される

#### 命名規則
```
入力: xls-input/document.xls
出力: xls-output/document.xlsx
```

#### 処理時間
- 小ファイル（<1MB）: 1-3秒
- 中ファイル（1-10MB）: 3-10秒
- 大ファイル（10-50MB）: 10-30秒

---

## 🔒 セキュリティ

### セキュリティスコア: 9.5/10

#### 実装済みセキュリティ機能

| 機能 | 説明 | スコア |
|------|------|--------|
| **ファイル名サニタイズ** | パストラバーサル攻撃を防止 | 10/10 |
| **ファイル形式検証** | マジックナンバーチェック | 10/10 |
| **ファイルサイズ制限** | DoS攻撃対策（50MB上限） | 10/10 |
| **セキュリティヘッダー** | HSTS, CSP, X-Frame-Options | 10/10 |
| **エラーメッセージ** | 本番環境で詳細を隠蔽 | 9/10 |
| **監査ログ** | 全操作を記録 | 8/10 |

### 認証・認可

#### Function Key認証
```bash
# 必須: Function Keyをクエリパラメータで指定
?code=YOUR_FUNCTION_KEY
```

**Function Keyの取得方法**:
1. Azure Portal → Function App
2. 「関数」→「convert_http」
3. 「関数キー」→「default」をコピー

#### IP制限（推奨）

```bash
# Azure CLIで特定IPのみ許可
az functionapp config access-restriction add \
  --resource-group your-resource-group \
  --name xls2xlsx-app \
  --rule-name "AllowOfficeIP" \
  --action Allow \
  --ip-address 203.0.113.0/24 \
  --priority 100
```

### データ保護

- ✅ **転送中の暗号化**: HTTPS/TLS 1.2以上
- ✅ **保存時の暗号化**: Azure Storage暗号化（AES-256）
- ✅ **一時ファイル**: 処理後即座に削除
- ✅ **SASトークン**: 短い有効期限（1時間）

### セキュリティヘッダー

すべてのレスポンスに以下のヘッダーが付与されます：

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
```

---

## 💰 料金・制限事項

### Azure Functions従量課金プラン

| 項目 | 無料枠 | 超過時料金 |
|------|--------|-----------|
| **実行回数** | 100万回/月 | ¥0.02/回 |
| **実行時間** | 40万GB秒/月 | ¥0.0000167/GB秒 |
| **データ転送（送信）** | 5GB/月 | ¥9/GB |

### Blob Storage料金

| 項目 | 料金（Hot tier） |
|------|-----------------|
| **ストレージ** | ¥2.00/GB/月 |
| **書き込み** | ¥0.055/10,000操作 |
| **読み取り** | ¥0.0044/10,000操作 |

### 想定コスト例

#### ケース1: 月1万ファイル変換（中小企業）
```
実行回数   : 10,000回 → ¥0（無料枠内）
実行時間   : ~10,000GB秒 → ¥0（無料枠内）
Blob Storage: ~10GB → ¥20
────────────────────────────────
合計       : 約¥20-50/月
```

#### ケース2: 月10万ファイル変換（大企業）
```
実行回数   : 100,000回 → ¥0（無料枠内）
実行時間   : ~100,000GB秒 → ¥0（無料枠内）
Blob Storage: ~100GB → ¥200
────────────────────────────────
合計       : 約¥200-500/月
```

#### ケース3: 月100万ファイル変換（エンタープライズ）
```
実行回数   : 1,000,000回 → ¥0（無料枠内）
実行時間   : ~1,000,000GB秒 → 約¥10,000
Blob Storage: ~1TB → ¥2,000
────────────────────────────────
合計       : 約¥12,000-15,000/月
```

### 制限事項

| 項目 | 制限値 | 備考 |
|------|--------|------|
| **最大ファイルサイズ** | 50MB | DoS攻撃対策 |
| **タイムアウト** | 5分 | Azure Functions制限 |
| **同時実行数** | 200（デフォルト） | 設定変更可能 |
| **SASトークン有効期限** | 1時間 | セキュリティ対策 |

---

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 問題1: 「Invalid file format」エラー

**原因**: アップロードしたファイルがXLS形式ではない

**解決方法**:
```bash
# ファイル形式を確認
file your-file.xls
# 出力例: Microsoft Excel 97-2003 (正常)
# 出力例: Microsoft Excel 2007+ (XLSX形式 - 変換不要)
```

---

#### 問題2: 「File size exceeds limit」エラー

**原因**: ファイルサイズが50MBを超えている

**解決方法**:
1. ファイルを分割する
2. 不要なデータを削除してサイズを削減
3. カスタム実装を依頼（制限値変更可能）

---

#### 問題3: タイムアウトエラー

**原因**: 処理に5分以上かかっている

**解決方法**:
```bash
# Function Appのタイムアウト設定を延長
az functionapp config appsettings set \
  --name xls2xlsx-app \
  --resource-group your-resource-group \
  --settings "functionTimeout=00:10:00"
```

---

#### 問題4: 変換結果が文字化けする

**原因**: 元ファイルのエンコーディング問題

**解決方法**:
1. 元のXLSファイルをExcelで開く
2. 「名前を付けて保存」→「XLS形式」で再保存
3. UTF-8エンコーディングを確認

---

#### 問題5: Blob Storageからダウンロードできない

**原因**: SASトークンの有効期限切れ（1時間）

**解決方法**:
```python
# すぐにダウンロードする
# または再度変換処理を実行
```

---

### ログの確認方法

#### Application Insightsでログを確認

```kusto
// Azure Portalで実行するKustoクエリ

// 最近のエラーを確認
traces
| where timestamp > ago(1h)
| where severityLevel >= 3
| project timestamp, message, severityLevel
| order by timestamp desc

// 変換処理の統計
customEvents
| where name == "FileConversion"
| summarize 
    Count=count(),
    AvgDuration=avg(todouble(customMeasurements["duration"])),
    SuccessRate=countif(customDimensions["status"] == "success") * 100.0 / count()
| project Count, AvgDuration, SuccessRate
```

---

## 📞 サポート

### 技術サポート

#### レベル1: セルフサービス
- **ドキュメント**: 本ガイド、README.md、CICD_GUIDE.md
- **FAQ**: GitHub Wiki
- **所要時間**: 即座

#### レベル2: コミュニティサポート
- **GitHub Issues**: https://github.com/nahisaho/xls2xlsx/issues
- **対応時間**: 1-3営業日
- **費用**: 無料

#### レベル3: 優先サポート（パートナー特典）
- **専用Slackチャンネル**: 招待制
- **メール**: partners@example.com
- **対応時間**: 24時間以内
- **費用**: パートナー契約に含む

### サポート範囲

| サポート項目 | 対応可否 |
|-------------|---------|
| 導入支援 | ✅ |
| 技術的な質問 | ✅ |
| バグ報告 | ✅ |
| 機能リクエスト | ✅ |
| カスタマイズ依頼 | ✅（別途見積） |
| Azure環境構築代行 | ✅（別途見積） |
| 24/7運用監視 | ❌（将来対応予定） |

---

## 📊 監視・運用

### 推奨監視項目

#### 1. Application Insightsダッシュボード

**監視メトリクス**:
- 実行回数（成功/失敗）
- 平均処理時間
- エラー率
- リクエスト数の推移

#### 2. アラート設定

```bash
# エラー率が5%を超えたらアラート
az monitor metrics alert create \
  --name "HighErrorRate" \
  --resource xls2xlsx-app \
  --resource-type "Microsoft.Web/sites" \
  --condition "avg exceptions/server > 5" \
  --window-size 5m \
  --action email your-email@example.com
```

#### 3. ログ保持

- **Application Insights**: 90日間（デフォルト）
- **Blob Storage**: カスタム設定可能
- **推奨**: 重要ログは別途アーカイブ

---

## 🎓 ベストプラクティス

### 1. エラーハンドリング

```python
import requests
import time

def convert_with_retry(file_path, max_retries=3):
    """リトライ機能付き変換"""
    for attempt in range(max_retries):
        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    api_url,
                    files={"file": f},
                    params={"code": function_key},
                    timeout=60
                )
            
            if response.status_code == 200:
                return response.content
            elif response.status_code >= 500:
                # サーバーエラー: リトライ
                time.sleep(2 ** attempt)
                continue
            else:
                # クライアントエラー: リトライしない
                raise ValueError(f"Conversion failed: {response.json()}")
        
        except requests.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    
    raise Exception("Max retries exceeded")
```

### 2. バッチ処理

```python
from concurrent.futures import ThreadPoolExecutor
import os

def batch_convert(files, max_workers=5):
    """複数ファイルの並列変換"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(convert_with_retry, f): f 
            for f in files
        }
        
        results = {}
        for future in futures:
            file_path = futures[future]
            try:
                result = future.result()
                results[file_path] = {"status": "success", "data": result}
            except Exception as e:
                results[file_path] = {"status": "error", "error": str(e)}
        
        return results

# 使用例
files = [f for f in os.listdir("input") if f.endswith(".xls")]
results = batch_convert(files)

# 結果サマリー
success = sum(1 for r in results.values() if r["status"] == "success")
print(f"成功: {success}/{len(files)}")
```

### 3. 監視とロギング

```python
import logging
from datetime import datetime

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('conversion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def convert_with_logging(file_path):
    """ログ記録付き変換"""
    start_time = datetime.now()
    logger.info(f"変換開始: {file_path}")
    
    try:
        result = convert_with_retry(file_path)
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"変換成功: {file_path} ({duration:.2f}秒)")
        return result
    
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"変換失敗: {file_path} ({duration:.2f}秒) - {str(e)}")
        raise
```

---

## 📈 パフォーマンス最適化

### 1. ファイルサイズの最適化

**推奨事項**:
- 不要な書式を削除
- 画像を圧縮
- 未使用のシートを削除
- 空白行・列を削除

### 2. ネットワーク最適化

```python
# 圧縮転送を有効化
import gzip

def compress_and_send(file_path):
    with open(file_path, 'rb') as f:
        compressed = gzip.compress(f.read())
    
    response = requests.post(
        api_url,
        files={"file": ("file.xls.gz", compressed)},
        headers={"Content-Encoding": "gzip"}
    )
    return response
```

### 3. キャッシング

```python
import hashlib
import os

def get_file_hash(file_path):
    """ファイルのハッシュ値を計算"""
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def convert_with_cache(file_path, cache_dir="cache"):
    """キャッシュ機能付き変換"""
    file_hash = get_file_hash(file_path)
    cache_file = os.path.join(cache_dir, f"{file_hash}.xlsx")
    
    # キャッシュがあれば使用
    if os.path.exists(cache_file):
        logger.info(f"キャッシュヒット: {file_path}")
        with open(cache_file, 'rb') as f:
            return f.read()
    
    # 変換実行
    result = convert_with_retry(file_path)
    
    # キャッシュに保存
    os.makedirs(cache_dir, exist_ok=True)
    with open(cache_file, 'wb') as f:
        f.write(result)
    
    return result
```

---

## 🔄 バージョン管理・更新

### 現在のバージョン

- **バージョン**: 1.0.0
- **リリース日**: 2025年11月20日
- **ステータス**: 安定版（Production Ready）

### 更新通知

自動的に以下の方法で通知されます：
- GitHub Releasesページ
- パートナー向けメール通知
- Slackチャンネル（優先サポート契約者）

### アップグレード手順

```bash
# GitHub Actionsを使用している場合
git pull origin main
# → 自動的にデプロイされます

# 手動デプロイの場合
git pull origin main
func azure functionapp publish xls2xlsx-app
```

---

## 📋 チェックリスト

### 導入前チェックリスト

- [ ] Azureアカウントの準備完了
- [ ] Function Appの作成完了
- [ ] Blob Storageコンテナの作成完了
- [ ] Application Insightsの有効化完了
- [ ] Function Keyの取得完了
- [ ] ローカル環境でのテスト完了
- [ ] セキュリティ設定の確認完了
- [ ] 監視・アラート設定完了

### 本番運用チェックリスト

- [ ] バックアップ戦略の策定
- [ ] ディザスタリカバリ計画の作成
- [ ] SLA要件の確認
- [ ] コスト監視の設定
- [ ] 定期的なログレビュー（週次）
- [ ] セキュリティ監査（月次）
- [ ] パフォーマンス評価（月次）

---

## 🎁 パートナー特典

### 優先サポート
- 専用Slackチャンネル
- 24時間以内の回答保証
- 月次レポート提供

### カスタマイズ対応
- 初回カスタマイズ相談無料
- 機能拡張の優先対応
- 専用機能の開発サポート

### トレーニング
- オンボーディングセッション（無料）
- 技術トレーニング（月1回）
- ベストプラクティス共有

---

## 📞 お問い合わせ

### 一般的な質問
- **GitHub Issues**: https://github.com/nahisaho/xls2xlsx/issues
- **メール**: support@example.com

### パートナー専用
- **Slack**: #xls2xlsx-partners（招待制）
- **メール**: partners@example.com
- **電話**: 03-XXXX-XXXX（平日9:00-18:00）

### 緊急時（優先サポート契約者のみ）
- **緊急連絡先**: emergency@example.com
- **対応時間**: 24時間365日

---

## 📚 関連ドキュメント

| ドキュメント | 説明 | リンク |
|-------------|------|--------|
| README.md | プロジェクト概要 | [表示](README.md) |
| 要件定義書.md | 詳細な仕様 | [表示](要件定義書.md) |
| SECURITY_AUDIT.md | セキュリティ監査 | [表示](SECURITY_AUDIT.md) |
| CICD_GUIDE.md | CI/CD運用ガイド | [表示](CICD_GUIDE.md) |
| TEST_REPORT.md | テスト結果 | [表示](TEST_REPORT.md) |

---

## 🔐 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

商用利用を含め、自由にご利用いただけます。詳細は[LICENSE](LICENSE)ファイルをご確認ください。

---

## 📝 改訂履歴

| バージョン | 日付 | 変更内容 |
|-----------|------|---------|
| 1.0.0 | 2025-11-20 | 初版リリース |

---

**本ドキュメントについてのご質問やフィードバックは、お気軽にお問い合わせください。**

パートナー企業様の成功を全力でサポートいたします！ 🚀
