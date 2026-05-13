"""Constant values."""

import datetime
from pathlib import Path

from pydantic import BaseModel


class D(BaseModel):
    """Directory paths."""

    repo: Path = Path(__file__).resolve().parent.parent.parent
    src: Path = repo / "src"
    helper: Path = src / "helper"
    data: Path = repo / "data"
    output: Path = data / f"output/{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # local LLM 用
    cache: Path = repo / ".cache"
    models: Path = cache / "models"
    llm: Path = models / "llm"
    embedding: Path = models / "embedding"
    lancedb: Path = cache / "lancedb"
