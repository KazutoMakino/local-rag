"""_summary_"""

import os

# OpenMPのスレッド数、Intel MKL 系を制限
os.environ["OMP_NUM_THREADS"] = "6"
os.environ["MKL_NUM_THREADS"] = "6"

import gc
import shutil
from pathlib import Path

import lancedb
from llama_index.core import (
    PromptTemplate,
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from llama_index.vector_stores.lancedb import LanceDBVectorStore
from tqdm import tqdm

from helper.build_model import ModelBuilder
from helper.cfg import Cfg
from helper.consts import D
from helper.directory_manager import mkdir_all
from helper.get_dummy_data import DataDownloader
from helper.logs import logger_instance, save_traceback
from helper.summarize_docs import generate_summary_txt

# logger のインスタンス作成
L = logger_instance()

###################################################################################################
# main
###################################################################################################


def main():
    L.info("start")

    mkdir_all()
    cfg = Cfg()
    gc.collect()

    L.info("ダミーデータのダウンロード")
    data_downloader = DataDownloader()
    data_downloader.download_data()

    L.info("モデル設定")
    model_builder = ModelBuilder(
        cfg=cfg,
        dir_embed_model=D().embedding / cfg.embedding_name,
        path_llm_model=D().llm / cfg.llm_downloader["filename"],
    )
    model_builder.build_model()
    gc.collect()

    L.info("要約生成処理")
    txt_files = sorted((D().data / cfg.dir_data).glob("*.txt"))
    for txt_file in tqdm(txt_files, desc="Summarizing", dynamic_ncols=True):
        if txt_file.name.endswith("_summary.txt"):
            continue
        summary_file = txt_file.with_name(txt_file.stem + "_summary.txt")
        if summary_file.exists():
            continue
        with txt_file.open(mode="r", encoding="utf-8") as f:
            content = f.read()
        prompt = cfg.summary_prompt.format(text=content[:4000])  # 長さ制限を考慮
        response = Settings.llm.complete(prompt=prompt)
        generate_summary_txt(txt_file, response.text)
        gc.collect()

    L.info("インデックス構築")
    summary_index, full_text_index = build_dual_indices(cfg)
    gc.collect()

    L.info("二段階検索の実行")

    L.info("要約インデックスで関連ファイルパスを特定")
    summary_retriever = summary_index.as_retriever(similarity_top_k=cfg.similarity_top_k)
    summary_nodes = summary_retriever.retrieve(cfg.query_str)
    gc.collect()

    L.info("検索対象パスの抽出 (メタデータの file_path を使用)")
    # target_paths = list(set([node.metadata["file_path"] for node in summary_nodes]))

    L.info("検索対象パスの抽出と変換")
    # 要約パスの _summary.txt を取り除いて .txt に戻す
    target_paths = []
    for node in summary_nodes:
        summary_path = Path(node.metadata["file_path"])
        # _summary.txt を .txt に置換（これで本文のパスになる）
        text_path = summary_path.with_name(summary_path.name.replace("_summary.txt", ".txt"))
        target_paths.append(str(text_path))

    target_paths = list(set(target_paths))

    L.info(f"検索対象ファイル数: {len(target_paths)}")

    # 検索対象ノードが空でないか確認
    if len(target_paths) == 0:
        L.info(
            f"検索クエリ: 「{cfg.query_str}」 に合致する情報が記載されていそうなファイルはありませんでした。"
        )
        return

    # インデックスの中身を覗いて、どんな file_path が入っているか確認する
    # (これは LanceDB に直接問い合わせる例です)
    db = lancedb.connect(str(D().lancedb))
    table = db.open_table(cfg.text_table)
    all_paths = table.to_pandas()["metadata"].apply(lambda x: x.get("file_path")).unique()

    gc.collect()

    L.info("本文インデックスにフィルタを適用してRAG実行")
    # filters = MetadataFilters(
    #     filters=[ExactMatchFilter(key="file_path", value=p) for p in target_paths], condition="or"
    # )
    query_engine = full_text_index.as_query_engine(
        # filters=filters,
        filters=None,
        similarity_top_k=cfg.similarity_top_k,
        text_qa_template=PromptTemplate(template=cfg.text_qa_template),
        response_mode=cfg.response_mode,
        streaming=cfg.streaming,
    )

    response = query_engine.query(cfg.query_str)
    gc.collect()

    L.info("ストリームを逐次出力")
    full_res_list: list[str] = []
    for token in response.response_gen:
        full_res_list.append(token)
    full_res = "".join(full_res_list).strip()
    print()
    L.info(f"回答： {full_res}")

    path_output = D().output / "output.txt"
    with path_output.open(mode="w", encoding="utf-8") as f:
        f.write(full_res)
    shutil.copy2(src=D().helper / "cfg.yml", dst=D().output)

    gc.collect()

    L.info("end")


###################################################################################################
# def
###################################################################################################


def build_dual_indices(cfg: Cfg):
    """要約用テーブルと本文用テーブルを個別に構築"""
    L.info("start")

    L.info("重複する名称のテーブルを削除")
    db_path = D().lancedb
    db = lancedb.connect(str(db_path))
    for t in ["summary_table", "text_table"]:
        if t in db.list_tables():
            db.drop_table(t)

    data_dir = D().data / cfg.dir_data
    all_files = sorted(data_dir.rglob("*.txt"))

    L.info("本文インデックス作成中...")
    text_files = [str(f) for f in all_files if not f.name.endswith("_summary.txt")]
    text_reader = SimpleDirectoryReader(input_files=text_files, file_metadata=get_meta)
    text_vector_store = LanceDBVectorStore(uri=str(db_path), table_name=cfg.text_table)
    text_docs = text_reader.load_data()
    for doc in text_docs:
        doc.doc_id = doc.metadata["file_path"]
    full_text_index = VectorStoreIndex.from_documents(
        text_docs,
        storage_context=StorageContext.from_defaults(vector_store=text_vector_store),
        show_progress=True,
    )

    L.info("要約インデックス作成中...")
    summary_files = [str(f) for f in all_files if f.name.endswith("_summary.txt")]
    summary_reader = SimpleDirectoryReader(input_files=summary_files, file_metadata=get_meta)
    summary_vector_store = LanceDBVectorStore(uri=str(db_path), table_name=cfg.summary_table)
    summary_docs = summary_reader.load_data()
    for doc in summary_docs:
        doc.doc_id = doc.metadata["file_path"]
    summary_index = VectorStoreIndex.from_documents(
        summary_docs,
        storage_context=StorageContext.from_defaults(vector_store=summary_vector_store),
        show_progress=True,
    )

    gc.collect()

    L.info("end")

    return summary_index, full_text_index


def get_meta(file_path: str) -> dict[str]:
    """Pathオブジェクトとして処理し、絶対パスを返す

    Args:
        file_path (str): _description_

    Returns:
        dict[str]: _description_
    """
    p = Path(file_path).resolve()
    return {"file_path": str(p), "file_name": p.name}


###################################################################################################

if __name__ == "__main__":
    try:
        main()
    except Exception:
        save_traceback()
    exit()
