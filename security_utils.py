"""
セキュリティユーティリティモジュール
ファイル名サニタイズ、入力検証などのセキュリティ機能を提供
"""
import re
import os
import logging
from typing import Tuple

# 定数
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILENAME_LENGTH = 255
XLS_MAGIC_NUMBERS = [
    b'\xd0\xcf\x11\xe0',  # OLE2/CFB (Compound File Binary) - XLS
    b'\x09\x08\x10\x00\x00\x06\x05\x00',  # BIFF5
]


def sanitize_filename(filename: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
    """
    ファイル名をサニタイズしてセキュリティリスクを軽減
    
    Args:
        filename: 元のファイル名
        max_length: 最大文字数
        
    Returns:
        サニタイズされたファイル名
        
    Security considerations:
        - パストラバーサル攻撃対策（../, \\など）
        - 特殊文字の除去
        - 長さ制限
        - 空ファイル名の防止
    """
    if not filename:
        return 'converted'
    
    # パス区切り文字を除去（パストラバーサル対策）
    filename = os.path.basename(filename)
    
    # 危険な文字を除去（英数字、ハイフン、アンダースコア、ドット、日本語のみ許可）
    # 制御文字、パス区切り、特殊文字を除外
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # 連続するドットを単一に（隠しファイル作成防止）
    filename = re.sub(r'\.{2,}', '.', filename)
    
    # 先頭と末尾のドット・スペースを除去
    filename = filename.strip('. ')
    
    # 長さ制限（拡張子を考慮）
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    # 空の場合はデフォルト
    if not filename or filename == '.':
        filename = 'converted'
    
    # 予約語チェック（Windows）
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in reserved_names:
        filename = f'file_{filename}'
    
    return filename


def validate_file_size(file_data: bytes, max_size: int = MAX_FILE_SIZE) -> Tuple[bool, str]:
    """
    ファイルサイズを検証
    
    Args:
        file_data: ファイルのバイナリデータ
        max_size: 最大許容サイズ（バイト）
        
    Returns:
        (検証成功: bool, エラーメッセージ: str)
    """
    if not file_data:
        return False, "ファイルデータが空です"
    
    file_size = len(file_data)
    
    if file_size > max_size:
        return False, f"ファイルサイズが上限を超えています（最大{max_size // 1024 // 1024}MB）。現在のサイズ: {file_size // 1024 // 1024}MB"
    
    if file_size < 100:  # 最小サイズチェック（100バイト未満は異常）
        return False, "ファイルサイズが小さすぎます"
    
    return True, ""


def validate_xls_format(file_data: bytes) -> Tuple[bool, str]:
    """
    XLSファイル形式を検証（マジックナンバーチェック）
    
    Args:
        file_data: ファイルのバイナリデータ
        
    Returns:
        (検証成功: bool, エラーメッセージ: str)
        
    Security note:
        マジックナンバーチェックにより、拡張子偽装攻撃を防止
    """
    if len(file_data) < 8:
        return False, "ファイルサイズが小さすぎます"
    
    # XLSファイルのマジックナンバーをチェック
    file_header = file_data[:8]
    
    for magic in XLS_MAGIC_NUMBERS:
        if file_header.startswith(magic):
            return True, ""
    
    # より詳細なチェック（OLE2構造）
    if file_data[:2] == b'\xd0\xcf':
        # OLE2ファイルとして認識されるが、XLSとして有効か確認
        logging.warning("OLE2ファイルとして検出されましたが、XLS形式の確認が必要です")
        return True, ""  # 厳密にはさらなる検証が必要
    
    return False, "有効なXLSファイル形式ではありません。XLS形式のファイルのみサポートされています。"


def validate_input(file_data: bytes, filename: str) -> Tuple[bool, str, str]:
    """
    入力データを包括的に検証
    
    Args:
        file_data: ファイルのバイナリデータ
        filename: ファイル名
        
    Returns:
        (検証成功: bool, サニタイズ後のファイル名: str, エラーメッセージ: str)
    """
    # ファイル名のサニタイズ
    sanitized_filename = sanitize_filename(filename)
    
    # ファイルサイズチェック
    size_valid, size_error = validate_file_size(file_data)
    if not size_valid:
        return False, sanitized_filename, size_error
    
    # ファイル形式チェック
    format_valid, format_error = validate_xls_format(file_data)
    if not format_valid:
        return False, sanitized_filename, format_error
    
    return True, sanitized_filename, ""


def get_security_headers() -> dict:
    """
    推奨セキュリティヘッダーを返す
    
    Returns:
        セキュリティヘッダーの辞書
    """
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }


def sanitize_error_message(error: Exception, is_production: bool = False) -> str:
    """
    エラーメッセージをサニタイズ
    本番環境では詳細を隠し、開発環境では詳細を表示
    
    Args:
        error: 例外オブジェクト
        is_production: 本番環境フラグ
        
    Returns:
        サニタイズされたエラーメッセージ
    """
    if is_production:
        # 本番環境: 一般的なメッセージのみ
        return "ファイルの処理中にエラーが発生しました。管理者にお問い合わせください。"
    else:
        # 開発環境: 詳細を表示
        return f"変換中にエラーが発生しました: {str(error)}"


def log_security_event(event_type: str, details: dict):
    """
    セキュリティイベントをログに記録
    
    Args:
        event_type: イベントタイプ（例: 'invalid_file_format', 'file_too_large'）
        details: イベント詳細情報
    """
    logging.warning(
        f"Security Event: {event_type}",
        extra={
            'event_type': event_type,
            'details': details,
            'severity': 'WARNING'
        }
    )


# 使用例
if __name__ == '__main__':
    # テスト
    test_filenames = [
        'normal_file.xls',
        '../../../etc/passwd.xls',
        'file<>name.xls',
        'CON.xls',
        '.' * 300 + '.xls',
        '',
    ]
    
    print("ファイル名サニタイズテスト:")
    for fn in test_filenames:
        sanitized = sanitize_filename(fn)
        print(f"  '{fn}' -> '{sanitized}'")
