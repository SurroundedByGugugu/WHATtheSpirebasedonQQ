// Classic script intentionally works even when index.html is opened via file://.
(function () {
  const message = document.getElementById("loading-message");
  const retry = document.getElementById("retry");
  retry.onclick = () => location.reload();
  function fail(text) {
    message.textContent = text;
    document.querySelector("#loading progress").hidden = true;
    retry.hidden = false;
  }
  if (location.protocol === "file:") {
    fail("不能直接双击 HTML 运行游戏。请双击 web 文件夹中的“启动网页版.cmd”，再打开终端显示的 http://127.0.0.1:8765 地址。部署时上传 cloudflare-upload.zip。");
    return;
  }
  const script = document.createElement("script");
  script.type = "module";
  script.src = "./app.js";
  script.onerror = () => fail("网页启动脚本加载失败。请运行 python -B web/build.py，并上传完整的 web/dist 文件夹或 cloudflare-upload.zip。");
  document.head.append(script);
  setTimeout(() => {
    if (!window.spireStarted) fail("网页启动脚本没有响应，请检查 app.js 是否完整上传，然后重新加载。");
  }, 15000);
})();