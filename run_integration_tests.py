#!/usr/bin/env python3
"""
統合テストスクリプト
Docker環境でHTTPトリガーとBlobトリガーをテストします
"""
import os
import sys
import time
import json
import subprocess
from datetime import datetime

# テスト結果を保存するファイル
TEST_RESULT_FILE = 'test_results.json'

class TestRunner:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'environment': 'Docker',
            'tests': []
        }
        
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
        
    def check_docker(self):
        """Dockerが利用可能かチェック"""
        self.log("Docker環境をチェック中...")
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.log(f"✅ Docker検出: {result.stdout.strip()}")
                self.add_test_result(
                    'docker_check',
                    'PASS',
                    result.stdout.strip()
                )
                return True
            else:
                self.log("❌ Dockerが見つかりません")
                self.add_test_result(
                    'docker_check',
                    'FAIL',
                    'Docker not found'
                )
                return False
        except Exception as e:
            self.log(f"❌ Dockerチェックエラー: {str(e)}")
            self.add_test_result(
                'docker_check',
                'ERROR',
                str(e)
            )
            return False
            
    def check_docker_compose(self):
        """Docker Composeが利用可能かチェック"""
        self.log("Docker Compose環境をチェック中...")
        try:
            result = subprocess.run(
                ['docker', 'compose', 'version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.log(f"✅ Docker Compose検出: {result.stdout.strip()}")
                self.add_test_result(
                    'docker_compose_check',
                    'PASS',
                    result.stdout.strip()
                )
                return True
            else:
                self.log("❌ Docker Composeが見つかりません")
                self.add_test_result(
                    'docker_compose_check',
                    'FAIL',
                    'Docker Compose not found'
                )
                return False
        except Exception as e:
            self.log(f"❌ Docker Composeチェックエラー: {str(e)}")
            self.add_test_result(
                'docker_compose_check',
                'ERROR',
                str(e)
            )
            return False
            
    def create_sample_xls_simple(self):
        """シンプルなXLSファイルを作成（xlwtなしで）"""
        self.log("サンプルXLSファイルを作成中...")
        
        # samplesディレクトリを作成
        os.makedirs('samples', exist_ok=True)
        
        # xlwtをインポートして使用
        try:
            import xlwt
            
            # サンプル1: 単一シート
            wb1 = xlwt.Workbook()
            ws1 = wb1.add_sheet('社員リスト')
            
            # ヘッダー
            headers = ['氏名', '年齢', '部署', '給与']
            for col, header in enumerate(headers):
                ws1.write(0, col, header)
            
            # データ
            data = [
                ['田中太郎', 25, '営業', 300000],
                ['佐藤花子', 30, '開発', 450000],
                ['鈴木一郎', 28, '総務', 350000],
                ['高橋美咲', 22, '営業', 280000],
                ['伊藤健太', 35, '開発', 500000]
            ]
            
            for row, record in enumerate(data, start=1):
                for col, value in enumerate(record):
                    ws1.write(row, col, value)
            
            wb1.save('samples/sample1.xls')
            self.log("✅ sample1.xls 作成完了")
            
            # サンプル2: 複数シート
            wb2 = xlwt.Workbook()
            
            # シート1
            ws2_1 = wb2.add_sheet('商品マスタ')
            ws2_1.write(0, 0, '商品名')
            ws2_1.write(0, 1, '価格')
            ws2_1.write(0, 2, '在庫')
            products = [
                ['りんご', 150, 100],
                ['バナナ', 120, 150],
                ['オレンジ', 180, 80]
            ]
            for row, record in enumerate(products, start=1):
                for col, value in enumerate(record):
                    ws2_1.write(row, col, value)
            
            # シート2
            ws2_2 = wb2.add_sheet('月次売上')
            ws2_2.write(0, 0, '月')
            ws2_2.write(0, 1, '売上')
            sales = [
                ['1月', 1000000],
                ['2月', 1200000],
                ['3月', 1500000]
            ]
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
            
        except ImportError:
            self.log("❌ xlwtパッケージが見つかりません")
            self.add_test_result(
                'create_samples',
                'SKIP',
                'xlwt not installed'
            )
            return False
        except Exception as e:
            self.log(f"❌ サンプル作成エラー: {str(e)}")
            self.add_test_result(
                'create_samples',
                'ERROR',
                str(e)
            )
            return False
            
    def start_docker_compose(self):
        """Docker Composeで環境を起動"""
        self.log("Docker Compose環境を起動中...")
        try:
            # 既存のコンテナを停止
            subprocess.run(
                ['docker', 'compose', 'down'],
                capture_output=True,
                timeout=30
            )
            
            start_time = time.time()
            
            # コンテナを起動
            result = subprocess.run(
                ['docker', 'compose', 'up', '-d', '--build'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                self.log(f"✅ Docker Compose起動完了 ({duration:.1f}秒)")
                
                # コンテナの起動を待つ
                self.log("コンテナの起動を待機中...")
                time.sleep(15)
                
                self.add_test_result(
                    'docker_compose_up',
                    'PASS',
                    'Docker Compose started successfully',
                    duration
                )
                return True
            else:
                self.log(f"❌ Docker Compose起動失敗: {result.stderr}")
                self.add_test_result(
                    'docker_compose_up',
                    'FAIL',
                    result.stderr
                )
                return False
                
        except Exception as e:
            self.log(f"❌ Docker Compose起動エラー: {str(e)}")
            self.add_test_result(
                'docker_compose_up',
                'ERROR',
                str(e)
            )
            return False
            
    def test_http_trigger(self):
        """HTTPトリガーをテスト"""
        self.log("HTTPトリガーをテスト中...")
        
        if not os.path.exists('samples/sample1.xls'):
            self.log("❌ sample1.xlsが見つかりません")
            self.add_test_result(
                'http_trigger_test',
                'SKIP',
                'Sample file not found'
            )
            return False
            
        try:
            import requests
            
            os.makedirs('test_output', exist_ok=True)
            
            start_time = time.time()
            
            # HTTPリクエストを送信
            with open('samples/sample1.xls', 'rb') as f:
                response = requests.post(
                    'http://localhost:8080/api/convert_http',
                    headers={
                        'Content-Type': 'application/octet-stream',
                        'X-Filename': 'sample1.xls'
                    },
                    data=f,
                    timeout=60
                )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                # レスポンスがXLSXファイルかJSONか確認
                content_type = response.headers.get('Content-Type', '')
                
                if 'application/json' in content_type:
                    # 大容量ファイル: JSONでURLが返る
                    json_response = response.json()
                    self.log(f"✅ HTTPトリガー成功（大容量）: {json_response}")
                    self.add_test_result(
                        'http_trigger_test',
                        'PASS',
                        f'Large file - Download URL returned: {json_response}',
                        duration
                    )
                else:
                    # 小容量ファイル: 直接XLSXが返る
                    output_path = 'test_output/http_converted_sample1.xlsx'
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    
                    file_size = len(response.content)
                    self.log(f"✅ HTTPトリガー成功（{duration:.1f}秒）: {output_path} ({file_size} bytes)")
                    self.add_test_result(
                        'http_trigger_test',
                        'PASS',
                        f'File converted successfully: {file_size} bytes',
                        duration
                    )
                
                return True
            else:
                self.log(f"❌ HTTPトリガー失敗: HTTP {response.status_code}")
                self.log(f"   レスポンス: {response.text[:200]}")
                self.add_test_result(
                    'http_trigger_test',
                    'FAIL',
                    f'HTTP {response.status_code}: {response.text[:200]}'
                )
                return False
                
        except Exception as e:
            self.log(f"❌ HTTPトリガーテストエラー: {str(e)}")
            self.add_test_result(
                'http_trigger_test',
                'ERROR',
                str(e)
            )
            return False
            
    def test_blob_trigger(self):
        """Blobトリガーをテスト"""
        self.log("Blobトリガーをテスト中...")
        
        if not os.path.exists('samples/sample2.xls'):
            self.log("❌ sample2.xlsが見つかりません")
            self.add_test_result(
                'blob_trigger_test',
                'SKIP',
                'Sample file not found'
            )
            return False
            
        try:
            from azure.storage.blob import BlobServiceClient
            
            # Azurite接続文字列
            connection_string = (
                "DefaultEndpointsProtocol=http;"
                "AccountName=devstoreaccount1;"
                "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
                "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
            )
            
            start_time = time.time()
            
            # BlobServiceClientを作成
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            
            # コンテナを作成
            for container_name in ['xls-input', 'xls-output']:
                try:
                    container_client = blob_service_client.get_container_client(container_name)
                    if not container_client.exists():
                        container_client.create_container()
                        self.log(f"   コンテナ作成: {container_name}")
                except Exception:
                    pass
            
            # ファイルをアップロード
            filename = 'sample2.xls'
            blob_client = blob_service_client.get_blob_client(
                container='xls-input',
                blob=filename
            )
            
            with open(f'samples/{filename}', 'rb') as data:
                blob_client.upload_blob(data, overwrite=True)
            
            self.log(f"   {filename} をxls-inputにアップロード完了")
            
            # Blobトリガーの実行を待つ
            self.log("   Blobトリガーの実行を待機中（15秒）...")
            time.sleep(15)
            
            # 変換結果を確認
            output_blob_name = 'sample2.xlsx'
            output_blob_client = blob_service_client.get_blob_client(
                container='xls-output',
                blob=output_blob_name
            )
            
            duration = time.time() - start_time
            
            if output_blob_client.exists():
                # ファイルをダウンロード
                os.makedirs('test_output', exist_ok=True)
                download_path = f'test_output/blob_converted_{output_blob_name}'
                
                with open(download_path, 'wb') as download_file:
                    download_file.write(output_blob_client.download_blob().readall())
                
                file_size = os.path.getsize(download_path)
                self.log(f"✅ Blobトリガー成功（{duration:.1f}秒）: {download_path} ({file_size} bytes)")
                self.add_test_result(
                    'blob_trigger_test',
                    'PASS',
                    f'File converted successfully: {file_size} bytes',
                    duration
                )
                return True
            else:
                self.log(f"❌ Blobトリガー失敗: 変換結果が見つかりません")
                self.add_test_result(
                    'blob_trigger_test',
                    'FAIL',
                    'Converted file not found in xls-output container'
                )
                return False
                
        except Exception as e:
            self.log(f"❌ Blobトリガーテストエラー: {str(e)}")
            self.add_test_result(
                'blob_trigger_test',
                'ERROR',
                str(e)
            )
            return False
            
    def cleanup(self):
        """環境をクリーンアップ"""
        self.log("環境をクリーンアップ中...")
        try:
            result = subprocess.run(
                ['docker', 'compose', 'down'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                self.log("✅ クリーンアップ完了")
                self.add_test_result(
                    'cleanup',
                    'PASS',
                    'Docker Compose stopped successfully'
                )
            else:
                self.log(f"⚠️  クリーンアップ警告: {result.stderr}")
                
        except Exception as e:
            self.log(f"⚠️  クリーンアップエラー: {str(e)}")
            
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
        
        with open(TEST_RESULT_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        self.log(f"✅ テスト結果保存完了: {TEST_RESULT_FILE}")
        
    def print_summary(self):
        """テスト結果サマリーを表示"""
        print("\n" + "=" * 60)
        print("テスト結果サマリー")
        print("=" * 60)
        
        summary = self.results.get('summary', {})
        print(f"総テスト数: {summary.get('total', 0)}")
        print(f"成功: {summary.get('passed', 0)}")
        print(f"失敗: {summary.get('failed', 0)}")
        print(f"エラー: {summary.get('errors', 0)}")
        print(f"スキップ: {summary.get('skipped', 0)}")
        print(f"成功率: {summary.get('success_rate', '0%')}")
        print("=" * 60)
        
        print("\n詳細:")
        for test in self.results['tests']:
            status_icon = {
                'PASS': '✅',
                'FAIL': '❌',
                'ERROR': '💥',
                'SKIP': '⏭️'
            }.get(test['status'], '❓')
            
            duration = f" ({test['duration_seconds']:.1f}秒)" if 'duration_seconds' in test else ""
            print(f"{status_icon} {test['name']}{duration}: {test['message'][:80]}")
        
        print("\n" + "=" * 60)
        
    def run(self):
        """統合テストを実行"""
        self.log("=" * 60)
        self.log("xls2xlsx 統合テスト開始")
        self.log("=" * 60)
        
        # 1. Docker環境チェック
        if not self.check_docker():
            self.log("Docker環境が利用できません。テストを中止します。")
            self.save_results()
            return False
            
        if not self.check_docker_compose():
            self.log("Docker Compose環境が利用できません。テストを中止します。")
            self.save_results()
            return False
        
        # 2. サンプルファイル作成
        self.create_sample_xls_simple()
        
        # 3. Docker Compose起動
        if not self.start_docker_compose():
            self.log("Docker Compose起動に失敗しました。テストを中止します。")
            self.save_results()
            return False
        
        # 4. HTTPトリガーテスト
        self.test_http_trigger()
        
        # 5. Blobトリガーテスト
        self.test_blob_trigger()
        
        # 6. クリーンアップ
        self.cleanup()
        
        # 7. 結果保存
        self.save_results()
        
        # 8. サマリー表示
        self.print_summary()
        
        self.log("=" * 60)
        self.log("統合テスト完了")
        self.log("=" * 60)
        
        # 成功したテスト数を返す
        summary = self.results.get('summary', {})
        return summary.get('failed', 0) == 0 and summary.get('errors', 0) == 0


if __name__ == '__main__':
    runner = TestRunner()
    success = runner.run()
    sys.exit(0 if success else 1)
