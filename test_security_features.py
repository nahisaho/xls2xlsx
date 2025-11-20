#!/usr/bin/env python3
"""
セキュリティ機能の検証テスト
"""
import sys
import os
from security_utils import (
    sanitize_filename,
    validate_file_size,
    validate_xls_format,
    get_security_headers,
    sanitize_error_message,
    validate_input
)

def test_filename_sanitization():
    """ファイル名サニタイズのテスト"""
    print("\n[TEST] ファイル名サニタイズ")
    
    test_cases = [
        ("normal.xls", "normal.xls", True),
        ("../../../etc/passwd", "passwd", True),  # パス部分は除去される
        ("file/../../../secret.xls", "secret.xls", True),  # 同上
        ("a" * 300 + ".xls", "a" * 251 + ".xls", True),  # 255文字制限
        ("file\x00name.xls", "file_name.xls", True),
        ("", "converted", True),  # 空の場合はconvertedになる
    ]
    
    passed = 0
    for input_name, expected, should_pass in test_cases:
        result = sanitize_filename(input_name)
        if should_pass and result == expected:
            print(f"  ✅ '{input_name[:30]}...' → '{result[:30]}...'")
            passed += 1
        else:
            print(f"  ❌ '{input_name[:30]}...' → '{result}' (期待: '{expected}')")
    
    print(f"  結果: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_file_size_validation():
    """ファイルサイズ検証のテスト"""
    print("\n[TEST] ファイルサイズ検証")
    
    test_cases = [
        (b'\x00' * 100, True, ""),                           # 正常: 100 bytes
        (b'\x00' * (50 * 1024 * 1024), True, ""),            # 正常: 50 MB
        (b'\x00' * (50 * 1024 * 1024), True, ""),            # 正常: 50 MB (上限)
        (b'\x00' * (51 * 1024 * 1024), False, "上限を超えています"),  # エラー: 51 MB
        (b'', False, "空です"),                               # エラー: 0 bytes
    ]
    
    passed = 0
    for data, should_pass, error_keyword in test_cases:
        is_valid, error_msg = validate_file_size(data)
        
        if should_pass and is_valid:
            print(f"  ✅ {len(data):,} bytes → OK")
            passed += 1
        elif not should_pass and not is_valid and error_keyword in error_msg:
            print(f"  ✅ {len(data):,} bytes → 拒否: {error_msg}")
            passed += 1
        else:
            print(f"  ❌ {len(data):,} bytes → is_valid={is_valid}, error='{error_msg}'")
    
    print(f"  結果: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_xls_format_validation():
    """XLSフォーマット検証のテスト"""
    print("\n[TEST] XLSフォーマット検証")
    
    # XLSマジックナンバー: D0 CF 11 E0 A1 B1 1A E1
    valid_xls = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1' + b'\x00' * 100
    invalid_data = b'PK\x03\x04' + b'\x00' * 100  # ZIPファイル (XLSX)
    
    test_cases = [
        (valid_xls, True, "有効なXLS"),
        (invalid_data, False, "無効なデータ"),
        (b'', False, "空データ"),
        (b'short', False, "短すぎるデータ"),
    ]
    
    passed = 0
    for data, expected, description in test_cases:
        # validate_xls_formatはタプル (bool, str) を返す
        result_tuple = validate_xls_format(data)
        result = result_tuple[0] if isinstance(result_tuple, tuple) else result_tuple
        
        if result == expected:
            status = "✅" if expected else "✅(正しく拒否)"
            print(f"  {status} {description}: {len(data)} bytes → {result}")
            passed += 1
        else:
            print(f"  ❌ {description}: expected={expected}, got={result}")
    
    print(f"  結果: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_security_headers():
    """セキュリティヘッダーのテスト"""
    print("\n[TEST] セキュリティヘッダー")
    
    headers = get_security_headers()
    
    required_headers = [
        'X-Content-Type-Options',
        'X-Frame-Options',
        'X-XSS-Protection',
        'Strict-Transport-Security',
        'Content-Security-Policy'
    ]
    
    passed = 0
    for header in required_headers:
        if header in headers:
            print(f"  ✅ {header}: {headers[header]}")
            passed += 1
        else:
            print(f"  ❌ {header}: 未設定")
    
    print(f"  結果: {passed}/{len(required_headers)} passed")
    return passed == len(required_headers)


def test_error_message_sanitization():
    """エラーメッセージサニタイズのテスト"""
    print("\n[TEST] エラーメッセージサニタイズ")
    
    # テスト用例外
    test_error = ValueError("Database connection failed: user=admin, password=secret123, host=192.168.1.100")
    
    # 本番環境: 詳細を隠す
    prod_message = sanitize_error_message(test_error, is_production=True)
    dev_message = sanitize_error_message(test_error, is_production=False)
    
    passed = 0
    
    # 本番環境のメッセージに機密情報が含まれていないことを確認
    if "secret123" not in prod_message and "192.168.1.100" not in prod_message:
        print(f"  ✅ 本番環境: 機密情報を隠蔽")
        print(f"     → '{prod_message}'")
        passed += 1
    else:
        print(f"  ❌ 本番環境: 機密情報が漏洩")
    
    # 開発環境では詳細を表示（ただし完全なエラーではなくエラータイプが含まれる）
    if "ValueError" in dev_message or "Database" in dev_message:
        print(f"  ✅ 開発環境: 詳細情報を表示")
        print(f"     → '{dev_message[:80]}...'")
        passed += 1
    else:
        print(f"  ❌ 開発環境: 詳細情報が不足")
        print(f"     → '{dev_message}'")
    
    print(f"  結果: {passed}/2 passed")
    return passed == 2


def test_complete_input_validation():
    """総合入力検証のテスト"""
    print("\n[TEST] 総合入力検証")
    
    # 有効なXLSデータ
    valid_xls = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1' + b'\x00' * 1000
    
    test_cases = [
        (valid_xls, "normal.xls", True, "正常なケース"),
        (valid_xls, "../../../etc/passwd", True, "パストラバーサル試行"),
        (b'invalid', "normal.xls", False, "無効なXLSフォーマット"),
        (b'\xD0\xCF\x11\xE0' * 60000000, "huge.xls", False, "ファイルが大きすぎる"),
    ]
    
    passed = 0
    for data, filename, should_pass, description in test_cases:
        is_valid, sanitized_name, error_msg = validate_input(data, filename)
        
        if should_pass and is_valid:
            print(f"  ✅ {description}")
            print(f"     → サニタイズ後: '{sanitized_name}'")
            passed += 1
        elif not should_pass and not is_valid:
            print(f"  ✅ {description} (正しく拒否)")
            print(f"     → エラー: {error_msg}")
            passed += 1
        else:
            print(f"  ❌ {description}")
            print(f"     → is_valid={is_valid}, error='{error_msg}'")
    
    print(f"  結果: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def main():
    """メインテスト実行"""
    print("=" * 70)
    print("セキュリティ機能検証テスト")
    print("=" * 70)
    
    tests = [
        ("ファイル名サニタイズ", test_filename_sanitization),
        ("ファイルサイズ検証", test_file_size_validation),
        ("XLSフォーマット検証", test_xls_format_validation),
        ("セキュリティヘッダー", test_security_headers),
        ("エラーメッセージサニタイズ", test_error_message_sanitization),
        ("総合入力検証", test_complete_input_validation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n  ❌ テスト実行エラー: {e}")
            results.append((test_name, False))
    
    # サマリー
    print("\n" + "=" * 70)
    print("テスト結果サマリー")
    print("=" * 70)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("=" * 70)
    print(f"総合結果: {passed_count}/{total_count} テスト成功 ({passed_count/total_count*100:.0f}%)")
    print("=" * 70)
    
    return 0 if passed_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
