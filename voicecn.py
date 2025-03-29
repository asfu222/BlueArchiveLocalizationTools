import json
import os
import binascii
from pathlib import Path
import subprocess
import sys
import argparse
import shutil
from lib.encryption import zip_password
def patch_voice_excel(voice_excel_path: Path, voice_file_names):
    with open(voice_excel_path, "r", encoding = "utf8") as f:
        voice_data = json.loads(f.read())
    id_s = {struct["Id"] for struct in voice_data}
    uid_s = {struct["UniqueId"] for struct in voice_data}
    id_c = 114514 # Just some identifiable hash
    uid_c = max(uid_s)+1 # Unique ID | on each update it changes
    for fpath in sorted(voice_file_names):
        voicepath = str(fpath.with_suffix('')).replace('\\', '/')
        while id_c in id_s:
            id_c+=1
        voice_data.append({
            "UniqueId": uid_c,
            "Id": id_c,
            "Nation_": [
                "All"
            ],
            "Path": [
                voicepath
            ],
            "Volume": [
                1.0
            ]
        })
        uid_c+=1
        id_c+=1

    with open(voice_excel_path, "wb") as fs:
        fs.write(json.dumps(voice_data, indent=4).encode())
def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.loads(f.read())
def load_voice_mappings(voice_excel_path):
    voice_mappings = {}
    voice_data = load_data(voice_excel_path)
    for entry in voice_data:
        voice_id_str = entry["Path"][0].split("/")[-1]  # Extract string VoiceId
        voice_mappings[voice_id_str] = entry["Id"]  # Map to integer Id
    return voice_mappings
def update_scenario_voice_ids(input_filepath, output_filepath, voice_excel_path = "./VoiceExcel.json"):
    data = load_data(input_filepath)
    voice_mappings = load_voice_mappings(voice_excel_path)
    
    for item in data:
        if item["VoiceId"] in voice_mappings:
            item["VoiceId"] = voice_mappings[item["VoiceId"]]
    
    with open(output_filepath, 'wb') as f_out:
        f_out.write(json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8'))
    
    print(f"Updated scenario script saved to {output_filepath}")
def build_scenario_script(input_filepath, output_filepath):
    data = load_data(input_filepath)
    for item in data:
        if isinstance(item["VoiceId"], str): # Strip unmapped (unused) Voice IDs
            item["VoiceId"] = 0
    
    with open(output_filepath, 'wb') as f_out:
        f_out.write(json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8'))
    
    print(f"Deployment scenario script saved to {output_filepath}")
def generate_voice_zip(gamedata_root: Path):
    voice_parents = set()
    voice_file_names = []
    for file in gamedata_root.rglob("*.ogg"):
        voice_file_names.append(file.relative_to(gamedata_root))
        new_name = file.with_name(file.name.lower())
        file.rename(new_name)
        voice_parents.add(file.parent)
    for voice_parent in voice_parents:
        password_str = zip_password(voice_parent.name.lower())
        cmd = ["zip", "-r", "-X", "-9", "-P", password_str, voice_parent.name, "."]
        subprocess.run(cmd, cwd=voice_parent, check=True)
        zip_filename = voice_parent.with_suffix('.zip')
        created_zip = voice_parent / zip_filename.name
        destination = voice_parent.parent / zip_filename.name
        shutil.move(str(created_zip), str(destination))
        if voice_parent.exists():
            shutil.rmtree(str(voice_parent))
        print(f"Built voice zip for {voice_parent.name}")
    for file in gamedata_root.rglob("*.ogg"):
        file.unlink()
    return sorted(voice_file_names)
def main(voice_file_names_path: Path, scenario_script_path: Path, voice_excel_path: Path):
    with open(voice_file_names_path, "r", encoding = "utf8") as f:
        voice_file_names = json.loads(f.read())
        voice_file_names = [Path(fpath) for fpath in voice_file_names]
    patch_voice_excel(voice_excel_path, voice_file_names)
    update_scenario_voice_ids(scenario_script_path, scenario_script_path, voice_excel_path)
    build_scenario_script(scenario_script_path, scenario_script_path)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Excel files and apply replacements.")
    parser.add_argument("gamedata_root", type=Path, help="Path to GameData root for voice files")
    parser.add_argument("output_filepath", type=Path, help="Path to save the voice file names.")
    args = parser.parse_args()
    
    voice_file_names = generate_voice_zip(args.gamedata_root)
    voice_file_names = [str(fpath) for fpath in voice_file_names]
    with open(args.output_filepath, "wb") as f:
        f.write(json.dumps(voice_file_names, separators=(',', ':'), ensure_ascii=False).encode())
