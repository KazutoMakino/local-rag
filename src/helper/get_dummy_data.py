"""ダミーデータをダウンロード"""

import gc
import re
from pathlib import Path

import requests
import untangle
from tqdm import tqdm

from helper.cfg import Cfg
from helper.consts import D
from helper.logs import logger_instance, save_traceback

L = logger_instance()

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
    def __init__(self):
        pass

    def download_data(self):
        L.info("start")

        cfg = Cfg()
        dir_save = D().data / cfg.dir_data
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
    """_summary_

    Args:
        keyword (str): _description_

    Returns:
        dict[str, str]: _description_
    """
    # ベースとなるURL
    base_url = "https://kokkai.ndl.go.jp/api/1.0/speech"

    # クエリパラメータを辞書で定義
    params = {"maximumRecords": 100, "any": keyword}

    # リクエストを送信
    response = requests.get(base_url, params=params)
    response.raise_for_status()  # エラーがあれば例外を発生させる

    # response.text を untangle に渡す
    obj = untangle.parse(response.text)

    dict_url: dict[str, str] = {}
    # dataプロパティが存在するか確認しつつループ
    if hasattr(obj, "data") and hasattr(obj.data, "records"):
        for record in obj.data.records.record:
            speech_record = record.recordData.speechRecord
            url = speech_record.speechURL.cdata
            issue_id = url.split("/")[-2]
            dict_url[issue_id] = f"https://kokkai.ndl.go.jp/txt/{issue_id}"

    return dict_url


def clean_text(text: str) -> str:
    """_summary_

    Args:
        text (str): _description_

    Returns:
        str: _description_
    """
    text = re.sub(r"[\r─━・]", "", text)
    text = text.replace("　", " ")
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def get_kokkai_text_from_api(url: str) -> str:
    """_summary_

    Args:
        url (str): _description_

    Returns:
        str: _description_
    """
    try:
        issue_id = url.split("/")[-1]
        if not issue_id:
            return "Could not extract issueID from the URL."
        api_url = f"https://kokkai.ndl.go.jp/api/speech?issueID={issue_id}&recordPacking=json"
        response = requests.get(api_url)
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
