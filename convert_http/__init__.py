import azure.functions as func
import pandas as pd
import logging
import io
import os
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from security_utils import (
    validate_input,
    get_security_headers,
    sanitize_error_message,
    log_security_event
)

# ファイルサイズ閾値（10MB以上はStorageに保存）
SIZE_THRESHOLD = 10 * 1024 * 1024

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTPリクエストでXLSファイルを受け取り、XLSXに変換して返す
    セキュリティ強化版
    
    - 10MB未満: レスポンスで直接返す
    - 10MB以上: Blob Storageに保存してダウンロードURLを返す
    """
    logging.info('HTTP trigger function processed a request.')
    
    # 本番環境判定
    is_production = os.environ.get('AZURE_FUNCTIONS_ENVIRONMENT') == 'Production'
    
    try:
        # リクエストからファイルを取得
        file_data = req.get_body()
        
        if not file_data:
            log_security_event('empty_request', {'ip': req.headers.get('X-Forwarded-For')})
            return create_error_response(
                "リクエストボディにXLSファイルが含まれていません。",
                400
            )
        
        # ファイル名を取得
        raw_filename = req.headers.get('X-Filename', 'converted')
        
        # セキュリティ検証（ファイル名サニタイズ、サイズチェック、形式チェック）
        is_valid, sanitized_filename, error_message = validate_input(file_data, raw_filename)
        
        if not is_valid:
            log_security_event('validation_failed', {
                'reason': error_message,
                'original_filename': raw_filename,
                'file_size': len(file_data),
                'ip': req.headers.get('X-Forwarded-For')
            })
            return create_error_response(error_message, 400)
        
        # .xls拡張子を除去
        if sanitized_filename.lower().endswith('.xls'):
            sanitized_filename = sanitized_filename[:-4]
        
        logging.info(f"Processing file: {sanitized_filename} ({len(file_data)} bytes)")

        # XLSをXLSXに変換
        xlsx_data = convert_xls_to_xlsx(file_data)

        # ファイルサイズに応じて出力方法を切り替え
        if len(xlsx_data) < SIZE_THRESHOLD:
            # 直接レスポンスで返す
            return create_file_response(xlsx_data, f"{sanitized_filename}.xlsx")
        else:
            # Blob Storageに保存してURLを返す
            download_url = save_to_blob_and_get_url(xlsx_data, f"{sanitized_filename}.xlsx")
            return create_json_response({'download_url': download_url})
    
    except pd.errors.ParserError as e:
        logging.error(f"Pandas parsing error: {str(e)}")
        log_security_event('parse_error', {'error': str(e)})
        return create_error_response(
            "ファイルの解析に失敗しました。有効なXLSファイルか確認してください。",
            400
        )
    
    except Exception as e:
        logging.error(f"変換エラー: {str(e)}", exc_info=True)
        log_security_event('conversion_error', {'error': str(e)})
        
        error_message = sanitize_error_message(e, is_production)
        return create_error_response(error_message, 500)


def convert_xls_to_xlsx(xls_data: bytes) -> bytes:
    """
    XLSバイナリデータをXLSXバイナリデータに変換
    
    Args:
        xls_data: XLSファイルのバイナリデータ
        
    Returns:
        XLSXファイルのバイナリデータ
        
    Raises:
        pd.errors.ParserError: XLS解析エラー
        ValueError: データサイズ/シート数制限超過
        Exception: その他の変換エラー
    """
    # XLSデータをDataFrameに読み込み
    xls_buffer = io.BytesIO(xls_data)
    
    # 複数シートに対応
    xlsx_buffer = io.BytesIO()
    
    # ExcelファイルをExcelFileオブジェクトとして読み込み
    xls_file = pd.ExcelFile(xls_buffer, engine='xlrd')
    
    # シート数チェック（異常に多いシートは拒否）
    MAX_SHEETS = 100
    if len(xls_file.sheet_names) > MAX_SHEETS:
        raise ValueError(f"シート数が多すぎます（最大{MAX_SHEETS}シート）")
    
    # Excelライターを作成
    with pd.ExcelWriter(xlsx_buffer, engine='openpyxl') as writer:
        # 全シートを変換
        for sheet_name in xls_file.sheet_names:
            # シート名の検証（Excelの制限: 31文字）
            if len(sheet_name) > 31:
                sheet_name = sheet_name[:31]
            
            df = pd.read_excel(xls_file, sheet_name=sheet_name)
            
            # データサイズチェック
            if len(df) > 1000000:  # 100万行を超える場合は警告
                logging.warning(f"Large dataset: {len(df)} rows in sheet '{sheet_name}'")
            
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
    connection_string = os.environ.get('AzureWebJobsStorage', 'UseDevelopmentStorage=true')

    # BlobServiceClientを作成
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # コンテナとBlobの参照を取得
    container_name = 'xls-output'
    
    # コンテナが存在しない場合は作成（プライベートアクセス）
    try:
        container_client = blob_service_client.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()
            # パブリックアクセスを明示的に無効化
            container_client.set_container_access_policy(
                signed_identifiers={},
                public_access=None
            )
    except Exception as e:
        logging.warning(f"コンテナ作成チェックエラー（無視可能）: {str(e)}")
    
    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=filename
    )
    
    # アップロード（メタデータ付き）
    blob_client.upload_blob(
        data,
        overwrite=True,
        metadata={
            'original_size': str(len(data)),
            'upload_time': datetime.utcnow().isoformat(),
            'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
    )
    
    # SASトークンを生成（1時間有効）
    # ローカル開発環境（Azurite）ではSAS生成をスキップ
    if 'UseDevelopmentStorage' in connection_string or '127.0.0.1' in connection_string:
        # Azurite用のURL（SASなし）
        download_url = f"{blob_client.url}"
    else:
        # Azure本番環境用のSAS付きURL
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=container_name,
            blob_name=filename,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1)
        )
        download_url = f"{blob_client.url}?{sas_token}"

    return download_url


def create_file_response(data: bytes, filename: str) -> func.HttpResponse:
    """
    ファイルダウンロード用のHTTPレスポンスを作成（セキュリティヘッダー付き）
    
    Args:
        data: ファイルデータ
        filename: ファイル名
        
    Returns:
        HTTPレスポンス
    """
    headers = {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': f'attachment; filename="{filename}"',
        **get_security_headers()
    }
    
    return func.HttpResponse(data, status_code=200, headers=headers)


def create_json_response(data: dict) -> func.HttpResponse:
    """
    JSON HTTPレスポンスを作成（セキュリティヘッダー付き）
    
    Args:
        data: JSONデータ
        
    Returns:
        HTTPレスポンス
    """
    import json
    
    headers = {
        'Content-Type': 'application/json',
        **get_security_headers()
    }
    
    return func.HttpResponse(
        json.dumps(data, ensure_ascii=False),
        status_code=200,
        headers=headers
    )


def create_error_response(message: str, status_code: int) -> func.HttpResponse:
    """
    エラーレスポンスを作成（セキュリティヘッダー付き）
    
    Args:
        message: エラーメッセージ
        status_code: HTTPステータスコード
        
    Returns:
        HTTPレスポンス
    """
    headers = get_security_headers()
    
    return func.HttpResponse(
        message,
        status_code=status_code,
        headers=headers
    )
