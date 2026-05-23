"""_summary_"""

import os

# OpenMPのスレッド数、Intel MKL 系を制限
os.environ["OMP_NUM_THREADS"] = "6"
os.environ["MKL_NUM_THREADS"] = "6"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

import gc
import shutil
from pathlib import Path

import lancedb
from helper.build_model import ModelBuilder
from helper.cfg import CFG, Cfg
from helper.consts import DIRS
from helper.directory_manager import mkdir_all
from helper.get_dummy_data import DataDownloader
from helper.logs import L, save_traceback
from helper.summarize_docs import generate_summary_txt
from llama_index.core import (
    PromptTemplate,
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.lancedb import LanceDBVectorStore
from tqdm import tqdm

###################################################################################################
# main
###################################################################################################


def main():
    L.info("start")

    mkdir_all()
    gc.collect()

    L.info("ダミーデータのダウンロード")
    data_downloader = DataDownloader()
    data_downloader.download_data()

    L.info("モデル設定")
    model_builder = ModelBuilder(
        dir_embed_model=DIRS.embedding / CFG.embedding_name,
        path_llm_model=DIRS.llm / CFG.llm_downloader["filename"],
    )
    model_builder.build_model()
    gc.collect()

    L.info("要約生成処理")
    txt_files = sorted((DIRS.data / CFG.dir_data).glob("*.txt"))
    for txt_file in tqdm(txt_files, desc="Summarizing", dynamic_ncols=True):
        if txt_file.name.endswith("_summary.txt"):
            continue
        summary_file = txt_file.with_name(txt_file.stem + "_summary.txt")
        if summary_file.exists():
            continue
        with txt_file.open(mode="r", encoding="utf-8") as f:
            content = f.read()
        prompt = CFG.summary_prompt.format(text=content[: CFG.len_src_to_summary])
        response = Settings.llm.complete(prompt=prompt)
        generate_summary_txt(txt_file, response.text)
        gc.collect()

    L.info("インデックス構築")
    summary_index, full_text_index = build_dual_indices()
    gc.collect()

    L.info("二段階検索の実行")

    L.info("要約インデックスで関連ファイルパスを特定")
    summary_retriever = summary_index.as_retriever(similarity_top_k=CFG.similarity_top_k)
    summary_nodes = summary_retriever.retrieve(CFG.query_str)
    gc.collect()

    L.info("検索対象パスの抽出 (メタデータの file_path を使用)")

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
            f"検索クエリ: 「{CFG.query_str}」 に合致する情報が記載されていそうなファイルはありませんでした。"
        )
        return

    L.info("本文インデックスにフィルタを適用してRAG実行")
    query_engine = full_text_index.as_query_engine(
        filters=None,
        similarity_top_k=CFG.similarity_top_k,
        text_qa_template=PromptTemplate(template=CFG.text_qa_template),
        response_mode=CFG.response_mode,
        streaming=CFG.streaming,
    )

    response = query_engine.query(CFG.query_str)
    gc.collect()

    L.info("ストリームを逐次出力")
    full_res_list: list[str] = []
    for token in response.response_gen:
        full_res_list.append(token)
    full_res = "".join(full_res_list).strip()
    print()
    L.info(f"回答： {full_res}")

    path_output = DIRS.output / "output.txt"
    with path_output.open(mode="w", encoding="utf-8") as f:
        f.write(full_res)
    shutil.copy2(src=DIRS.helper / "cfg.yml", dst=DIRS.output)

    gc.collect()

    L.info("end")


###################################################################################################
# def
###################################################################################################


