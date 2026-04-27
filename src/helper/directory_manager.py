"""ディレクトリマネージャー"""

from consts import D


def mkdir_all():
    """ディレクトリを作成"""
    # data
    D().data.mkdir(parents=True, exist_ok=True)
    D().output.mkdir(parents=True, exist_ok=True)
    # model
    D().cache.mkdir(parents=True, exist_ok=True)
    D().models.mkdir(parents=True, exist_ok=True)
    D().llm.mkdir(parents=True, exist_ok=True)
    D().embedding.mkdir(parents=True, exist_ok=True)
    D().storage.mkdir(parents=True, exist_ok=True)
    D().lancedb.mkdir(parents=True, exist_ok=True)
