from lib.downloader import FileDownloader
from lib.console import ProgressBar, notice, print
from utils.util import UnityUtils, ZipUtils
from os import path
import os
import base64
from lib.encryption import convert_string, create_key
import json
import argparse
APK_URL = "https://d.apkpure.com/b/XAPK/com.YostarJP.BlueArchive?version=latest&nc=arm64-v8a&sv=24"
TEMP_DIR = "Temp"
os.makedirs(TEMP_DIR, exist_ok=True)
def download_apk_file(apk_url: str) -> str:
    print("Download APK to retrieve server URL...")
    if not (
        (
            apk_req := FileDownloader(
                apk_url,
                request_method="get",
                use_cloud_scraper=True,
            )
        )
        and (apk_data := apk_req.get_response(True))
    ):
        raise LookupError("Cannot fetch apk info.")

    apk_path = path.join(
        TEMP_DIR,
        apk_data.headers["Content-Disposition"]
        .rsplit('"', 2)[-2]
        .encode("ISO8859-1")
        .decode(),
    )
    apk_size = int(apk_data.headers.get("Content-Length", 0))

    if path.exists(apk_path) and path.getsize(apk_path) == apk_size:
        return apk_path

    with ProgressBar(apk_size, "Downloading APK...", "B") as bar:
        bar.item_text(apk_path.split("/")[-1])
        FileDownloader(
            apk_url,
            request_method="get",
            enable_progress=True,
            use_cloud_scraper=True,
        ).save_file(apk_path)

    return apk_path

def extract_apk_file(apk_path: str) -> None:
    """Extract the XAPK file."""
    apk_files = ZipUtils.extract_zip(
        apk_path, path.join(TEMP_DIR), keywords=["apk"]
    )

    ZipUtils.extract_zip(
        apk_files, path.join(TEMP_DIR, "Data"), zips_dir=TEMP_DIR
    )
def decode_server_url(data: bytes) -> str:
    """
    Decodes the server URL from the given data.

    Args:
        data (bytes): Binary data to decode.

    Returns:
        str: Decoded server URL.
    """
    ciphers = {
        "ServerInfoDataUrl": "X04YXBFqd3ZpTg9cKmpvdmpOElwnamB2eE4cXDZqc3ZgTg==",
        "DefaultConnectionGroup": "tSrfb7xhQRKEKtZvrmFjEp4q1G+0YUUSkirOb7NhTxKfKv1vqGFPEoQqym8=",
        "SkipTutorial": "8AOaQvLC5wj3A4RC78L4CNEDmEL6wvsI",
        "Language": "wL4EWsDv8QX5vgRaye/zBQ==",
    }
    b64_data = base64.b64encode(data).decode()
    json_str = convert_string(b64_data, create_key("GameMainConfig"))
    obj = json.loads(json_str)
    encrypted_url = obj[ciphers["ServerInfoDataUrl"]]
    url = convert_string(encrypted_url, create_key("ServerInfoDataUrl"))
    return url
def get_server_url() -> str:
    """Decrypt the server version from the game's binary files."""
    print("Retrieving game info...")
    url = version = ""
    for dir, _, files in os.walk(
        path.join(path.join(TEMP_DIR, "Data"), "assets", "bin", "Data")
    ):
        for file in files:
            if url_obj := UnityUtils.search_unity_pack(
                path.join(dir, file), ["TextAsset"], ["GameMainConfig"], True
            ):
                url = decode_server_url(url_obj[0].read().m_Script.encode("utf-8", "surrogateescape"))  # type: ignore
                notice(f"Get URL successfully: {url}")
            if version_obj := UnityUtils.search_unity_pack(
                path.join(dir, file), ["PlayerSettings"]
            ):
                try:
                    version = version_obj[0].read().bundleVersion  # type: ignore
                except:
                    version = "unavailable"
                print(f"The apk version is {version}.")

            if url and version:
                break

    if not url:
        raise LookupError("Cannot find server url from apk.")
    if not version:
        notice("Cannot retrieve apk version data.")
    return url
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Yostar server URL for Blue Archive JP")
    parser.add_argument("output_path", help="output file for server url")

    args = parser.parse_args()
    apk_path = download_apk_file(APK_URL)
    extract_apk_file(apk_path)
    with open(args.output_path, "wb") as fs:
        fs.write(f"BA_SERVER_URL={get_server_url()}".encode())