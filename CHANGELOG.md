# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CI/CD pipeline with GitHub Actions
- Automated testing on push and pull requests
- Security scanning with Bandit and Safety
- Code quality checks with flake8, pylint, black, and isort
- Dependabot for automatic dependency updates
- Pull request template

## [1.0.0] - 2025-11-20

### Added
- HTTPトリガー関数（convert_http）
- Blobトリガー関数（convert_blob）
- XLS→XLSX変換機能
- 複数シート対応
- 10MB未満は直接レスポンス、10MB以上はBlob Storage経由
- Docker環境でのローカルテスト対応
- セキュリティ機能（9.5/10スコア）
  - ファイル名サニタイズ（パストラバーサル対策）
  - ファイル形式検証（マジックナンバーチェック）
  - ファイルサイズ制限（50MB上限）
  - セキュリティヘッダー（5種類）
  - エラーメッセージ処理（環境別）
  - セキュリティイベントログ
- 統合テスト（5/5成功）
- セキュリティテスト（6/6成功）
- 包括的なドキュメント
  - README.md
  - 要件定義書.md
  - SECURITY_AUDIT.md
  - SECURITY_IMPLEMENTATION.md
  - TEST_REPORT.md

### Security
- Function Key認証
- SASトークン（1時間有効期限）
- プライベートBlob Storage
- 入力検証・サニタイズ

## [0.1.0] - 2025-11-XX

### Added
- 初期プロジェクト構築
- 基本的なXLS→XLSX変換機能
- 要件定義書作成

[Unreleased]: https://github.com/nahisaho/xls2xlsx/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/nahisaho/xls2xlsx/releases/tag/v1.0.0
[0.1.0]: https://github.com/nahisaho/xls2xlsx/releases/tag/v0.1.0
