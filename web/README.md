# 私货之塔 · 浏览器单人版

所有新增代码在 web/，现有 main.py、app/、data/、game/、storage/ 不需要修改。浏览器通过 Pyodide 执行现有 Python 引擎，无需服务器运行 Python。当前只提供单人玩法，没有多人或 PVP 服务。

## 本地打开

双击本目录中的 **启动网页版.cmd**，保持终端运行，然后用浏览器打开终端显示的 **http://127.0.0.1:8765/**。

也可以在项目根目录执行：

```powershell
python -B web/serve.py
```

需要本机已有 Python 3.10 或以上。端口被占用时可用 `python -B web/serve.py --port 8766`。按 Ctrl+C 停止预览。不要双击 index.html：file:// 无法正常加载模块、Worker 和资源包。

## 上传到自己的 Cloudflare

1. 在项目根目录运行 `python -B web/build.py`。
2. 打开 Cloudflare 控制台的 **Workers & Pages**，创建 **Pages / Direct Upload** 项目。
3. 上传 **web/cloudflare-upload.zip**，或整个 **web/dist** 文件夹。ZIP 根目录必须包含 index.html；不要上传项目根目录或只有 index.html 的文件夹。
4. 部署后先打开分配的 pages.dev 地址确认游戏可以载入。
5. 在该 Pages 项目的 **Custom domains** 中添加自己的域名，按页面提示配置 DNS。绑定根域名和子域名的 DNS 要求不同，以 Cloudflare 显示的要求为准。

已有 Pages 项目可上传新的部署。此实现仅生成部署文件，不会替你发布站点或改动域名。

官方说明：
- [Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/)
- [Custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/)

## 文件与玩法

- index.html / style.css / app.js：界面与单人操作。
- bootstrap.js：识别 file://、脚本缺失和启动失败。
- worker.js：在独立线程加载 Pyodide 并运行游戏。
- bridge.py：适配现有 GameService，输出网页所需状态。
- build.py：只读取原有引擎，生成 dist 和上传 ZIP。
- serve.py：仅提供静态文件的本地 HTTP 预览。
- verify.py / browser_check.cjs：适配层及浏览器启动回归检查。

选角色后按开局选项和路线按钮前进。战斗时先选择敌人，再点击手牌；用“结束回合”结算。事件、奖励、火堆、商店及特殊选牌的完整提示会出现在冒险记录，可直接输入原有单人命令，也可点击提示中的命令名称再补参数。输入 `/card help` 查看网页帮助。

**当前版本没有持久存档**：刷新、关闭标签页会结束本局，离开页面前会提示。游戏不跨设备同步。

首次打开会从 jsDelivr 下载固定版本的 Pyodide（314.0.6），通常比后续打开慢；浏览器会缓存运行环境，但此版不承诺离线可玩。网络需能访问 cdn.jsdelivr.net；超过 150 秒会显示错误和重试入口。加载状态显示具体阶段和已等待秒数。

[Pyodide 官方 Worker 文档](https://pyodide.org/en/stable/usage/webworker.html)

## 更新游戏

修改原有游戏内容后，再运行 `python -B web/build.py` 并重新上传。资源包只包含 app、data、game、storage 的 Python 源码及网页适配层，不包含 bot_config.ini、QQ 配置、原有存档或 Git 文件。浏览器需要拿到引擎源码才能运行，部署到公开网站后这些打包源码同样可以被下载。

## 启动报错排查

- ERR_FILE_NOT_FOUND：使用完整生成的 dist；build.py 会先检查入口文件是否齐全。
- origin null / CORS / file://：使用启动网页版.cmd 提供的 HTTP 地址。
- 游戏运行环境下载失败：检查网络是否能打开 jsDelivr；刷新重试。
- engine.zip / build.json 找不到：部署了源码目录或漏传文件；重新上传 cloudflare-upload.zip。

## 部署更新与缓存

构建会为启动脚本、界面脚本、样式、Worker、版本清单和引擎包生成带内容版本的文件名。页面会引用同一构建版本，避免浏览器缓存的旧界面与新引擎混用。首次从旧版升级时，部署成功后请结束当前游戏再强制刷新一次；刷新会丢失本局进度。

根页面及固定名称的兼容入口设置为 no-cache。若 Cloudflare 中存在覆盖缓存响应头的自定义规则，应让入口 HTML 遵循源站缓存策略。CSP 已允许 Cloudflare Web Analytics 的脚本和上报域名；本项目不主动注入或启用统计。
