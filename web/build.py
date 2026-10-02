"""Build versioned static assets without modifying the original game source."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

WEB = Path(__file__).resolve().parent
ROOT = WEB.parent
DIST = WEB / "dist"
ASSETS = ("index.html", "style.css", "app.js", "bootstrap.js", "worker.js", "_headers")


def replace_reference(text, old, new):
    if old not in text:
        raise ValueError(f"Missing asset reference: {old}")
    return text.replace(old, new)


def build():
    missing = [name for name in (*ASSETS, "bridge.py") if not (WEB / name).is_file()]
    if missing:
        raise SystemExit("Missing web source files: " + ", ".join(missing))
    DIST.mkdir(exist_ok=True)
    # Source allowlist excludes bot configuration, saved games and Git metadata.
    with zipfile.ZipFile(DIST / "engine.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for folder in ("app", "data", "game", "storage"):
            for path in sorted((ROOT / folder).rglob("*.py")):
                archive.write(path, path.relative_to(ROOT).as_posix())
        archive.write(WEB / "bridge.py", "web_bridge.py")

    digest = hashlib.sha256((DIST / "engine.zip").read_bytes()).hexdigest()[:16]
    sources = {name: (WEB / name).read_text(encoding="utf-8") for name in ASSETS}
    fingerprint = hashlib.sha256(digest.encode())
    for name in ASSETS:
        fingerprint.update(name.encode())
        fingerprint.update(sources[name].encode("utf-8"))
    version = fingerprint.hexdigest()[:16]
    emitted = {"engine.zip"}

    def emit(name, content):
        (DIST / name).write_text(content, encoding="utf-8")
        emitted.add(name)

    # Stable aliases keep old entry points readable. The new page references only
    # versioned assets, including its worker, manifest and Python bundle.
    engine_name = f"engine.{digest}.zip"
    shutil.copyfile(DIST / "engine.zip", DIST / engine_name)
    emitted.add(engine_name)
    manifest = json.dumps({"engine": digest, "version": version})
    emit("build.json", manifest)
    emit(f"build.{version}.json", manifest)
    worker = replace_reference(sources["worker.js"], "./build.json", f"./build.{version}.json")
    worker = replace_reference(worker, "./engine.zip?v=${encodeURIComponent(engine)}",
                               "./engine.${encodeURIComponent(engine)}.zip")
    app = replace_reference(sources["app.js"], "./worker.js", f"./worker.{version}.js")
    bootstrap = replace_reference(sources["bootstrap.js"], "./app.js", f"./app.{version}.js")
    for name, content in (("worker.js", worker), ("app.js", app),
                          ("bootstrap.js", bootstrap), ("style.css", sources["style.css"])):
        emit(name, content)
        stem, extension = name.rsplit(".", 1)
        emit(f"{stem}.{version}.{extension}", content)
    index = replace_reference(sources["index.html"], "./bootstrap.js", f"./bootstrap.{version}.js")
    index = replace_reference(index, "./style.css", f"./style.{version}.css")
    emit("index.html", index)
    emit("_headers", sources["_headers"])
    with zipfile.ZipFile(WEB / "cloudflare-upload.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(emitted):
            archive.write(DIST / name, name)
    print(f"Built: {DIST} (version {version})")
    print(f"Upload: {WEB / 'cloudflare-upload.zip'}")


if __name__ == "__main__":
    build()
