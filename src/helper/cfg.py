"""cfg.yml に記載した設定値を Cfg class の属性値として定義"""

from pathlib import Path

from helper.logs import L
from yaml import safe_load

#######################################################################################
# def
#######################################################################################


class Cfg:
    """cfg.yml から読み込んだ設定値をインスタンス化"""

    def __init__(self):
        # cfg.yml 読み込み
        path_cfg = Path(__file__).resolve().parent / "cfg.yml"
        if not path_cfg.exists():
            L.error(f"not found: {path_cfg}")
            raise FileNotFoundError
        with path_cfg.open(mode="r") as f:
            cfg: dict = safe_load(f)

        # # パス
        # データの所在（`{repo.}/data/` からの相対パスを推奨）
        self.dir_data: str = cfg["dir_data"]
        # ファイル更新を確認するための json `{repo.}/.cache/` からの相対パスを推奨）
        self.file_tracker: str = cfg["file_tracker"]

        # # 最終的な RAG 用の設定値
        # 比較対象となるベクトル DB のテーブル名称
        self.text_table: str = cfg["text_table"]
        # プロンプト
        self.query_str: str = cfg["query_str"]
        # テンプレート
        self.text_qa_template: str = cfg["text_qa_template"]

        # # サマリー用の設定値
        # 比較対象となるベクトル DB のテーブル名称
        self.summary_table: str = cfg["summary_table"]
        # summary 作成用のプロンプト
        self.summary_prompt: str = cfg["summary_prompt"]

        # # LLM / embedding モデル用の設定値
        # local LLM モデル
        self.llm_name: str = cfg["llm"]
        self.llm_downloader: dict = cfg[self.llm_name]["downloader"]
        self.llm_revision_hash: str = cfg[self.llm_name]["revision_hash"]
        self.llm_params: dict = cfg[self.llm_name]["params"]
        # embedding モデル
        self.embedding_name: str = cfg["embedding"]
        self.embedding_downloader: dict = cfg[self.embedding_name]["downloader"]
        self.embedding_revision_hash: str = cfg[self.embedding_name]["revision_hash"]

        # # その他の設定値
        # プロンプトに使用するパラメータ
        self.len_src_to_summary: int = cfg["len_src_to_summary"]
        self.similarity_top_k: int = cfg["similarity_top_k"]
        self.streaming: bool = cfg["streaming"]
        self.response_mode: str = cfg["response_mode"]
        # RAG で取得可能なファイル形式 (word における旧式の拡張子 .doc は読み取り不可)
        self.list_file_ext: str = cfg["list_file_ext"]


#######################################################################################
# instance
#######################################################################################

CFG: Cfg = Cfg()
