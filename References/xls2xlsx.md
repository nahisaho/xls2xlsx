# 第1章 はじめに

## 1.1 概要

本手順書では、Excel旧形式（XLS）を新形式（XLSX）に変換するツールをAzure Functionsで実装する方法を解説します。

**実装する機能:**
- **HTTPトリガー関数**: REST API形式でファイルを受け取り、変換結果を返す
- **Blobトリガー関数**: Azure Storageにアップロードされたファイルを自動変換

## 1.2 システム構成図

```
┌─────────────────────────────────────────────────────────┐
│                    Azure Functions                      │
│  ┌─────────────────┐    ┌─────────────────┐             │
│  │ HTTP Trigger    │    │ Blob Trigger    │             │
│  │ (convert-http)  │    │ (convert-blob)  │             │
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
              │  - input/  (入力)   │
              │  - output/ (出力)   │
              └─────────────────────┘
```

## 1.3 前提条件

**必要な知識:**
- Pythonの基本文法（関数、import、例外処理）
- コマンドラインの基本操作

**必要なアカウント:**
- Microsoftアカウント
- Azureサブスクリプション（無料枠で可）

## 1.4 使用技術

| 技術 | バージョン | 用途 |
|------|-----------|------|
| Python | 3.10〜3.12 | ランタイム |
| Azure Functions | v4 | サーバーレス実行環境 |
| pandas | 最新 | データフレーム操作 |
| openpyxl | 最新 | XLSX書き込み |
| xlrd | 最新 | XLS読み込み |

> **注**: Python 3.13も利用可能ですが、従量課金プランでは非対応です。

---

# 第2章 環境構築

## 2.1 Pythonのインストール

### Windows

