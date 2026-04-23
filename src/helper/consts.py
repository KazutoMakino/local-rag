"""Constant values."""

from pathlib import Path

from pydantic import BaseModel


class D(BaseModel):
    """Directory paths."""

    repo: Path = Path(__file__).resolve().parent.parent.parent
    src: Path = repo / "src"
    helper: Path = src / "helper"
    data: Path = repo / "data"

    # local LLM 用
    cache: Path = repo / ".cache"
    models: Path = cache / "models"
    llm: Path = models / "llm"
    embedding: Path = models / "embedding"
    storage: Path = cache / "storage"
    lancedb: Path = cache / "lancedb"
