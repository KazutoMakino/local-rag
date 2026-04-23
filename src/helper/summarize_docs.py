"""既存文書に対して1対1に、要約・メタデータを記載した.jsonファイルを作成"""

import os

# OpenMPのスレッド数、Intel MKL 系を制限
os.environ["OMP_NUM_THREADS"] = "6"
os.environ["MKL_NUM_THREADS"] = "6"


import gc
import re
from pathlib import Path

from helper.logs import logger_instance, save_traceback

L = logger_instance()


###################################################################################################
# def
###################################################################################################


def generate_summary_txt(txt_file: Path, response_text: str) -> str:
    """テキストから情報を抽出して .txt (要約) として保存"""
    summary_file = txt_file.with_name(txt_file.stem + "_summary.txt")

    # シンプルな抽出処理
    data = {
        "summary": re.search(r"\[SUMMARY\]\n(.*?)(?=\n\[|$)", response_text, re.DOTALL),
        "keywords": re.search(r"\[KEYWORDS\]\n(.*?)(?=\n\[|$)", response_text, re.DOTALL),
        "type": re.search(r"\[TYPE\]\n(.*?)(?=\n\[|$)", response_text, re.DOTALL),
        "date": re.search(r"\[DATE\]\n(.*?)(?=\n\[|$)", response_text, re.DOTALL),
    }

    # 抽出結果を整形して保存
    with summary_file.open(mode="w", encoding="utf-8") as f:
        for k, v in data.items():
            content = v.group(1).strip() if v else "不明"
            f.write(f"[{k.upper()}]\n{content}\n\n")

    gc.collect()
