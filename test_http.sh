#!/bin/bash

# テストスクリプト - Docker環境でのHTTPトリガーテスト

echo "=== xls2xlsx Docker Test Script ==="
echo ""

# 関数のURLを設定
FUNCTION_URL="http://localhost:8080/api/convert_http"

# テスト対象のファイル
TEST_FILE="samples/sample1.xls"

if [ ! -f "$TEST_FILE" ]; then
    echo "❌ Error: $TEST_FILE が見つかりません。"
    echo "先に create_samples.py を実行してください。"
    exit 1
fi

echo "📤 Testing HTTP trigger with $TEST_FILE..."
echo ""

# 出力ディレクトリを作成
mkdir -p test_output

# curlでテスト
curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/octet-stream" \
  -H "X-Filename: sample1.xls" \
  --data-binary "@$TEST_FILE" \
  --output test_output/converted_sample1.xlsx \
  -w "\nHTTP Status: %{http_code}\n"

echo ""

# 結果を確認
if [ -f "test_output/converted_sample1.xlsx" ]; then
    FILE_SIZE=$(stat -c%s "test_output/converted_sample1.xlsx" 2>/dev/null || stat -f%z "test_output/converted_sample1.xlsx" 2>/dev/null)
    echo "✅ 変換成功！"
    echo "   出力ファイル: test_output/converted_sample1.xlsx"
    echo "   ファイルサイズ: $FILE_SIZE bytes"
else
    echo "❌ 変換失敗"
fi

echo ""
echo "=== テスト完了 ==="
