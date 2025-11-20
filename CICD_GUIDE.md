# CI/CD パイプラインガイド

## 📋 概要

このプロジェクトはGitHub Actionsを使用した包括的なCI/CDパイプラインを実装しています。

## 🔄 ワークフロー構成

### 1. CI - Continuous Integration (`ci.yml`)

**トリガー**:
- `main`、`develop`ブランチへのpush
- Pull Requestの作成・更新
- 手動実行

**ジョブ**:

#### テスト実行
- Python 3.11、3.12のマトリックステスト
- 統合テスト（`run_local_tests.py`）
- セキュリティテスト（`test_security_features.py`）
- テスト結果のアーティファクト保存（30日間）

#### セキュリティスキャン
- **Bandit**: Pythonコードの脆弱性スキャン
- **Safety**: 依存パッケージの既知の脆弱性チェック
- レポートのアーティファクト保存

#### コード品質チェック
- **Black**: コードフォーマットチェック
- **isort**: import順序チェック
- **flake8**: コードスタイルチェック
- **pylint**: 静的解析

#### Azure Functions検証
- `function.json`の構文チェック
- `host.json`の検証
- 設定ファイルの整合性確認

### 2. CD - Continuous Deployment (`cd.yml`)

**トリガー**:
- `main`ブランチへのpush
- バージョンタグ（`v*`）のpush
- 手動実行（環境選択可能）

**ジョブ**:

#### ビルド
- 依存パッケージのインストール
- デプロイメントパッケージの作成
- パッケージのアーティファクト保存（90日間）

#### ステージング環境へのデプロイ
- `main`ブランチへのpush時に自動実行
- Azure Functions (Staging)へのデプロイ
- 環境: `staging`

#### 本番環境へのデプロイ
- バージョンタグ（`v*`）のpush時に自動実行
- Azure Functions (Production)へのデプロイ
- GitHub Releaseの自動作成
- 環境: `production`

### 3. PR Validation (`pr-validation.yml`)

**トリガー**:
- Pull Requestの作成・更新

**ジョブ**:
- PRタイトルのConventional Commitsフォーマットチェック
- 全テストの実行
- セキュリティスキャン
- コード変更の分析
- 自動コメントの投稿

### 4. CodeQL Security (`codeql.yml`)

**トリガー**:
- `main`、`develop`ブランチへのpush
- Pull Request
- スケジュール（毎週月曜日）

**ジョブ**:
- GitHub CodeQLによる高度なセキュリティ分析
- セキュリティ脆弱性の自動検出

## 🚀 セットアップ手順

### 1. GitHub Secretsの設定

Azure Functionsへのデプロイを有効にするには、以下のシークレットを設定してください：

```bash
# ステージング環境
AZURE_FUNCTIONAPP_PUBLISH_PROFILE_STAGING

# 本番環境
AZURE_FUNCTIONAPP_PUBLISH_PROFILE_PRODUCTION
```

**取得方法**:
1. Azure Portalでfunction appを開く
2. 「概要」→「発行プロファイルの取得」をクリック
3. ダウンロードしたファイルの内容をGitHub Secretsに設定

### 2. ワークフローの有効化

`cd.yml`ファイルを編集して、デプロイを有効にします：

```yaml
# 変更前
if: false  # Set to true when Azure credentials are configured

# 変更後
if: true  # Azure credentials configured
```

### 3. Dependabotの有効化

`.github/dependabot.yml`が自動的に有効化されます。
- 毎週月曜日9:00に依存関係をチェック
- 自動的にPull Requestを作成

## 📝 使用方法

### ローカルでのテスト実行

```bash
# 統合テスト
python run_local_tests.py

# セキュリティテスト
python test_security_features.py

# コード品質チェック
black --check .
isort --check-only .
flake8 .
pylint $(find . -name "*.py" -not -path "./.venv/*")
```

### デプロイフロー

#### ステージング環境
```bash
# mainブランチにマージ
git checkout main
git merge develop
git push origin main
```

#### 本番環境
```bash
# バージョンタグを作成
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### Pull Requestの作成

1. フィーチャーブランチを作成
   ```bash
   git checkout -b feat/new-feature
   ```

2. 変更をコミット（Conventional Commits形式）
   ```bash
   git commit -m "feat: add new feature"
   ```

3. PRを作成
   - PRテンプレートに従って記入
   - 自動的にCI/CDが実行される

## 🔍 Conventional Commits

PRタイトルは以下のフォーマットに従ってください：

- `feat:` - 新機能
- `fix:` - バグ修正
- `docs:` - ドキュメント
- `style:` - コードスタイル
- `refactor:` - リファクタリング
- `test:` - テスト
- `chore:` - ビルド・設定
- `perf:` - パフォーマンス改善
- `ci:` - CI/CD関連
- `build:` - ビルドシステム
- `revert:` - 変更の取り消し

**例**:
```
feat: add batch processing API
fix: resolve file size validation bug
docs: update README with deployment guide
```

## 📊 ワークフロー状態の確認

### GitHub Actions画面
1. リポジトリの「Actions」タブをクリック
2. 各ワークフローの実行履歴を確認

### バッジの追加

README.mdに以下のバッジを追加できます：

```markdown
![CI](https://github.com/nahisaho/xls2xlsx/workflows/CI%20-%20Continuous%20Integration/badge.svg)
![CD](https://github.com/nahisaho/xls2xlsx/workflows/CD%20-%20Continuous%20Deployment/badge.svg)
![Security](https://github.com/nahisaho/xls2xlsx/workflows/CodeQL%20Advanced%20Security/badge.svg)
```

## 🔒 セキュリティ

### スキャンツール
- **Bandit**: Pythonコードのセキュリティ問題を検出
- **Safety**: 依存パッケージの脆弱性をチェック
- **CodeQL**: GitHub Advanced Securityによる高度な分析

### レポートの確認
1. Actions → 該当のワークフロー実行
2. Artifactsセクションから`security-reports`をダウンロード

## 🛠️ トラブルシューティング

### テストが失敗する場合
```bash
# ローカルで再現
python run_local_tests.py
python test_security_features.py
```

### デプロイが失敗する場合
1. GitHub Secretsが正しく設定されているか確認
2. Azure Function Appが存在するか確認
3. ワークフローログを確認

### コード品質チェックが失敗する場合
```bash
# 自動フォーマット
black .
isort .

# エラー箇所を確認
flake8 .
pylint $(find . -name "*.py" -not -path "./.venv/*")
```

## 📈 メトリクス

### 現在の状態
- **セキュリティスコア**: 9.5/10
- **テスト成功率**: 100% (11/11)
- **コードカバレッジ**: 統合テスト・セキュリティテスト完備

### 改善目標
- [ ] ユニットテストカバレッジ80%以上
- [ ] E2Eテストの追加
- [ ] パフォーマンステストの実装

## 🔗 関連ドキュメント

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Azure Functions CI/CD](https://learn.microsoft.com/en-us/azure/azure-functions/functions-how-to-github-actions)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Keep a Changelog](https://keepachangelog.com/)

## 📞 サポート

問題が発生した場合：
1. GitHub Issuesで報告
2. ワークフローログを添付
3. エラーメッセージを記載
