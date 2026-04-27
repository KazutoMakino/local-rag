# Local RAG

当該リポジトリは、**ローカル環境で CPU のみを用いて RAG (Retrieval-Augmented Generation) を実行する**ための実装例およびテンプレートです。
Python プロジェクトの標準的な構成（`uv` による依存関係管理、`isort/ruff` による品質管理）を備えており、ハンズオン資料としても活用いただけます。

## 📋 概要

- **メイン実行コード**: `src/main.py`
- **パッケージ管理**: `uv` (Windows スタンドアロン版)
- **ソース管理**: GitHub CLI (`gh`)
- **動作環境**:
    - Windows 10/11 (PowerShell)
    - ※ テスト環境: Arch Linux (Hyprland) にて動作確認済み

## 🛠️ 事前準備

本プロジェクトでは、ツールとして **GitHub CLI** および **uv** を使用します。未インストールの場合は、以下の手順で Windows 自体にインストールしてください（python はインストール済みの前提）。

### 1. GitHub CLI (`gh`) のインストール

[GitHub CLI 公式サイト](https://cli.github.com/)からインストーラーをダウンロードするか、`winget` を使用してインストールしてください。

```powershell
winget install --id GitHub.cli
```

もしも、例えば会社の規定などの影響で winget 経由で GitHub CLI がインストール不可の場合は、git を[公式サイト](https://git-scm.com/install/windows)からダウンロードし、git のユーザ名／メールアドレスを設定の後、以下コマンドにて clone してください。

```powershell
git clone https://github.com/KazutoMakino/local-rag.git
```

### 2. uv のインストール（スタンドアロン版）

Python のライブラリとしてではなく、Windows のツールとしてインストールします。PowerShell で以下のコマンドを実行してください。

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

もしも、OS 全体にインストールしたくない場合は、以下のように python のライブラリとしてインストールすることも可能です。

```powershell
python -m pip install uv
```

インストール後、PowerShell を再起動するか環境変数を反映させて、uv --version が実行できることを確認してください。

## 🚀 環境構築

### 1. リポジトリのクローン

GitHub CLI を用いてリポジトリをクローンします。

```powershell
gh repo clone KazutoMakino/local-rag
cd local-rag
```

### 2. 依存関係のインストール

プロジェクトに必要なライブラリをインストールし、仮想環境 (.venv) を作成します。

```powershell
uv sync
```

### 3. 仮想環境の有効化

PowerShell で以下のコマンドを実行して仮想環境に入ります。

```powershell
.venv\Scripts\activate.ps1
```

※ コマンドプロンプトの場合は `.venv\Scripts\activate`, linux などの場合はシェルに合わせて `source .venv/bin/activate.*` を実行することで、仮想環境が有効化されます。

## 🏃 実行方法

### メイン処理の実行

RAG のメインロジックは src/main.py に集約されています。以下のコマンドで実行してください。

```powershell
python src/main.py
```

## 📂 ディレクトリ構成
```
.
├── .github/          # GitHub Actions 等の設定
├── src/              # ソースコード
│    └── main.py       # メイン実行ファイル
├── tests/            # テストコード
├── pyproject.toml    # プロジェクト設定・依存関係定義
├── uv.lock           # 依存関係のロックファイル
└── README.md         # 本ファイル
```

## ⚠️ トラブルシューティング：ビルド環境について

`llama-cpp-python` を含むパッケージをインストールする際、OSごとに以下の開発ツールが必要となります。`uv sync` でビルドエラーが発生した場合は、各OSの手順に従ってツールをインストール後、再び `uv sync` してください。

### Windows

`llama-cpp-python` のビルドには C++ コンパイラが必要です。

1. **Visual Studio Build Tools** をインストールしてください。
   - インストール時、「C++ によるデスクトップ開発」ワークロードを選択してください。
2. Windows SDK もあわせてインストールしてください。

### Ubuntu / Debian

ビルドに必要なコンパイラとヘッダファイルをインストールします。
```bash
sudo apt update
sudo apt install build-essential python3-dev
```

### Arch Linux

```bash
sudo pacman -S base-devel
```

## ⚖️ ライセンス

本プロジェクトは [MIT License](./LICENSE) のもとで公開されています。
