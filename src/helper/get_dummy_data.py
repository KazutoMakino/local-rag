"""ダミーデータをダウンロード"""

import gc
import re

import requests
import untangle
from helper.cfg import CFG
from helper.consts import DIRS
from helper.logs import L, save_traceback
from tqdm import tqdm

#######################################################################################
# main
#######################################################################################


def main() -> None:
    L.info("start")

    data_downloader = DataDownloader()
    data_downloader.download_data()

    L.info("end")


#######################################################################################
# class
#######################################################################################


class DataDownloader:
    def download_data(self):
        """ダミーデータをダウンロード"""
        L.info("start")

        dir_save = DIRS.data / CFG.dir_data
        dir_save.mkdir(parents=True, exist_ok=True)
        dict_url = get_kokkai_data(keyword="スタートアップ")
        for name, url in tqdm(dict_url.items(), dynamic_ncols=True):
            path_save = dir_save / f"{name}.txt"
            if path_save.exists():
                continue
            text = get_kokkai_text_from_api(url)
            path_save.write_text(text, encoding="utf-8")
            gc.collect()

        L.info("end")


#######################################################################################
# def
#######################################################################################


def get_kokkai_data(keyword: str) -> dict[str, str]:
    """国会文書の ID と URL のペアを取得する

    Args:
        keyword (str): 国会文書におけるデータベースから拾ってくる際に用いるキーワード

    Returns:
        dict[str, str]: 国会文書の ID と URL のペア
    """
    # ベースとなるURL
    base_url = "https://kokkai.ndl.go.jp/api/1.0/speech"
    # クエリパラメータを辞書で定義
    params = {"maximumRecords": 50, "any": keyword}
    # リクエストを送信
    response = requests.get(base_url, params=params, timeout=10)
    # エラーがあれば例外を発生させる
    response.raise_for_status()
    # response.text を untangle に渡す
    obj = untangle.parse(response.text)
    dict_url: dict[str, str] = {}
    # dataプロパティが存在するか確認 しつつループ
    if hasattr(obj, "data") and hasattr(obj.data, "records"):
        for record in obj.data.records.record:
            speech_record = record.recordData.speechRecord
            url = speech_record.speechURL.cdata
            issue_id = url.split("/")[-2]
            dict_url[issue_id] = f"https://kokkai.ndl.go.jp/txt/{issue_id}"

    return dict_url


def clean_text(text: str) -> str:
    """不要な文字列を削除

    Args:
        text (str): 文字列

    Returns:
        str: 不要な部分が削除された文字列
    """
    text = re.sub(r"[\r─━・]", "", text)
    text = text.replace("　", " ")
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def get_kokkai_text_from_api(url: str) -> str:
    """ダミーデータをダウンロード

    Args:
        url (str): 国会データの URL

    Returns:
        str: 国会文書
    """
    try:
        issue_id = url.split("/")[-1]
        if not issue_id:
            return "Could not extract issueID from the URL."
        api_url = f"https://kokkai.ndl.go.jp/api/speech?issueID={issue_id}&recordPacking=json"
        response = requests.get(url=api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "speechRecord" not in data or not data["speechRecord"]:
            return "No speech records found for this issue."
        full_text = []
        for record in data["speechRecord"]:
            cleaned_speech = clean_text(record["speech"])
            if cleaned_speech:
                full_text.append(cleaned_speech)
        return "\n".join(full_text)

    except requests.exceptions.RequestException as e:
        return f"Error fetching URL: {e}"
    except (KeyError, TypeError) as e:
        return f"Error parsing JSON response: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


#######################################################################################

if __name__ == "__main__":
    try:
        main()
    except Exception:
        save_traceback()
    exit()
