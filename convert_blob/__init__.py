import azure.functions as func
import pandas as pd
import logging
import io
import os
from azure.storage.blob import BlobServiceClient
from security_utils import validate_xls_format, log_security_event

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
        
        # ファイル形式検証（マジックナンバーチェック）
        if not validate_xls_format(xls_data):
            log_security_event('invalid_xls_format', {'blob_name': inputblob.name})
            logging.error(f"Invalid XLS format detected: {inputblob.name}")
            return

        # XLSXに変換
        xlsx_data = convert_xls_to_xlsx(xls_data)

        # 出力コンテナに保存
        save_to_output_container(xlsx_data, output_name)

        logging.info(f"Successfully converted {original_name} to {output_name}")

    except Exception as e:
        logging.error(f"変換エラー: {str(e)}", exc_info=True)
        log_security_event('blob_conversion_error', {
            'blob_name': inputblob.name,
            'error': str(e)
        })
        raise


def convert_xls_to_xlsx(xls_data: bytes) -> bytes:
    """
    XLSバイナリデータをXLSXバイナリデータに変換

    Args:
        xls_data: XLSファイルのバイナリデータ

    Returns:
        XLSXファイルのバイナリデータ
        
    Raises:
        ValueError: データサイズ/シート数制限超過
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


def save_to_output_container(data: bytes, filename: str):
    """
    出力コンテナにファイルを保存

    Args:
        data: ファイルのバイナリデータ
        filename: 保存するファイル名
    """
    # 接続文字列を取得
    connection_string = os.environ.get('AzureWebJobsStorage', 'UseDevelopmentStorage=true')

    # BlobServiceClientを作成
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # コンテナが存在しない場合は作成（プライベートアクセス）
    container_name = 'xls-output'
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

    # 出力コンテナにアップロード
    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=filename
    )

    blob_client.upload_blob(data, overwrite=True)
    logging.info(f"Saved to xls-output/{filename}")
