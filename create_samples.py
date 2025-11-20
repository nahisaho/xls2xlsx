#!/usr/bin/env python3
"""
サンプルXLSファイルを生成するスクリプト
"""
import pandas as pd
import os

def create_sample_xls():
    """サンプルXLSファイルを作成"""
    
    # 出力ディレクトリを作成
    os.makedirs('samples', exist_ok=True)
    
    # サンプルデータ1: 単一シート
    print("Creating sample1.xls (単一シート)...")
    df1 = pd.DataFrame({
        '氏名': ['田中太郎', '佐藤花子', '鈴木一郎', '高橋美咲', '伊藤健太'],
        '年齢': [25, 30, 28, 22, 35],
        '部署': ['営業', '開発', '総務', '営業', '開発'],
        '給与': [300000, 450000, 350000, 280000, 500000]
    })
    
    with pd.ExcelWriter('samples/sample1.xls', engine='xlwt') as writer:
        df1.to_excel(writer, sheet_name='社員リスト', index=False)
    
    # サンプルデータ2: 複数シート
    print("Creating sample2.xls (複数シート)...")
    df2_sheet1 = pd.DataFrame({
        '商品名': ['りんご', 'バナナ', 'オレンジ', 'ぶどう', 'いちご'],
        '価格': [150, 120, 180, 300, 400],
        '在庫': [100, 150, 80, 50, 30]
    })
    
    df2_sheet2 = pd.DataFrame({
        '月': ['1月', '2月', '3月', '4月', '5月'],
        '売上': [1000000, 1200000, 1500000, 1300000, 1400000],
        '利益': [200000, 250000, 300000, 280000, 290000]
    })
    
    df2_sheet3 = pd.DataFrame({
        '顧客名': ['A社', 'B社', 'C社', 'D社', 'E社'],
        '担当者': ['山田', '佐々木', '中村', '小林', '加藤'],
        '取引額': [5000000, 3000000, 8000000, 2000000, 4500000]
    })
    
    with pd.ExcelWriter('samples/sample2.xls', engine='xlwt') as writer:
        df2_sheet1.to_excel(writer, sheet_name='商品マスタ', index=False)
        df2_sheet2.to_excel(writer, sheet_name='月次売上', index=False)
        df2_sheet3.to_excel(writer, sheet_name='顧客リスト', index=False)
    
    # サンプルデータ3: 大きなデータ（100行）
    print("Creating sample3.xls (大容量データ)...")
    df3 = pd.DataFrame({
        'ID': range(1, 101),
        '名前': [f'ユーザー{i}' for i in range(1, 101)],
        'メール': [f'user{i}@example.com' for i in range(1, 101)],
        'スコア': [i * 10 % 100 for i in range(1, 101)],
        'ステータス': ['アクティブ' if i % 2 == 0 else '非アクティブ' for i in range(1, 101)]
    })
    
    with pd.ExcelWriter('samples/sample3.xls', engine='xlwt') as writer:
        df3.to_excel(writer, sheet_name='ユーザーデータ', index=False)
    
    print("\n✅ サンプルファイルの生成が完了しました！")
    print("生成されたファイル:")
    print("  - samples/sample1.xls (単一シート)")
    print("  - samples/sample2.xls (複数シート)")
    print("  - samples/sample3.xls (大容量データ)")

if __name__ == '__main__':
    # xlwtパッケージが必要
    try:
        import xlwt
        create_sample_xls()
    except ImportError:
        print("Error: xlwtパッケージが必要です。")
        print("インストール: pip install xlwt")
