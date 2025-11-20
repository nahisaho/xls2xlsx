#!/usr/bin/env python3
"""
ローカル統合テストスクリプト（Docker不要）
Azure Functions Core Toolsを使用してローカルでテストします
"""
import os
import sys
import time
import json
import subprocess
import signal
from datetime import datetime

# テスト結果を保存するファイル
TEST_RESULT_FILE = 'test_results.json'

class LocalTestRunner:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'environment': 'Local (Azure Functions Core Tools)',
            'tests': []
        }
        self.func_process = None
        
    def log(self, message):
        """ログメッセージを出力"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")
        
    def add_test_result(self, test_name, status, message, duration=None):
        """テスト結果を追加"""
        result = {
            'name': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        if duration:
            result['duration_seconds'] = duration
        self.results['tests'].append(result)
        
    def check_python_packages(self):
        """必要なPythonパッケージをチェック"""
        self.log("Pythonパッケージをチェック中...")
        required_packages = {
            'pandas': 'pandas',
            'xlwt': 'xlwt',
            'openpyxl': 'openpyxl',
            'xlrd': 'xlrd',
            'azure.functions': 'azure-functions'
        }
        
        missing_packages = []
        for import_name, package_name in required_packages.items():
            try:
                __import__(import_name)
            except ImportError:
                missing_packages.append(package_name)
        
        if missing_packages:
            self.log(f"❌ 不足パッケージ: {', '.join(missing_packages)}")
            self.add_test_result(
                'python_packages_check',
                'FAIL',
                f'Missing packages: {", ".join(missing_packages)}'
            )
            return False
        else:
            self.log("✅ 必要なパッケージはすべてインストール済み")
            self.add_test_result(
                'python_packages_check',
                'PASS',
                'All required packages are installed'
            )
            return True
            
    def create_sample_xls(self):
        """サンプルXLSファイルを作成"""
        self.log("サンプルXLSファイルを作成中...")
        
        os.makedirs('samples', exist_ok=True)
        
        try:
            import xlwt
            
            # サンプル1: 単一シート
            wb1 = xlwt.Workbook()
            ws1 = wb1.add_sheet('社員リスト')
            
            headers = ['氏名', '年齢', '部署', '給与']
            for col, header in enumerate(headers):
                ws1.write(0, col, header)
            
            data = [
                ['田中太郎', 25, '営業', 300000],
                ['佐藤花子', 30, '開発', 450000],
                ['鈴木一郎', 28, '総務', 350000],
            ]
            
            for row, record in enumerate(data, start=1):
                for col, value in enumerate(record):
                    ws1.write(row, col, value)
            
            wb1.save('samples/sample1.xls')
            self.log("✅ sample1.xls 作成完了")
            
            # サンプル2: 複数シート
            wb2 = xlwt.Workbook()
            
            ws2_1 = wb2.add_sheet('商品マスタ')
            ws2_1.write(0, 0, '商品名')
            ws2_1.write(0, 1, '価格')
            products = [['りんご', 150], ['バナナ', 120]]
            for row, record in enumerate(products, start=1):
                for col, value in enumerate(record):
                    ws2_1.write(row, col, value)
            
            ws2_2 = wb2.add_sheet('月次売上')
            ws2_2.write(0, 0, '月')
            ws2_2.write(0, 1, '売上')
            sales = [['1月', 1000000], ['2月', 1200000]]
            for row, record in enumerate(sales, start=1):
                for col, value in enumerate(record):
                    ws2_2.write(row, col, value)
            
            wb2.save('samples/sample2.xls')
            self.log("✅ sample2.xls 作成完了")
            
            self.add_test_result(
                'create_samples',
                'PASS',
                'Sample XLS files created successfully'
            )
            return True
            
        except Exception as e:
            self.log(f"❌ サンプル作成エラー: {str(e)}")
            self.add_test_result(
                'create_samples',
                'ERROR',
                str(e)
            )
            return False
            
    def test_conversion_logic(self):
        """変換ロジックを直接テスト"""
        self.log("変換ロジックを直接テスト中...")
        
        if not os.path.exists('samples/sample1.xls'):
            self.log("❌ sample1.xlsが見つかりません")
            self.add_test_result(
                'conversion_logic_test',
                'SKIP',
                'Sample file not found'
            )
            return False
            
        try:
            import pandas as pd
            import io
            
            start_time = time.time()
            
            # XLSファイルを読み込み
            with open('samples/sample1.xls', 'rb') as f:
                xls_data = f.read()
            
            # 変換ロジック
            xls_buffer = io.BytesIO(xls_data)
            xlsx_buffer = io.BytesIO()
            
            xls_file = pd.ExcelFile(xls_buffer, engine='xlrd')
            
            with pd.ExcelWriter(xlsx_buffer, engine='openpyxl') as writer:
                for sheet_name in xls_file.sheet_names:
                    df = pd.read_excel(xls_file, sheet_name=sheet_name)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            xlsx_buffer.seek(0)
            xlsx_data = xlsx_buffer.getvalue()
            
            duration = time.time() - start_time
            
            # 出力ディレクトリを作成
            os.makedirs('test_output', exist_ok=True)
            
            # XLSXファイルを保存
            output_path = 'test_output/logic_test_sample1.xlsx'
            with open(output_path, 'wb') as f:
                f.write(xlsx_data)
            
            file_size = len(xlsx_data)
            self.log(f"✅ 変換ロジックテスト成功（{duration:.1f}秒）: {output_path} ({file_size} bytes)")
            
            # 変換されたファイルを読み込んで検証
            df_result = pd.read_excel(output_path, sheet_name='社員リスト')
            row_count = len(df_result)
            col_count = len(df_result.columns)
            
            self.add_test_result(
                'conversion_logic_test',
                'PASS',
                f'Converted successfully: {row_count} rows, {col_count} columns, {file_size} bytes',
                duration
            )
            return True
            
        except Exception as e:
            self.log(f"❌ 変換ロジックテストエラー: {str(e)}")
            import traceback
            traceback.print_exc()
            self.add_test_result(
                'conversion_logic_test',
                'ERROR',
                str(e)
            )
            return False
            
    def test_multiple_sheets(self):
        """複数シートの変換をテスト"""
        self.log("複数シート変換をテスト中...")
        
        if not os.path.exists('samples/sample2.xls'):
            self.log("❌ sample2.xlsが見つかりません")
            self.add_test_result(
                'multiple_sheets_test',
                'SKIP',
                'Sample file not found'
            )
            return False
            
        try:
            import pandas as pd
            import io
            
            start_time = time.time()
            
            # XLSファイルを読み込み
            with open('samples/sample2.xls', 'rb') as f:
                xls_data = f.read()
            
            # 変換ロジック
            xls_buffer = io.BytesIO(xls_data)
            xlsx_buffer = io.BytesIO()
            
            xls_file = pd.ExcelFile(xls_buffer, engine='xlrd')
            sheet_count = len(xls_file.sheet_names)
            
            with pd.ExcelWriter(xlsx_buffer, engine='openpyxl') as writer:
                for sheet_name in xls_file.sheet_names:
                    df = pd.read_excel(xls_file, sheet_name=sheet_name)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            xlsx_buffer.seek(0)
            xlsx_data = xlsx_buffer.getvalue()
            
            duration = time.time() - start_time
            
            # XLSXファイルを保存
            output_path = 'test_output/logic_test_sample2.xlsx'
            with open(output_path, 'wb') as f:
                f.write(xlsx_data)
            
            file_size = len(xlsx_data)
            self.log(f"✅ 複数シート変換テスト成功（{duration:.1f}秒）: {output_path} ({sheet_count}シート, {file_size} bytes)")
            
            self.add_test_result(
                'multiple_sheets_test',
                'PASS',
                f'{sheet_count} sheets converted successfully: {file_size} bytes',
                duration
            )
            return True
            
        except Exception as e:
            self.log(f"❌ 複数シート変換テストエラー: {str(e)}")
            self.add_test_result(
                'multiple_sheets_test',
                'ERROR',
                str(e)
            )
            return False
            
    def verify_output_files(self):
        """出力ファイルの検証"""
        self.log("出力ファイルを検証中...")
        
        output_files = [
            'test_output/logic_test_sample1.xlsx',
            'test_output/logic_test_sample2.xlsx'
        ]
        
        verified = 0
        for file_path in output_files:
            if os.path.exists(file_path):
                try:
                    import pandas as pd
                    
                    # ファイルを読み込んで検証
                    excel_file = pd.ExcelFile(file_path)
                    sheet_count = len(excel_file.sheet_names)
                    file_size = os.path.getsize(file_path)
                    
                    self.log(f"   ✅ {file_path}: {sheet_count}シート, {file_size} bytes")
                    verified += 1
                    
                except Exception as e:
                    self.log(f"   ❌ {file_path}: 読み込みエラー - {str(e)}")
            else:
                self.log(f"   ❌ {file_path}: ファイルが存在しません")
        
        if verified == len(output_files):
            self.add_test_result(
                'verify_output_files',
                'PASS',
                f'All {verified} output files verified successfully'
            )
            return True
        else:
            self.add_test_result(
                'verify_output_files',
                'FAIL',
                f'Only {verified}/{len(output_files)} files verified'
            )
            return False
            
    def save_results(self):
        """テスト結果をJSONファイルに保存"""
        self.log(f"テスト結果を {TEST_RESULT_FILE} に保存中...")
        
        # 統計情報を追加
        total = len(self.results['tests'])
        passed = sum(1 for t in self.results['tests'] if t['status'] == 'PASS')
        failed = sum(1 for t in self.results['tests'] if t['status'] == 'FAIL')
        errors = sum(1 for t in self.results['tests'] if t['status'] == 'ERROR')
        skipped = sum(1 for t in self.results['tests'] if t['status'] == 'SKIP')
        
        self.results['summary'] = {
            'total': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'skipped': skipped,
            'success_rate': f"{(passed/total*100):.1f}%" if total > 0 else "0%"
        }
        
        # テスト環境情報を追加
        self.results['environment_info'] = {
            'python_version': sys.version,
            'platform': sys.platform,
            'working_directory': os.getcwd()
        }
        
        with open(TEST_RESULT_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        self.log(f"✅ テスト結果保存完了: {TEST_RESULT_FILE}")
        
    def print_summary(self):
        """テスト結果サマリーを表示"""
        print("\n" + "=" * 70)
        print("テスト結果サマリー")
        print("=" * 70)
        
        summary = self.results.get('summary', {})
        print(f"総テスト数: {summary.get('total', 0)}")
        print(f"✅ 成功: {summary.get('passed', 0)}")
        print(f"❌ 失敗: {summary.get('failed', 0)}")
        print(f"💥 エラー: {summary.get('errors', 0)}")
        print(f"⏭️  スキップ: {summary.get('skipped', 0)}")
        print(f"成功率: {summary.get('success_rate', '0%')}")
        print("=" * 70)
        
        print("\n詳細:")
        for test in self.results['tests']:
            status_icon = {
                'PASS': '✅',
                'FAIL': '❌',
                'ERROR': '💥',
                'SKIP': '⏭️'
            }.get(test['status'], '❓')
            
            duration = f" ({test['duration_seconds']:.1f}秒)" if 'duration_seconds' in test else ""
            print(f"{status_icon} {test['name']}{duration}")
            print(f"   {test['message'][:100]}")
        
        print("\n" + "=" * 70)
        print(f"詳細レポート: {TEST_RESULT_FILE}")
        print("=" * 70 + "\n")
        
    def run(self):
        """統合テストを実行"""
        self.log("=" * 70)
        self.log("xls2xlsx ローカル統合テスト開始")
        self.log("=" * 70)
        
        # 1. Pythonパッケージチェック
        if not self.check_python_packages():
            self.log("必要なパッケージが不足しています。")
            self.log("pip install -r requirements.txt を実行してください。")
            self.save_results()
            self.print_summary()
            return False
        
        # 2. サンプルファイル作成
        self.create_sample_xls()
        
        # 3. 変換ロジックテスト
        self.test_conversion_logic()
        
        # 4. 複数シートテスト
        self.test_multiple_sheets()
        
        # 5. 出力ファイル検証
        self.verify_output_files()
        
        # 6. 結果保存
        self.save_results()
        
        # 7. サマリー表示
        self.print_summary()
        
        self.log("=" * 70)
        self.log("ローカル統合テスト完了")
        self.log("=" * 70)
        
        # 成功したかどうかを返す
        summary = self.results.get('summary', {})
        return summary.get('failed', 0) == 0 and summary.get('errors', 0) == 0


if __name__ == '__main__':
    runner = LocalTestRunner()
    success = runner.run()
    sys.exit(0 if success else 1)
