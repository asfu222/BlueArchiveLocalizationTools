from lib.downloader import FileDownloader
from lib.console import ProgressBar, notice
from utils.util import ZipUtils
from os import path
import os
APK_URL = "https://d.apkpure.com/b/XAPK/com.YostarJP.BlueArchive?version=latest&nc=arm64-v8a&sv=24"
TEMP_DIR = "Temp"
os.makedirs(TEMP_DIR, exist_ok=True)
def download_apk_file(apk_url: str) -> str:
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

if not path.exists(path.join(TEMP_DIR, "Data")):
    notice("Download APK and setting up resources.")
    apk_path = download_apk_file(APK_URL)
    extract_apk_file(apk_path)