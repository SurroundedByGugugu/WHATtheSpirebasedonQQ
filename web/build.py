"""Build a static Cloudflare upload without changing original source files."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

WEB = Path(__file__).resolve().parent
ROOT = WEB.parent
DIST = WEB / "dist"
ASSETS = ("index.html", "style.css", "app.js", "bootstrap.js", "worker.js", "_headers")


def build():
    missing = [name for name in (*ASSETS, "bridge.py") if not (WEB / name).is_file()]
    if missing:
        raise SystemExit("Missing web source files: " + ", ".join(missing))
    DIST.mkdir(exist_ok=True)
    for name in ASSETS:
        shutil.copyfile(WEB / name, DIST / name)
    # Explicit source allowlist: no bot configuration, save data, Git or credentials.
    with zipfile.ZipFile(DIST / "engine.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for folder in ("app", "data", "game", "storage"):
            for path in sorted((ROOT / folder).rglob("*.py")):
                archive.write(path, path.relative_to(ROOT).as_posix())
        archive.write(WEB / "bridge.py", "web_bridge.py")
    digest = hashlib.sha256((DIST / "engine.zip").read_bytes()).hexdigest()[:16]
    (DIST / "build.json").write_text(json.dumps({"engine": digest}), encoding="utf-8")
    with zipfile.ZipFile(WEB / "cloudflare-upload.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in (*ASSETS, "engine.zip", "build.json"):
            archive.write(DIST / name, name)
    print(f"Built: {DIST}")
    print(f"Upload: {WEB / 'cloudflare-upload.zip'}")


if __name__ == "__main__":
    build()
