"""モデル構築／ダウンロード"""

import os

# OpenMPのスレッド数、Intel MKL 系を制限
os.environ["OMP_NUM_THREADS"] = "6"
os.environ["MKL_NUM_THREADS"] = "6"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

from pathlib import Path

from dotenv import load_dotenv
from helper.cfg import CFG
from helper.consts import DIRS
from helper.logs import L, save_traceback
from huggingface_hub import hf_hub_download, snapshot_download
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.llama_cpp import LlamaCPP

###################################################################################################
# main
###################################################################################################


def main():
    L.info("start")

    # 初期設定
    dir_embed_model = DIRS.embedding / CFG.embedding_name
    path_llm_model = DIRS.llm / CFG.llm_downloader["filename"]
    dir_embed_model.mkdir(parents=True, exist_ok=True)

    # モデル構築／ダウンロード
    download_models_if_needed(
        dir_embed_model=dir_embed_model,
        path_llm_model=path_llm_model,
        embedding_downloader=CFG.embedding_downloader,
        embedding_revision_hash=CFG.embedding_revision_hash,
        llm_downloader=CFG.llm_downloader,
        llm_revision_hash=CFG.llm_revision_hash,
    )

    L.info("end")


###################################################################################################
# class
###################################################################################################


class ModelBuilder:
    def __init__(self, dir_embed_model: Path, path_llm_model: Path):
        """ディレクトリ／ファイルパス設定

        Args:
            dir_embed_model (Path): embedding モデルのあるディレクトリパス
            path_llm_model (Path): LLM モデルのあるディレクトリパス
        """
        self.dir_embed_model: Path = dir_embed_model
        self.dir_embed_model.mkdir(parents=True, exist_ok=True)
        self.path_llm_model: Path = path_llm_model

    def build_model(self):
        """モデルが存在しない場合にダウンロードを実行する

        Returns:
            Settings (Settings): モデルビルド後に llama_index.core.Settings オブジェクトとして返す
        """
        L.info("start")

        L.info("モデルが存在しない場合にダウンロードを実行する")
        download_models_if_needed(
            dir_embed_model=self.dir_embed_model,
            path_llm_model=self.path_llm_model,
            embedding_downloader=CFG.embedding_downloader,
            embedding_revision_hash=CFG.embedding_revision_hash,
            llm_downloader=CFG.llm_downloader,
            llm_revision_hash=CFG.llm_revision_hash,
        )

        L.info("モデル設定 (オフライン)")
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=str(self.dir_embed_model), local_files_only=True
        )
        Settings.llm = LlamaCPP(
            model_path=str(self.path_llm_model), verbose=False, **CFG.llm_params
        )

        L.info("end")

        return Settings


###################################################################################################
# def
###################################################################################################


def download_models_if_needed(
    dir_embed_model: Path,
    path_llm_model: Path,
    embedding_downloader: dict,
    embedding_revision_hash: str,
    llm_downloader: dict,
    llm_revision_hash: str,
):
    """モデルが存在しない場合にダウンロードを実行する

    Args:
        dir_embed_model (Path): embedding モデルのあるディレクトリパス
        path_llm_model (Path): LLM モデルのあるディレクトリパス
        embedding_downloader (dict): embedding モデルをダウンロードするときに用いるパラメータ
        embedding_revision_hash (str): _description_
        llm_downloader (dict): LLM モデルをダウンロードするときに用いるパラメータ
        llm_revision_hash (str): _description_
    """
    L.info("start")

    L.info("埋め込みモデルのチェックとダウンロード")
    if not (dir_embed_model / "config.json").exists():
        L.info(f"埋め込みモデルが見つからないため、ダウンロードします: {dir_embed_model}")
        # .env 読み込み
        load_dotenv()
        token = os.getenv(key="HF_TOKEN")
        # モデルダウンロード
        snapshot_download(
            local_dir=dir_embed_model,
            local_dir_use_symlinks=False,
            token=token,
            revision=embedding_revision_hash,
            **embedding_downloader,
        )

    L.info("LLM (GGUFファイル単体) のチェックとダウンロード")
    if not path_llm_model.exists():
        L.info(f"LLMモデルが見つからないため、ダウンロードします: {path_llm_model}")
        # .env 読み込み
        load_dotenv()
        token = os.getenv(key="HF_TOKEN")
        # モデルダウンロード
        hf_hub_download(
            local_dir=path_llm_model.parent,
            local_dir_use_symlinks=False,
            revision=llm_revision_hash,
            **llm_downloader,
        )

    L.info("end")


###################################################################################################

if __name__ == "__main__":
    try:
        main()
    except Exception:
        save_traceback()
    exit()
