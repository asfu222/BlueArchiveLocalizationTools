import argparse
import json
from pathlib import Path
from zipfile import ZipFile
from extractor import TablesExtractor
from repacker import TableRepackerImpl
from lib.encryption import zip_password
from lib.console import notice
import io

def apply_replacements(input_filepath, replacements_filepath):
    with open(input_filepath, "r", encoding="utf8") as inp_f:
        data = json.loads(inp_f.read())
    with open(replacements_filepath, "r", encoding="utf8") as repl_f:
        replacements = json.loads(repl_f.read())
    for struct in data:
        for field in struct:
            if field not in replacements:
                continue
            if struct[field] not in replacements[field]:
                continue
            struct[field] = replacements[field][struct[field]]
    with open(input_filepath, "wb") as out_f:
        out_f.write(json.dumps(data, separators=(',', ':'), ensure_ascii=False).encode())

def main(excel_input_path: Path, repl_input_dir: Path) -> None:
    import setup_flatdata
    packer = TableRepackerImpl('Extracted.FlatData')
    source_dir = Path(f'Extracted/Table/{excel_input_path.stem}')
    if not source_dir.exists():
        TablesExtractor('Extracted', excel_input_path.parent).extract_table(excel_input_path.name)
    
    with ZipFile(excel_input_path, "r") as excel_zip:
        excel_zip.setpassword(zip_password("Excel.zip"))
        zip_data = io.BytesIO()
        with ZipFile(zip_data, "w") as temp_zip:
            for item in excel_zip.infolist():
                temp_zip.writestr(item.filename, excel_zip.read(item.filename))

        with ZipFile(excel_input_path, "w") as excel_zip:
            excel_zip.setpassword(zip_password("Excel.zip"))
            zip_data.seek(0)
            with ZipFile(zip_data, "r") as temp_zip:
                for file in source_dir.iterdir():
                    repl_file = repl_input_dir / file.name
                    if not repl_file.exists():
                        excel_zip.writestr(f"{file.stem.lower()}.bytes", temp_zip.read(f"{file.stem.lower()}.bytes"))
                        continue
                    apply_replacements(file, repl_file)
                    excel_zip.writestr(f"{file.stem.lower()}.bytes", packer.repackExcelZipJson(file))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Excel files and apply replacements.")
    parser.add_argument("excel_input_path", type=Path, help="Path to the directory containing Excel.zip.")
    parser.add_argument("repl_input_dir", type=Path, help="Path to the directory containing replacement files for Excel.zip.")
    args = parser.parse_args()
    main(args.excel_input_path, args.repl_input_dir)
