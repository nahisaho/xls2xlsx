#!/usr/bin/env python3
"""
Azurite Blob Storageにファイルをアップロードしてトリガーをテスト
"""
import os
import sys
from azure.storage.blob import BlobServiceClient

def test_blob_trigger(file_path):
    """
    Blobトリガーのテスト
    
    Args:
        file_path: アップロードするXLSファイルのパス
    """
    # Azurite接続文字列
    connection_string = (
        "DefaultEndpointsProtocol=http;"
        "AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
        "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
    )
    
    try:
        # BlobServiceClientを作成
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # コンテナを作成（存在しない場合）
        input_container = 'xls-input'
        output_container = 'xls-output'
        
        print(f"📦 コンテナを準備中...")
        for container_name in [input_container, output_container]:
            try:
                container_client = blob_service_client.get_container_client(container_name)
                if not container_client.exists():
                    container_client.create_container()
                    print(f"   ✅ {container_name} コンテナを作成しました")
                else:
                    print(f"   ℹ️  {container_name} コンテナは既に存在します")
            except Exception as e:
                print(f"   ⚠️  {container_name}: {str(e)}")
        
        # ファイルをアップロード
        if not os.path.exists(file_path):
            print(f"❌ Error: {file_path} が見つかりません")
            return
        
        filename = os.path.basename(file_path)
        blob_client = blob_service_client.get_blob_client(
            container=input_container,
            blob=filename
        )
        
        print(f"\n📤 {filename} を {input_container} にアップロード中...")
        with open(file_path, 'rb') as data:
            blob_client.upload_blob(data, overwrite=True)
        
        print(f"✅ アップロード完了！")
        print(f"\n⏳ Blobトリガーが実行されるまで数秒お待ちください...")
        print(f"   関数ログを確認してください。")
        print(f"\n📥 変換結果の確認:")
        print(f"   コンテナ: {output_container}")
        print(f"   ファイル: {filename[:-4]}.xlsx")
        
        # 結果を確認（10秒後）
        import time
        time.sleep(10)
        
        output_blob_name = filename[:-4] + '.xlsx'
        output_blob_client = blob_service_client.get_blob_client(
            container=output_container,
            blob=output_blob_name
        )
        
        if output_blob_client.exists():
            print(f"\n✅ 変換成功！{output_container}/{output_blob_name} が作成されました")
            
            # ファイルをダウンロード
            os.makedirs('test_output', exist_ok=True)
            download_path = f'test_output/{output_blob_name}'
            with open(download_path, 'wb') as download_file:
                download_file.write(output_blob_client.download_blob().readall())
            print(f"   ダウンロード先: {download_path}")
        else:
            print(f"\n⏳ まだ変換が完了していません。少し待ってから再度確認してください。")
        
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_blob.py <xls_file_path>")
        print("Example: python test_blob.py samples/sample1.xls")
        sys.exit(1)
    
    test_blob_trigger(sys.argv[1])