1. [Python公式サイト](https://www.python.org/downloads/)からインストーラをダウンロード
2. インストーラを実行し、**「Add Python to PATH」にチェック**を入れる
3. 「Install Now」をクリック

### macOS

```bash
# Homebrewを使用
brew install python@3.11
```

### バージョン確認

```bash
python --version
# 出力例: Python 3.11.5
```

## 2.2 VS Codeのインストール

1. [VS Code公式サイト](https://code.visualstudio.com/)からダウンロード
2. インストーラを実行

## 2.3 VS Code拡張機能のインストール

VS Codeを起動し、以下の拡張機能をインストールします。

1. **Python** (Microsoft)
   - 拡張機能タブ（Ctrl+Shift+X）を開く
   - 「Python」で検索
   - Microsoft製の拡張機能をインストール

2. **Azure Functions** (Microsoft)
   - 「Azure Functions」で検索
   - インストール

3. **Azure Account** (Microsoft)
   - 「Azure Account」で検索
   - インストール

## 2.4 Azure Functions Core Toolsのインストール

ローカルでAzure Functionsを実行するためのツールです。

### Windows

```bash
# npmを使用（Node.jsが必要）
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

または、[インストーラ](https://github.com/Azure/azure-functions-core-tools/releases)からダウンロード。

### macOS

```bash
brew tap azure/functions
brew install azure-functions-core-tools@4
```

### バージョン確認

```bash
func --version
# 出力例: 4.0.5455
```

## 2.5 Azure CLIのインストール（任意）

リソース作成をコマンドラインで行う場合に使用します。

### Windows

[Azure CLI インストーラ](https://docs.microsoft.com/ja-jp/cli/azure/install-azure-cli-windows)からダウンロード。

### macOS

```bash
brew install azure-cli
```

### バージョン確認

```bash
az --version
# 出力例: azure-cli 2.53.0
```

---

# 第3章 Azure環境の準備

## 3.1 Azureポータルへのサインイン

1. [Azureポータル](https://portal.azure.com/)にアクセス
2. Microsoftアカウントでサインイン

## 3.2 リソースグループの作成

リソースグループは、関連するAzureリソースをまとめる論理的なコンテナです。

1. Azureポータルで「リソースグループ」を検索
2. 「+ 作成」をクリック
3. 以下を入力:
   - **サブスクリプション**: 使用するサブスクリプション
   - **リソースグループ名**: `rg-xls-converter`
   - **リージョン**: `Japan East`
4. 「確認および作成」→「作成」

## 3.3 ストレージアカウントの作成

Azure Functionsの実行とファイル保存に使用します。

1. Azureポータルで「ストレージアカウント」を検索
2. 「+ 作成」をクリック
3. 以下を入力:
   - **リソースグループ**: `rg-xls-converter`
   - **ストレージアカウント名**: `stxlsconverter`（グローバルで一意）
   - **リージョン**: `Japan East`
   - **パフォーマンス**: Standard
   - **冗長性**: LRS（ローカル冗長）
4. 「確認および作成」→「作成」

## 3.4 Blobコンテナの作成

1. 作成したストレージアカウントを開く
2. 左メニューの「コンテナー」をクリック
3. 「+ コンテナー」をクリックし、以下を作成:
   - **名前**: `xls-input`（入力用）
   - **パブリックアクセスレベル**: プライベート
4. 同様に `xls-output`（出力用）も作成

## 3.5 Function Appの作成

1. Azureポータルで「関数アプリ」を検索
2. 「+ 作成」をクリック
3. **基本**タブ:
   - **リソースグループ**: `rg-xls-converter`
   - **関数アプリ名**: `func-xls-converter`（グローバルで一意）
   - **ランタイムスタック**: Python
   - **バージョン**: 3.11
   - **リージョン**: Japan East
   - **オペレーティングシステム**: Linux
   - **ホスティングプラン**: 従量課金（サーバーレス）
4. **ストレージ**タブ:
   - **ストレージアカウント**: `stxlsconverter`（先ほど作成したもの）
5. 「確認および作成」→「作成」

---

# 第4章 プロジェクトの作成

## 4.1 プロジェクトフォルダの作成

```bash
mkdir xls-converter
cd xls-converter
```

## 4.2 VS Codeでプロジェクトを開く

```bash
code .
```

## 4.3 Azure Functionsプロジェクトの初期化

1. VS Codeでコマンドパレットを開く（Ctrl+Shift+P）
2. 「Azure Functions: Create New Project」を選択
3. 以下を設定:
   - **フォルダ**: 現在のフォルダを選択
   - **言語**: Python
   - **Pythonインタープリター**: Python 3.11を選択
   - **テンプレート**: Skip for now（後で関数を追加）

> **注**: 本手順書ではv1プログラミングモデル（function.json方式）を使用します。Microsoftはv2モデル（デコレータ方式）を推奨していますが、初心者にはv1の方が構造を理解しやすいため採用しています。

## 4.4 生成されるファイル構造

```
xls-converter/
├── .venv/                  # 仮想環境
├── .vscode/                # VS Code設定
├── host.json               # ホスト設定
├── local.settings.json     # ローカル設定
└── requirements.txt        # 依存パッケージ
```

## 4.5 依存パッケージの設定

`requirements.txt`を以下の内容に編集:

```plaintext
azure-functions
pandas
openpyxl
xlrd
azure-storage-blob
```

## 4.6 パッケージのインストール

```bash
# 仮想環境をアクティベート
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# パッケージインストール
pip install -r requirements.txt
```

---

# 第5章 HTTPトリガー関数の実装

## 5.1 関数の作成

1. VS Codeでコマンドパレットを開く（Ctrl+Shift+P）
2. 「Azure Functions: Create Function」を選択
3. 以下を設定:
   - **テンプレート**: HTTP trigger
   - **関数名**: `convert_http`
   - **認証レベル**: Function

## 5.2 関数コードの実装

`convert_http/__init__.py`を以下の内容に置き換え:

```python
import azure.functions as func
import pandas as pd
import logging
import io
import os
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta

# ファイルサイズ閾値（10MB以上はStorageに保存）
SIZE_THRESHOLD = 10 * 1024 * 1024

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTPリクエストでXLSファイルを受け取り、XLSXに変換して返す

    - 10MB未満: レスポンスで直接返す
    - 10MB以上: Blob Storageに保存してダウンロードURLを返す
    """
    logging.info('HTTP trigger function processed a request.')

    try:
        # リクエストからファイルを取得
        file_data = req.get_body()

        if not file_data:
            return func.HttpResponse(
                "リクエストボディにXLSファイルが含まれていません。",
                status_code=400
            )

        # ファイル名を取得（ヘッダーまたはクエリパラメータから）
        filename = req.headers.get('X-Filename', 'converted')
        if filename.lower().endswith('.xls'):
            filename = filename[:-4]

        # XLSをXLSXに変換
        xlsx_data = convert_xls_to_xlsx(file_data)

        # ファイルサイズに応じて出力方法を切り替え
        if len(xlsx_data) < SIZE_THRESHOLD:
            # 直接レスポンスで返す
            return func.HttpResponse(
                xlsx_data,
                status_code=200,
                headers={
                    'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'Content-Disposition': f'attachment; filename="{filename}.xlsx"'
                }
            )
        else:
            # Blob Storageに保存してURLを返す
            download_url = save_to_blob_and_get_url(xlsx_data, f"{filename}.xlsx")
            return func.HttpResponse(
                f'{{"download_url": "{download_url}"}}',
                status_code=200,
                headers={'Content-Type': 'application/json'}
            )

    except Exception as e:
        logging.error(f"変換エラー: {str(e)}")
        return func.HttpResponse(
            f"変換中にエラーが発生しました: {str(e)}",
            status_code=500
        )


def convert_xls_to_xlsx(xls_data: bytes) -> bytes:
    """
    XLSバイナリデータをXLSXバイナリデータに変換

    Args:
        xls_data: XLSファイルのバイナリデータ

    Returns:
        XLSXファイルのバイナリデータ
    """
    # XLSデータをDataFrameに読み込み
    xls_buffer = io.BytesIO(xls_data)

    # 複数シートに対応
    xlsx_buffer = io.BytesIO()

    # ExcelファイルをExcelFileオブジェクトとして読み込み
    xls_file = pd.ExcelFile(xls_buffer, engine='xlrd')

    # Excelライターを作成
    with pd.ExcelWriter(xlsx_buffer, engine='openpyxl') as writer:
        # 全シートを変換
        for sheet_name in xls_file.sheet_names:
            df = pd.read_excel(xls_file, sheet_name=sheet_name)
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    xlsx_buffer.seek(0)
    return xlsx_buffer.getvalue()


def save_to_blob_and_get_url(data: bytes, filename: str) -> str:
    """
    Blob Storageにファイルを保存し、SAS付きダウンロードURLを返す

    Args:
        data: ファイルのバイナリデータ
        filename: 保存するファイル名

    Returns:
        SAS付きダウンロードURL
    """
    # 接続文字列を取得
    connection_string = os.environ['AzureWebJobsStorage']

    # BlobServiceClientを作成
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # コンテナとBlobの参照を取得
    container_name = 'xls-output'
    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=filename
    )

    # アップロード
    blob_client.upload_blob(data, overwrite=True)

    # SASトークンを生成（1時間有効）
    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=container_name,
        blob_name=filename,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)
    )

    # ダウンロードURLを構築
    download_url = f"{blob_client.url}?{sas_token}"

    return download_url
```

## 5.3 function.jsonの確認

`convert_http/function.json`が以下のようになっていることを確認:

```json
{
  "scriptFile": "__init__.py",
  "bindings": [
    {
      "authLevel": "function",
      "type": "httpTrigger",
      "direction": "in",
      "name": "req",
      "methods": ["post"]
    },
    {
      "type": "http",
      "direction": "out",
      "name": "$return"
    }
  ]
}
```

---

# 第6章 Blobトリガー関数の実装

## 6.1 関数の作成

1. VS Codeでコマンドパレットを開く（Ctrl+Shift+P）
2. 「Azure Functions: Create Function」を選択
3. 以下を設定:
   - **テンプレート**: Azure Blob Storage trigger
   - **関数名**: `convert_blob`
   - **設定名**: AzureWebJobsStorage
   - **パス**: `xls-input/{name}`

## 6.2 関数コードの実装

`convert_blob/__init__.py`を以下の内容に置き換え:

```python
import azure.functions as func
import pandas as pd
import logging
import io
import os
from azure.storage.blob import BlobServiceClient

def main(inputblob: func.InputStream):
    """
    xls-inputコンテナにアップロードされたXLSファイルを
    XLSXに変換してxls-outputコンテナに保存

    Args:
        inputblob: 入力Blobストリーム
    """
    logging.info(f"Blob trigger function processed blob: {inputblob.name}")
    logging.info(f"Blob size: {inputblob.length} bytes")

    try:
        # ファイル名を取得（.xlsを.xlsxに変更）
        original_name = inputblob.name.split('/')[-1]

        # .xls以外のファイルはスキップ
        if not original_name.lower().endswith('.xls'):
            logging.info(f"Skipping non-XLS file: {original_name}")
            return

        output_name = original_name[:-4] + '.xlsx'

        # XLSデータを読み込み
        xls_data = inputblob.read()

        # XLSXに変換
        xlsx_data = convert_xls_to_xlsx(xls_data)

        # 出力コンテナに保存
        save_to_output_container(xlsx_data, output_name)

        logging.info(f"Successfully converted {original_name} to {output_name}")

    except Exception as e:
        logging.error(f"変換エラー: {str(e)}")
        raise


def convert_xls_to_xlsx(xls_data: bytes) -> bytes:
    """
    XLSバイナリデータをXLSXバイナリデータに変換

    Args:
        xls_data: XLSファイルのバイナリデータ

    Returns:
        XLSXファイルのバイナリデータ
    """
    # XLSデータをDataFrameに読み込み
    xls_buffer = io.BytesIO(xls_data)

    # 複数シートに対応
    xlsx_buffer = io.BytesIO()

    # ExcelファイルをExcelFileオブジェクトとして読み込み
    xls_file = pd.ExcelFile(xls_buffer, engine='xlrd')

    # Excelライターを作成
    with pd.ExcelWriter(xlsx_buffer, engine='openpyxl') as writer:
        # 全シートを変換
        for sheet_name in xls_file.sheet_names:
            df = pd.read_excel(xls_file, sheet_name=sheet_name)
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    xlsx_buffer.seek(0)
    return xlsx_buffer.getvalue()


def save_to_output_container(data: bytes, filename: str):
    """
    出力コンテナにファイルを保存

    Args:
        data: ファイルのバイナリデータ
        filename: 保存するファイル名
    """
    # 接続文字列を取得
    connection_string = os.environ['AzureWebJobsStorage']

    # BlobServiceClientを作成
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # 出力コンテナにアップロード
    blob_client = blob_service_client.get_blob_client(
        container='xls-output',
        blob=filename
    )

    blob_client.upload_blob(data, overwrite=True)
    logging.info(f"Saved to xls-output/{filename}")
```

## 6.3 function.jsonの確認

`convert_blob/function.json`が以下のようになっていることを確認:

```json
{
  "scriptFile": "__init__.py",
  "bindings": [
    {
      "name": "inputblob",
      "type": "blobTrigger",
      "direction": "in",
      "path": "xls-input/{name}",
      "connection": "AzureWebJobsStorage"
    }
  ]
}
```

---

# 第7章 ローカルテスト

## 7.1 ローカル設定の構成

`local.settings.json`を編集:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "<ストレージ接続文字列>",
    "FUNCTIONS_WORKER_RUNTIME": "python"
  }
}
```

**接続文字列の取得方法:**
1. Azureポータルでストレージアカウントを開く
2. 「アクセスキー」をクリック
3. 「接続文字列」をコピー

## 7.2 ローカル実行

```bash
func start
```

成功すると以下のように表示されます:

```
Functions:
        convert_http: [POST] http://localhost:7071/api/convert_http
        convert_blob: blobTrigger
```

## 7.3 HTTPトリガーのテスト

### curlを使用

```bash
curl -X POST http://localhost:7071/api/convert_http \
  -H "X-Filename: sample.xls" \
  --data-binary @sample.xls \
  --output converted.xlsx
```

### PowerShellを使用

```powershell
$headers = @{
    "X-Filename" = "sample.xls"
}
Invoke-RestMethod -Uri "http://localhost:7071/api/convert_http" `
    -Method Post `
    -InFile "sample.xls" `
    -OutFile "converted.xlsx" `
    -Headers $headers
```

### Postmanを使用

1. メソッド: POST
2. URL: `http://localhost:7071/api/convert_http`
3. Headers: `X-Filename: sample.xls`
4. Body: binary → ファイルを選択
5. Send → Save Response

## 7.4 Blobトリガーのテスト

1. Azure Storage Explorerをインストール（または Azureポータルを使用）
2. `xls-input`コンテナにXLSファイルをアップロード
3. ローカルのターミナルでログを確認
4. `xls-output`コンテナに変換されたXLSXファイルが生成されることを確認

---

# 第8章 Azureへのデプロイ

## 8.1 VS Codeからデプロイ

1. VS Codeの左サイドバーでAzureアイコンをクリック
2. 「WORKSPACE」セクションの「Deploy to Function App...」をクリック
   - または、コマンドパレット（Ctrl+Shift+P）→「Azure Functions: Deploy to Function App」
3. 以下を選択:
   - **サブスクリプション**: 使用するサブスクリプション
   - **Function App**: `func-xls-converter`（第3章で作成したもの）
4. 確認ダイアログで「Deploy」をクリック
5. デプロイ完了まで待機（2-3分）

## 8.2 デプロイの確認

1. VS Codeの出力パネル（Ctrl+Shift+U）で「Azure Functions」を選択
2. 「Deployment successful」と表示されることを確認

## 8.3 アプリケーション設定の確認

デプロイ後、Azure上の設定を確認します:

1. Azureポータルで関数アプリを開く
2. 「構成」→「アプリケーション設定」
3. `AzureWebJobsStorage`が正しく設定されていることを確認

---

# 第9章 動作確認

## 9.1 HTTPトリガーのテスト

### 関数URLの取得

1. Azureポータルで関数アプリを開く
2. 「関数」→「convert_http」をクリック
3. 「関数のURLの取得」をクリック
4. URLをコピー（関数キーが含まれる）

### curlでテスト

```bash
curl -X POST "https://func-xls-converter.azurewebsites.net/api/convert_http?code=<関数キー>" \
  -H "X-Filename: sample.xls" \
  --data-binary @sample.xls \
  --output converted.xlsx
```

## 9.2 Blobトリガーのテスト

1. Azureポータルでストレージアカウントを開く
2. 「コンテナー」→「xls-input」
3. 「アップロード」でXLSファイルをアップロード
4. 「xls-output」コンテナを確認
5. 変換されたXLSXファイルが生成されていれば成功

## 9.3 ログの確認

1. Azureポータルで関数アプリを開く
2. 「関数」→「convert_http」または「convert_blob」
3. 「監視」をクリック
4. 実行履歴とログを確認

---

# 第10章 トラブルシューティング

## 10.1 よくあるエラーと対処法

### ModuleNotFoundError: No module named 'pandas'

**原因**: 依存パッケージがインストールされていない

**対処法**:
1. `requirements.txt`にパッケージが記載されているか確認
2. 再デプロイを実行

### Unable to find storage account

**原因**: ストレージ接続文字列が設定されていない

**対処法**:
1. `local.settings.json`の`AzureWebJobsStorage`を確認
2. Azureポータルの「アプリケーション設定」を確認

### xlrd.biffh.XLRDError: Excel xlsx file; not supported

**原因**: XLSXファイルをXLSとして読み込もうとしている

**対処法**:
- 入力ファイルが本当にXLS形式か確認
- xlrdは`.xls`形式のみサポート（xlrd 2.0以降）

### Request body too large

**原因**: HTTPリクエストのサイズ制限を超えている

**対処法**:
- Azure Functionsの最大リクエストサイズは**210MB**
- `host.json`で制限を調整可能:

```json
{
  "extensions": {
    "http": {
      "maxRequestBodySize": 209715200
    }
  }
}
```

### HTTPトリガーのタイムアウト

**原因**: Azure Load Balancerのアイドルタイムアウト制限

**対処法**:
- HTTPトリガー関数は最大**230秒**でレスポンスを返す必要があります
- `host.json`の`functionTimeout`を長くしても、この制限は回避できません
- 長時間処理が必要な場合は、非同期パターン（Durable Functions）を検討してください

### Cold start latency (初回実行が遅い)

**原因**: pandasパッケージが大きいため、初回起動に時間がかかる

**対処法**:
- 定期的なウォームアップリクエストを設定
- Premium プランへの変更を検討

## 10.2 デバッグ方法

### ローカルデバッグ

1. VS Codeでブレークポイントを設定
2. F5キーでデバッグ実行
3. HTTPリクエストを送信
4. ブレークポイントで停止し、変数を確認

### Azure上のログ確認

```bash
# Azure CLIでログをストリーミング
az webapp log tail --name func-xls-converter --resource-group rg-xls-converter
```

### Application Insightsの活用

1. Azureポータルで関数アプリを開く
2. 「Application Insights」を有効化
3. 詳細なメトリクスとトレースを確認

---

# 第11章 セキュリティとベストプラクティス

## 11.1 認証の設定

本番環境では、関数キー以外の認証も検討してください:

- **Azure AD認証**: エンタープライズ環境向け
- **APIキー + IP制限**: 特定のクライアントのみ許可

## 11.2 ネットワークセキュリティ

1. Azureポータルで関数アプリを開く
2. 「ネットワーク」→「アクセス制限」
3. 必要に応じてIP制限を設定

## 11.3 入力バリデーション

本番環境では、以下のバリデーションを追加することを推奨:

```python
# ファイルサイズ制限
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

if len(file_data) > MAX_FILE_SIZE:
    return func.HttpResponse(
        "ファイルサイズが上限を超えています（最大50MB）",
        status_code=413
    )

# ファイル形式の検証
if not file_data[:8].startswith(b'\xd0\xcf\x11\xe0'):
    return func.HttpResponse(
        "有効なXLSファイルではありません",
        status_code=400
    )
```

## 11.4 コスト最適化

- **従量課金プラン**: 実行回数が少ない場合に最適
- **Premium プラン**: コールドスタートを避けたい場合
- **ストレージライフサイクル**: 古いファイルを自動削除

---

# 第12章 次のステップ

## 12.1 機能拡張のアイデア

- **複数ファイル一括変換**: ZIPでまとめて変換
- **XLSX→XLS逆変換**: 逆方向の変換もサポート
- **変換オプション**: シート選択、データフィルタリング
- **通知機能**: 変換完了時にメール/Teams通知

## 12.2 参考リンク

- [Azure Functions Python開発者ガイド](https://docs.microsoft.com/ja-jp/azure/azure-functions/functions-reference-python)
- [pandas公式ドキュメント](https://pandas.pydata.org/docs/)
- [openpyxl公式ドキュメント](https://openpyxl.readthedocs.io/)

---

# 付録A: 完全なプロジェクト構造

```
xls-converter/
├── .venv/
├── .vscode/
│   └── settings.json
├── convert_http/
│   ├── __init__.py
│   └── function.json
├── convert_blob/
│   ├── __init__.py
│   └── function.json
├── host.json
├── local.settings.json
└── requirements.txt
```

---

# 付録B: host.jsonの完全な設定例

```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "excludedTypes": "Request"
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  },
  "extensions": {
    "http": {
      "maxRequestBodySize": 209715200,
      "routePrefix": "api"
    },
    "blobs": {
      "maxDegreeOfParallelism": 4
    }
  },
  "functionTimeout": "00:05:00"
}
```

> **注**:
> - `extensionBundle`は必須です。これがないとバインディング拡張機能が動作しません。
> - 従量課金プランの`functionTimeout`はデフォルト5分、最大10分です。
> - HTTPトリガーは230秒のタイムアウト制限があるため、長時間処理には注意が必要です。

---

【使用ガイド】
この手順書に従って、XLS→XLSX変換ツールをAzure Functionsで構築できます。第2章から順番に進めてください。

【レビューポイント】
1. ストレージアカウント名、関数アプリ名が実際の環境に合っているか
2. セキュリティ設定（認証、IP制限）が要件を満たしているか
3. エラーハンドリングが十分か

【次のステップ】
1. 第2章から環境構築を開始
2. サンプルXLSファイルを用意してテスト
3. 本番環境向けにセキュリティ設定を強化
