import zipfile
from pathlib import Path

files_dir = Path("files")
zip_path = Path("gtfs.zip")

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for txt_file in sorted(files_dir.glob("*.txt")):
        zf.write(txt_file, txt_file.name)

print(f"Created {zip_path} with {len(list(files_dir.glob('*.txt')))} files")
