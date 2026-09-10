"""Build and serve the browser version locally. No Python game server is used."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from build import build, DIST

class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript",
                      ".mjs": "text/javascript", ".wasm": "application/wasm"}
    def end_headers(self):
        # Mirror Cloudflare's shared headers, including CSP, during local testing.
        for line in (DIST / "_headers").read_text(encoding="utf-8").splitlines():
            if line.startswith("  ") and not line.strip().startswith("Cache-Control:"):
                name, value = line.strip().split(":", 1)
                self.send_header(name, value.strip())
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    build()
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=str(DIST)))
    except OSError as error:
        raise SystemExit(f"Cannot start local preview: {error}. Try --port 8766.") from error
    print(f"Open http://127.0.0.1:{args.port}/ in your browser. Ctrl+C stops the preview.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