def build_dual_indices() -> tuple[VectorStoreIndex]:
    """要約用・本文用テーブルを差分更新する。
    新規ファイルが存在しない場合は、インデックスのロードのみを行い追加処理をスキップする。

    Returns:
        tuple[VectorStoreIndex]: 要約と本文の VectorStoreIndex
    """
    L.info("start")

    db_path = DIRS.lancedb
    db = lancedb.connect(str(db_path))

    L.info("既存テーブルのリストを取得")
    res = db.list_tables()
    existing_tables = res.tables if hasattr(res, "tables") else []

    def _get_new_files(all_files, table_name):
        """DBのテーブルを直接参照し、未登録のファイルパスを抽出する"""
        if table_name not in existing_tables:
            return all_files

        try:
            L.info("全件のデータを取得")
            tbl = db.open_table(table_name)
            df = tbl.to_pandas()

            if df.empty:
                return all_files

            L.info("カラム名に直接 file_path があるか、metadata カラムの中にあるかを確認")
            if "file_path" in df.columns:
                registered_paths = set(df["file_path"].astype(str).tolist())
            elif "metadata" in df.columns:
                registered_paths = set(
                    df["metadata"]
                    .apply(lambda x: x.get("file_path") if isinstance(x, dict) else None)
                    .dropna()
                    .tolist()
                )
            else:
                L.warning(f"テーブル '{table_name}' にパス情報が見つかりません。全件対象とします。")
                return all_files

            return [f for f in all_files if str(f.resolve()) not in registered_paths]

        except Exception as e:
            L.warning(f"既存パスの照合中にエラーが発生しました（全件対象とします）: {e}")
            return all_files

    # 共通の変換設定 (Pipeline用)
    transformations = [
        SentenceSplitter(chunk_size=1024, chunk_overlap=100),  # 高速化のためサイズ調整
        Settings.embed_model,
    ]

    L.info("本文インデックスの処理")
    all_text_files = sorted((DIRS.data / CFG.dir_data).rglob("*.txt"))
    all_text_files = [f for f in all_text_files if not f.name.endswith("_summary.txt")]
    new_text_files = _get_new_files(all_text_files, CFG.text_table)
    text_vector_store = LanceDBVectorStore(uri=str(db_path), table_name=CFG.text_table)
    if not new_text_files:
        L.info(f"本文インデックス ({CFG.text_table}): 更新はありません。既存データをロードします。")
        full_text_index = VectorStoreIndex.from_vector_store(
            vector_store=text_vector_store,
            storage_context=StorageContext.from_defaults(vector_store=text_vector_store),
        )
    else:
        L.info(
            f"本文インデックス ({CFG.text_table}): {len(new_text_files)} 件の新規ファイルを追加中..."
        )
        reader = SimpleDirectoryReader(input_files=new_text_files, file_metadata=get_meta)
        docs = reader.load_data()
        for doc in docs:
            doc.doc_id = doc.metadata["file_path"]
        pipeline = IngestionPipeline(
            transformations=transformations, vector_store=text_vector_store
        )
        pipeline.run(documents=docs, show_progress=True)
        full_text_index = VectorStoreIndex.from_vector_store(text_vector_store)

    L.info("要約インデックスの処理")
    all_summary_files = sorted((DIRS.data / CFG.dir_data).glob("*_summary.txt"))
    new_summary_files = _get_new_files(all_summary_files, CFG.summary_table)
    summary_vector_store = LanceDBVectorStore(uri=str(db_path), table_name=CFG.summary_table)
    if not new_summary_files:
        L.info(
            f"要約インデックス ({CFG.summary_table}): 更新はありません。既存データをロードします。"
        )
        summary_index = VectorStoreIndex.from_vector_store(
            vector_store=summary_vector_store,
            storage_context=StorageContext.from_defaults(vector_store=summary_vector_store),
        )
    else:
        L.info(
            f"要約インデックス ({CFG.summary_table}): {len(new_summary_files)} 件の新規要約を追加中..."
        )
        reader = SimpleDirectoryReader(input_files=new_summary_files, file_metadata=get_meta)
        docs = reader.load_data()
        for doc in docs:
            doc.doc_id = doc.metadata["file_path"]

        pipeline = IngestionPipeline(
            transformations=transformations, vector_store=summary_vector_store
        )
        pipeline.run(documents=docs, show_progress=True)

        summary_index = VectorStoreIndex.from_vector_store(summary_vector_store)

    gc.collect()
    L.info("end")
    return summary_index, full_text_index


def get_meta(file_path: str) -> dict[str]:
    """Pathオブジェクトとして処理し、絶対パスを返す

    Args:
        file_path (str): 対象ファイルのパス

    Returns:
        dict[str]: 対象ファイルのパス文字列とファイル名称の辞書
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
