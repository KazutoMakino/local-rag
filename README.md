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

## 🔑 Hugging Face トークンの設定

モデルのダウンロード等に認証が必要な場合があるため、Hugging Faceのアクセストークンを設定します。

### トークンの取得:

Hugging Face Settings/Tokens にアクセスします。  
New token をクリックし、適切な権限（Readで十分です）を選択してトークンを生成・コピーしてください。

### .env ファイルの作成:

プロジェクトルートに .env という名前のファイルを新規作成し、以下の形式でトークンを記述します。
```text
HF_TOKEN=your_access_token_here
```
※ your_access_token_here の部分を、先ほどコピーした自身のトークンに置き換えてください。

⚠️ 注意事項

.env ファイルは絶対にGitHubへプッシュしないでください。  
リポジトリをクローンした直後の .gitignore には通常 .env が含まれているはずですが、念のため確認してください。

## 🚀 環境構築

### 1. リポジトリのクローン

GitHub CLI を用いてリポジトリをクローンします。

```powershell
gh repo clone KazutoMakino/local-rag
cd local-rag
```

もしも、例えば会社の規定などの影響で winget 経由で GitHub CLI がインストール不可の場合は、git を[公式サイト](https://git-scm.com/install/windows)からダウンロードし、git のユーザ名／メールアドレスを設定の後、以下コマンドにて clone してください。

```powershell
git clone https://github.com/KazutoMakino/local-rag.git
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

上記スクリプトを実行すると、以下ステップが自動的に行われます。

1. ダミーデータのダウンロード: 検索対象となるテキストデータを自動取得します
    - リポジトリ例では、フリーの国会文書データから "スタートアップ" というキーワードでヒットするデータを取得します
    - データは `data/dummy/kokkai/` に .txt 形式で保存されます
2. モデル構築: LLM（Large Language Model）および Embedding モデルを Hugging Face よりローカルにダウンロードし、このローカルに保存したファイルを読み込みます
    - LLM: gemma-4-E4B-it-Q4_K_M (https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF)
    - Embedding: ruri-v3-130m (https://huggingface.co/cl-nagoya/ruri-v3-130m)
3. インデックス作成: 要約用インデックス（高速検索用）と本文用インデックス（詳細検索用）の2段階を構築します (⚠️ 新規作成には、１ファイルあたり数分かかります)
4. 二段階検索の実行: 要約インデックスで関連性の高いファイルを特定し、その内容を本文インデックスで詳細に検索します
5. 回答生成: 検索結果を基にモデルが回答を生成し、data/output/yyyymmdd-hhmmss/output.txt に結果が出力されます

※ 初回実行時はモデルのダウンロードや要約ファイル作成が行われるため、通信環境により数十分以上かかる場合があります。

## 📂 ディレクトリ構成
```
.
├── .github/          # GitHub Actions 等の設定
├── src/              # ソースコード
│    ├── main.py     # メイン実行ファイル
│    └── helper/     # サブの実行ファイル群
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
