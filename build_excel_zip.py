import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZipFile
from extractor import TablesExtractor
from repacker import TableRepackerImpl
from lib.encryption import zip_password
import shutil

def apply_replacements(input_filepath: Path, replacements_filepath: Path) -> Path:
    with open(input_filepath, "r", encoding="utf8") as inp_f:
        data = json.loads(inp_f.read())
    with open(replacements_filepath, "r", encoding="utf8") as repl_f:
        replacements = json.loads(repl_f.read())
    for repl_obj in replacements:
        fields = repl_obj["fields"]
        mapping_list = repl_obj["mappings"]
        
        lookup = {tuple(mapping["old"]): (mapping["new"], mapping.get("target_index", 0), mapping.get("replacement_count", float("inf"))) for mapping in mapping_list}
        
        for struct in data:
            key = tuple(struct[field] for field in fields)
            if key in lookup:
                new_values, target_index, replacement_count = lookup[key]
                if target_index != 0:
                    lookup[key] = (new_values, target_index-1, replacement_count)
                    continue
                if replacement_count > 0:
                    lookup[key] = (new_values, target_index, replacement_count-1)
                else:
                    continue
                for idx, field in enumerate(fields):
                    struct[field] = new_values[idx]
    out_path = input_filepath.parent / "temp" / input_filepath.name
    out_path.parent.mkdir(parents=True, exist_ok=True)
        
    with open(out_path, "wb") as out_f:
        out_f.write(json.dumps(data, separators=(',', ':'), ensure_ascii=False).encode())
        return out_path


def main(excel_input_path: Path, repl_input_dir: Path, output_filepath: Path) -> None:
    import setup_flatdata
    packer = TableRepackerImpl('Extracted.FlatData')
    source_dir = Path(f'Extracted/Table/{excel_input_path.stem}')
    source_binary_dir = Path(f'Extracted/Temp/Table/{excel_input_path.stem}')
    if not source_dir.exists():
        print("Extracting source zip JSONs...")
        TablesExtractor('Extracted', excel_input_path.parent).extract_table(excel_input_path.name)
    if not source_binary_dir.exists():
        print("Extracting source zip binaries...")
        source_binary_dir.mkdir(parents=True, exist_ok=True)
        with ZipFile(excel_input_path, "r") as excel_zip:
            excel_zip.setpassword(zip_password("Excel.zip"))
            excel_zip.extractall(path=source_binary_dir)
    with tempfile.TemporaryDirectory() as temp_extract_dir:
        temp_extract_path = Path(temp_extract_dir)
        shutil.copytree(source_binary_dir, temp_extract_dir, dirs_exist_ok=True)
        print("Applying replacements...")
        for file in source_dir.iterdir():
            target_file = temp_extract_path / f"{file.stem.lower()}.bytes"
            repl_file = repl_input_dir / file.name
            if repl_file.exists():
                out_file = apply_replacements(file, repl_file)
                new_content = packer.repackExcelZipJson(out_file)
                if out_file.exists():
                    out_file.unlink()
                with open(target_file, "wb") as tf:
                    tf.write(new_content)
        password_str = zip_password("Excel.zip").decode()
        cmd = ["zip", "-r", "-X", "-9", "-P", password_str, str(output_filepath.resolve()), "."]
        subprocess.run(cmd, cwd=temp_extract_path, check=True)
    temp_dir = source_dir / "temp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    print(f"Outputed modified zip to {output_filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Excel files and apply replacements.")
    parser.add_argument("excel_input_path", type=Path, help="Path to the Excel.zip file.")
    parser.add_argument("repl_input_dir", type=Path, help="Path to the directory with replacement files for Excel.zip.")
    parser.add_argument("output_filepath", type=Path, nargs="?", default=None, help="Path to save the modified Excel.zip. Defaults to the input file path.")
    args = parser.parse_args()

    output_filepath = args.output_filepath if args.output_filepath else args.excel_input_path
    main(args.excel_input_path, args.repl_input_dir, output_filepath)
