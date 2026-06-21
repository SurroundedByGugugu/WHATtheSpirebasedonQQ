# clean_pycache.py
from pathlib import Path
import shutil

def clean_pycache(root: Path) -> None:
    count = 0

    for path in root.rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path)
            print(f"已删除：{path}")
            count += 1

    print(f"\n清理完成，共删除 {count} 个 __pycache__ 文件夹。")

if __name__ == "__main__":
    clean_pycache(Path.cwd())