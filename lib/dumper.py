"""Dump il2cpp file to csharp file."""

import json
import os
from os import path

from lib.downloader import FileDownloader
from utils.util import CommandUtils, FileUtils, ZipUtils

IL2CPP_ZIP = "https://github.com/asfu222/Il2CppInspectorRedux/releases/latest/download/Il2CppInspectorRedux.CLI-linux-x64.zip"
ZIP_NAME = "Il2CppInspectorRedux.CLI.zip"

class IL2CppDumper:

    def __init__(self) -> None:
        self.project_dir = ""

    def get_il2cpp_dumper(self, save_path: str) -> None:
        FileDownloader(IL2CPP_ZIP).save_file(path.join(save_path, ZIP_NAME))
        ZipUtils.extract_zip(path.join(save_path, ZIP_NAME), path.join(save_path, "Il2CppInspector"))
        self.project_dir = path.join(save_path, "Il2CppInspector")

    def dump_il2cpp(
        self,
        extract_path: str,
        il2cpp_path: str,
        global_metadata_path: str,
        max_retries: int = 1,
    ) -> None:
        """Dump il2cpp with using il2cpp-dumper.
        Args:
            extract_path (str): Absolute path to extract dump file.
            il2cpp_path (str): Absolute path to il2cpp lib.
            global_metadata_path (str): Absolute path to global metadata.
            max_retries (int): Max retry count for dump when dump failed.


        Raises:
            RuntimeError: Raise error when dump unsuccess.
        """

        os.makedirs(extract_path, exist_ok=True)

        success, err = CommandUtils.run_command(
            "./Il2CppInspector",
            "--bin",
            il2cpp_path,
            "--metadata",
            global_metadata_path,
            "--select-outputs",
            "--cs-out",
            path.join(extract_path, "dump.cs"),
            "--must-compile",
            cwd=self.project_dir
        )
        print(success, err)
        '''
        success, err = CommandUtils.run_command(
            "dotnet",
            "run",
            "--framework",
            "net8.0",
            il2cpp_path,
            global_metadata_path,
            extract_path,
            cwd=self.project_dir,
        )
        if not success:
            if max_retries == 0:
                raise RuntimeError(
                    f"Error occurred during dump the lib2cpp file. Retry might solve this issue. Info: {err}"
                )
            return self.dump_il2cpp(
                extract_path, il2cpp_path, global_metadata_path, max_retries - 1
            )
        '''

        return None
