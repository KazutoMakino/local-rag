from pathlib import Path

from yaml import safe_load

from helper.logs import logger_instance

L = logger_instance()


class Cfg:
    """cfg.yml から読み込んだ設定値をインスタンス化"""

    def __init__(self):
        # cfg.yml 読み込み
        path_cfg = Path(__file__).resolve().parent / "cfg.yml"
        if not path_cfg.exists():
            L.error(f"not found: {path_cfg}")
            raise FileNotFoundError
        with path_cfg.open(mode="r") as f:
            cfg = safe_load(f)

        #
        self.summary_prompt: str = cfg["summary_prompt"]
        self.text_qa_template: str = cfg["text_qa_template"]
        self.llm_name: str = cfg["llm"]
        self.llm_downloader: dict = cfg[self.llm_name]["downloader"]
        self.llm_params: dict = cfg[self.llm_name]["params"]
        self.embedding_name: str = cfg["embedding"]
        self.embedding_downloader: dict = cfg[self.embedding_name]["downloader"]
        self.dir_data: str = cfg["dir_data"]
        self.file_tracker: str = cfg["file_tracker"]
        self.list_file_ext: str = cfg["list_file_ext"]
        self.similarity_top_k: int = cfg["similarity_top_k"]
        self.streaming: bool = cfg["streaming"]
        self.response_mode: str = cfg["response_mode"]
        self.query_str: str = cfg["query_str"]
        self.text_table: str = cfg["text_table"]
        self.summary_table: str = cfg["summary_table"]
