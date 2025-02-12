import os
import importlib
from lib.console import notice
from pathlib import Path
import json
import flatbuffers
from lib.encryption import xor_with_key

class TableRepackerImpl:
    def __init__(self, flat_data_module_name):
        try:
            flat_data_lib = importlib.import_module(flat_data_module_name)
            self.repack_wrapper_lib = importlib.import_module(
                f"{flat_data_module_name}.repack_wrapper"
            )
        except Exception as e:
            notice(
                f"Cannot import FlatData module. Make sure FlatData is available in Extracted folder. {e}",
                "error",
            )
    def repackExcelZipJson(self, json_path: Path):
        table_type = json_path.stem
        if not table_type:
            raise ValueError("JSON data must include a 'table' key indicating the table type.")
        pack_func_name = f"pack_{table_type}"
        pack_func = getattr(self.repack_wrapper_lib, pack_func_name, None)
        if not pack_func:
            raise ValueError(f"No pack function found for table type: {table_type}.")
        with open(json_path, 'r', encoding = 'utf-8') as f:
            json_data = json.loads(f.read())
            builder = flatbuffers.Builder(4096)
            offset = pack_func(builder, json_data)
            builder.Finish(offset)
            return xor_with_key(table_type, bytes(builder.Output()))