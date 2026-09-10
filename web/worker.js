// Python runs in a dedicated worker so game calculations do not block the interface.
let runtime;
let dispatch;
let queue = Promise.resolve();

async function initialize() {
  self.postMessage({ type: "progress", message: "正在加载游戏运行环境，首次打开可能需要一点时间…" });
  const { loadPyodide } = await import("https://cdn.jsdelivr.net/pyodide/v314.0.6/full/pyodide.mjs");
  runtime = await loadPyodide({ indexURL: "https://cdn.jsdelivr.net/pyodide/v314.0.6/full/" });
  self.postMessage({ type: "progress", message: "正在载入角色、卡牌和高塔…" });
  const manifest = await fetch("./build.json", { cache: "no-store" });
  if (!manifest.ok) throw new Error("找不到 build.json，请上传完整的 dist 文件夹。");
  const { engine } = await manifest.json();
  const response = await fetch(`./engine.zip?v=${encodeURIComponent(engine)}`);
  if (!response.ok) throw new Error("游戏资源下载失败，请检查网络后重试。");
  runtime.unpackArchive(await response.arrayBuffer(), "zip", { extractDir: "/game" });
  runtime.runPython("import sys, os\nsys.path.insert(0, '/game')\nos.chdir('/game')\nfrom web_bridge import dispatch");
  dispatch = runtime.globals.get("dispatch");
  return JSON.parse(dispatch(""));
}

self.onmessage = ({ data }) => {
  queue = queue.then(async () => {
    try {
      const result = data.type === "init" ? await initialize() : JSON.parse(dispatch(data.command));
      self.postMessage({ type: "result", id: data.id, result });
    } catch (error) {
      self.postMessage({ type: "error", id: data.id, message: String(error.message || error) });
    }
  });
};
