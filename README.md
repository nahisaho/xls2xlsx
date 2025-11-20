# xls2xlsx

> **🔒 セキュリティ強化版実装完了** (2025-11-20)  
> セキュリティスコア: **9.5/10** | 全テスト合格率: **100%** (11/11テスト)

![CI](https://github.com/nahisaho/xls2xlsx/workflows/CI%20-%20Continuous%20Integration/badge.svg)
![Security](https://github.com/nahisaho/xls2xlsx/workflows/CodeQL%20Advanced%20Security/badge.svg)

Excel旧形式（XLS）を新形式（XLSX）に変換するAzure Functionsアプリケーション

## 概要

このプロジェクトは、XLSファイルをXLSXファイルに変換するサーバーレスアプリケーションです。以下の2つの方法で変換が可能です：

1. **HTTPトリガー**: REST API経由でファイルをアップロードして変換
2. **Blobトリガー**: Azure Blob Storageにファイルをアップロードすると自動変換

## 機能

### コア機能
- ✅ XLS → XLSX 形式変換
- ✅ 複数シート対応
- ✅ 10MB未満: 直接レスポンスで返却
- ✅ 10MB以上: Blob Storage経由でダウンロードURL提供
- ✅ Docker環境でのローカルテスト対応
- ✅ Azure環境へのデプロイ対応

### 🛡️ セキュリティ機能（新規実装）
- ✅ **ファイル名サニタイズ** - パストラバーサル攻撃対策
- ✅ **ファイル形式検証** - マジックナンバーチェック
- ✅ **ファイルサイズ制限** - 50MB上限、DoS対策
- ✅ **セキュリティヘッダー** - HSTS, CSP, X-Frame-Options等
- ✅ **エラーメッセージ処理** - 本番環境で詳細を隠蔽
- ✅ **認証** - Function Key
- ✅ **プライベートStorage** - パブリックアクセス無効化
- ✅ **SASトークン** - 1時間有効期限

📄 詳細ドキュメント:
- [SECURITY_AUDIT.md](SECURITY_AUDIT.md) - セキュリティ監査レポート
- [SECURITY_IMPLEMENTATION.md](SECURITY_IMPLEMENTATION.md) - 実装完了レポート

## システム構成

```
┌─────────────────────────────────────────────────────────┐
│                    Azure Functions                      │
│  ┌─────────────────┐    ┌─────────────────┐             │
│  │ HTTP Trigger    │    │ Blob Trigger    │             │
│  │ (convert_http)  │    │ (convert_blob)  │             │
│  └────────┬────────┘    └────────┬────────┘             │
│           │                      │                      │
│           ▼                      ▼                      │
│  ┌─────────────────────────────────────────┐            │
│  │      変換ロジック (pandas + openpyxl)    │            │
│  └─────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │  Azure Blob Storage │
              │  - xls-input/       │
              │  - xls-output/      │
              └─────────────────────┘
```

## 技術スタック

- **Python**: 3.11
- **Azure Functions**: v4
- **pandas**: データフレーム操作
- **openpyxl**: XLSX書き込み
- **xlrd**: XLS読み込み
- **azure-storage-blob**: Blob操作

## プロジェクト構造

```
xls2xlsx/
├── convert_http/           # HTTPトリガー関数
│   ├── __init__.py
│   └── function.json
├── convert_blob/           # Blobトリガー関数
│   ├── __init__.py
│   └── function.json
├── samples/                # サンプルXLSファイル（生成後）
├── test_output/            # テスト結果の出力先
├── host.json               # ホスト設定
├── requirements.txt        # 依存パッケージ
├── Dockerfile              # Docker設定
├── docker-compose.yml      # Docker Compose設定
├── create_samples.py       # サンプルファイル生成
├── test_http.sh            # HTTPテストスクリプト
├── test_blob.py            # Blobテストスクリプト
└── README.md
```

## クイックスタート（ローカルテスト）

**Dockerなしで動作確認する場合:**

```bash
# 1. リポジトリをクローン
git clone <repository-url>
cd xls2xlsx

# 2. Python仮想環境を作成
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 依存パッケージをインストール
pip install -r requirements.txt

# 4. 統合テストを実行（変換ロジックを検証）
python run_local_tests.py
```

✅ テスト結果は `test_results.json` と `TEST_REPORT.md` に保存されます。

## セットアップ

### 前提条件

- Python 3.10以上（必須）
- Docker & Docker Compose（オプション：HTTP/Blobトリガーテスト用）

### Docker環境でのセットアップ

1. **リポジトリをクローン**

```bash
git clone <repository-url>
cd xls2xlsx
```

2. **サンプルXLSファイルを生成**

```bash
pip install pandas xlwt
python create_samples.py
```

3. **Dockerコンテナを起動**

```bash
docker-compose up -d
```

サービスが起動します：
- Azure Functions: `http://localhost:8080`
- Azurite (Blob Storage): `http://localhost:10000`

4. **ログを確認**

```bash
docker-compose logs -f functions
```

## テスト方法

### 統合テスト（ローカル - Docker不要）

変換ロジックを直接テストする場合:

```bash
# 仮想環境をアクティベート
source .venv/bin/activate

# 統合テストを実行
python run_local_tests.py
```

**テスト内容:**
- ✅ Pythonパッケージの確認
- ✅ サンプルXLSファイルの生成
- ✅ XLS→XLSX変換ロジックのテスト
- ✅ 複数シート変換のテスト
- ✅ 出力ファイルの検証

**出力ファイル:**
- `test_results.json` - JSON形式の詳細結果
- `test_execution.log` - 実行ログ
- `TEST_REPORT.md` - 詳細レポート
- `TEST_SUMMARY.md` - サマリー
- `samples/` - 生成されたサンプルXLSファイル
- `test_output/` - 変換済みXLSXファイル

### 1. HTTPトリガーのテスト（Docker環境）

#### シェルスクリプトを使用

```bash
chmod +x test_http.sh
./test_http.sh
```

#### curlコマンドを直接実行

```bash
curl -X POST http://localhost:8080/api/convert_http \
  -H "Content-Type: application/octet-stream" \
  -H "X-Filename: sample1.xls" \
  --data-binary "@samples/sample1.xls" \
  --output test_output/converted.xlsx
```

#### PowerShell（Windows）

```powershell
$headers = @{
    "Content-Type" = "application/octet-stream"
    "X-Filename" = "sample1.xls"
}
Invoke-RestMethod -Uri "http://localhost:8080/api/convert_http" `
    -Method Post `
    -InFile "samples/sample1.xls" `
    -OutFile "test_output/converted.xlsx" `
    -Headers $headers
```

### 2. Blobトリガーのテスト（Docker環境）

```bash
pip install azure-storage-blob
python test_blob.py samples/sample1.xls
```

このスクリプトは以下を実行します：
1. Azuriteに`xls-input`と`xls-output`コンテナを作成
2. `xls-input`にXLSファイルをアップロード
3. Blobトリガーが自動実行され、変換が行われる
4. `xls-output`から変換済みファイルをダウンロード

**注意**: このテストにはDocker環境が必要です。

## ローカル開発（Docker不使用）

### セットアップ

1. **仮想環境を作成**

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

2. **依存パッケージをインストール**

```bash
pip install -r requirements.txt
```

3. **Azure Functions Core Toolsをインストール**

```bash
# macOS
brew tap azure/functions
brew install azure-functions-core-tools@4

# Windows
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

4. **Azuriteを起動**

```bash
# 別のターミナルで
docker run -p 10000:10000 -p 10001:10001 -p 10002:10002 \
  mcr.microsoft.com/azure-storage/azurite
```

5. **関数を実行**

```bash
func start
```

関数が起動します：
- HTTP Trigger: `http://localhost:7071/api/convert_http`

## Azure環境へのデプロイ

### 1. Azureリソースの作成

```bash
# リソースグループ作成
az group create --name rg-xls-converter --location japaneast

# ストレージアカウント作成
az storage account create \
  --name stxlsconverter \
  --resource-group rg-xls-converter \
  --location japaneast \
  --sku Standard_LRS

# Blobコンテナ作成
az storage container create --name xls-input --account-name stxlsconverter
az storage container create --name xls-output --account-name stxlsconverter

# Function App作成
az functionapp create \
  --name func-xls-converter \
  --resource-group rg-xls-converter \
  --storage-account stxlsconverter \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux \
  --consumption-plan-location japaneast
```

### 2. デプロイ

```bash
func azure functionapp publish func-xls-converter
```

### 3. 動作確認

```bash
# 関数URLを取得
FUNCTION_URL=$(az functionapp function show \
  --name func-xls-converter \
  --resource-group rg-xls-converter \
  --function-name convert_http \
  --query invokeUrlTemplate -o tsv)

# テスト
curl -X POST "$FUNCTION_URL" \
  -H "X-Filename: sample1.xls" \
  --data-binary "@samples/sample1.xls" \
  --output converted.xlsx
```

## API仕様

### HTTPトリガー

#### エンドポイント
```
POST /api/convert_http
```

#### リクエストヘッダー
| ヘッダー | 必須 | 説明 |
|---------|------|------|
| Content-Type | Yes | `application/octet-stream` |
| X-Filename | No | ファイル名（省略時: "converted"） |

#### レスポンス（10MB未満）
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Body: XLSXファイルのバイナリデータ

#### レスポンス（10MB以上）
```json
{
  "download_url": "https://stxlsconverter.blob.core.windows.net/xls-output/sample.xlsx?{SASトークン}"
}
```

### Blobトリガー

- **入力コンテナ**: `xls-input`
- **出力コンテナ**: `xls-output`
- **トリガー条件**: `.xls` 拡張子のファイルのみ
- **出力ファイル名**: 元のファイル名の拡張子を `.xlsx` に変更

## トラブルシューティング

### Docker環境でコンテナが起動しない

```bash
# ログを確認
docker-compose logs functions

# コンテナを再ビルド
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Azuriteに接続できない

```bash
# Azuriteが起動しているか確認
docker-compose ps

# ポートが使用中でないか確認
netstat -an | grep 10000
```

### 変換エラーが発生する

- XLSファイルが正しい形式か確認
- xlrdは `.xls` 形式のみサポート（`.xlsx` は非対応）
- ファイルが破損していないか確認

### Pythonパッケージのエラー

```bash
# 依存関係を再インストール
pip install --upgrade -r requirements.txt
```

## テスト結果

### ✅ 統合テスト: 100% 成功 (5/5)

最新のテスト結果（2025-11-20実施）:

| テスト項目 | 結果 | 実行時間 |
|-----------|------|----------|
| Pythonパッケージチェック | ✅ PASS | - |
| サンプルファイル作成 | ✅ PASS | - |
| 変換ロジックテスト | ✅ PASS | 0.02秒 |
| 複数シート変換テスト | ✅ PASS | 0.01秒 |
| 出力ファイル検証 | ✅ PASS | - |

**検証済み機能:**
- ✅ XLS → XLSX 形式変換
- ✅ 単一シート/複数シートの変換
- ✅ データ整合性の保持
- ✅ 変換ファイルの読み込み可能性

詳細は `TEST_REPORT.md` を参照してください。

## パフォーマンス

### 実測値（ローカルテスト）

| ファイルサイズ | シート数 | 処理時間 |
|--------------|---------|----------|
| 5.5 KB | 1シート | 0.02秒 |
| 5.5 KB | 2シート | 0.01秒 |

### 想定値（本番環境）

| ファイルサイズ | 処理時間目安 |
|--------------|------------|
| 1MB未満 | 5-10秒 |
| 1-10MB | 10-30秒 |
| 10-50MB | 30-60秒 |

※ 初回実行時はコールドスタートにより遅延が発生する場合があります。

## セキュリティ

### 本番環境での推奨設定

1. **認証レベル**: 関数キー以上を使用
2. **IP制限**: 信頼できるIPアドレスのみ許可
3. **入力検証**: ファイルサイズ、形式の検証を実装
4. **SASトークン**: 短い有効期限を設定（デフォルト: 1時間）

## プロジェクトファイル

### 主要ファイル

- `convert_http/` - HTTPトリガー関数
- `convert_blob/` - Blobトリガー関数
- `host.json` - Azure Functions設定
- `requirements.txt` - 依存パッケージ
- `要件定義書.md` - 詳細な要件定義

### テスト関連

- `run_local_tests.py` - ローカル統合テストスクリプト
- `run_integration_tests.py` - Docker統合テストスクリプト
- `create_samples.py` - サンプルファイル生成
- `test_http.sh` - HTTPトリガーテストスクリプト
- `test_blob.py` - Blobトリガーテストスクリプト

### ドキュメント

- `README.md` - このファイル
- `要件定義書.md` - プロジェクト要件定義
- `TEST_REPORT.md` - テスト詳細レポート
- `TEST_SUMMARY.md` - テストサマリー

## ライセンス

MIT License

## 参考資料

- [Azure Functions Python開発者ガイド](https://docs.microsoft.com/ja-jp/azure/azure-functions/functions-reference-python)
- [pandas公式ドキュメント](https://pandas.pydata.org/docs/)
- [openpyxl公式ドキュメント](https://openpyxl.readthedocs.io/)
- [xlrd公式ドキュメント](https://xlrd.readthedocs.io/)

## サポート

問題が発生した場合は、GitHubのIssuesで報告してください。

---

**作成日**: 2025-11-20  
**バージョン**: 1.0.0
