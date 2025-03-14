import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZipFile
from extractor import TablesExtractor
from repacker import TableRepackerImpl
from lib.encryption import zip_password
from lib.console import notice

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

def main(excel_input_path: Path, repl_input_dir: Path, output_filepath: Path) -> None:
    import setup_flatdata
    packer = TableRepackerImpl('Extracted.FlatData')
    source_dir = Path(f'Extracted/Table/{excel_input_path.stem}')
    if not source_dir.exists():
        TablesExtractor('Extracted', excel_input_path.parent).extract_table(excel_input_path.name)
    
    with tempfile.TemporaryDirectory() as temp_extract_dir:
        temp_extract_path = Path(temp_extract_dir)
        with ZipFile(excel_input_path, "r") as excel_zip:
            excel_zip.setpassword(zip_password("Excel.zip"))
            excel_zip.extractall(path=temp_extract_path)
        
        for file in source_dir.iterdir():
            target_file = temp_extract_path / f"{file.stem.lower()}.bytes"
            repl_file = repl_input_dir / file.name
            if repl_file.exists():
                apply_replacements(file, repl_file)
                new_content = packer.repackExcelZipJson(file)
                with open(target_file, "wb") as tf:
                    tf.write(new_content)
        password_str = zip_password("Excel.zip").decode()
        cmd = ["zip", "-r", "-9", "-P", password_str, str(output_filepath.resolve()), "."]
        subprocess.run(cmd, cwd=temp_extract_path, check=True)
    
    notice(f"Outputted modified zip to {output_filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Excel files and apply replacements.")
    parser.add_argument("excel_input_path", type=Path, help="Path to the Excel.zip file.")
    parser.add_argument("repl_input_dir", type=Path, help="Path to the directory with replacement files for Excel.zip.")
    parser.add_argument("output_filepath", type=Path, nargs="?", default=None, help="Path to save the modified Excel.zip. Defaults to the input file path.")
    args = parser.parse_args()

    output_filepath = args.output_filepath if args.output_filepath else args.excel_input_path
    main(args.excel_input_path, args.repl_input_dir, output_filepath)
