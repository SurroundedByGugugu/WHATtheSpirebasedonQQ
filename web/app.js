window.spireStarted = true;
const $ = (id) => document.getElementById(id);
let worker, ready = false, busy = true, state = null, target = null, requestId = 0;
let watchdog, loadingStarted, currentStage = "准备游戏";
const descriptions = [
  ["IRONCLAD", "铁甲战士", "HP 80，GOLD 99"],
  ["THE SILENT", "静默猎手", "HP 70，GOLD 99"],
  ["LUMINE", "昼·里辛塔法", "HP 70，GOLD 99"],
  ["YOIRINE", "Yoirine", "HP 70，GOLD 67"],
  ["SUZURI", "Suzuri", "HP 76，GOLD 99"],
  ["DEFECT", "故障机器人", "HP 75，GOLD 99"]
];
function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function button(label, command, className = "") {
  const node = el("button", label, className);
  node.type = "button";
  node.dataset.command = command;
  node.disabled = busy || !ready;
  return node;
}
function showRelicDetails(relic) {
  let dialog = $("relic-dialog");
  if (!dialog) {
    dialog = el("dialog", undefined, "relic-dialog");
    dialog.id = "relic-dialog";
    dialog.setAttribute("aria-labelledby", "relic-dialog-name");
    document.body.append(dialog);
  }
  const heading = el("div", undefined, "panel-heading");
  const name = el("h2", relic.name);
  name.id = "relic-dialog-name";
  const close = el("button", "关闭");
  close.type = "button";
  close.autofocus = true;
  close.onclick = () => dialog.close();
  heading.append(name, close);
  dialog.replaceChildren(heading, el("h3", "效果说明"),
    el("p", relic.info, "relic-info"), el("h3", "遗物故事"),
    el("p", relic.story, "relic-story"));
  dialog.showModal();
}
function setBusy(value) {
  busy = value;
  document.querySelectorAll("[data-command], #command-form button, #command, #new-run").forEach((node) => {
    node.disabled = value || !ready;
  });
  $("connection").textContent = value ? "正在处理…" : "准备就绪";
}
function showError(message, fatal = false) {
  $("error").textContent = message;
  $("error").hidden = false;
  if (fatal) {
    clearInterval(watchdog);
    ready = false;
    worker?.terminate();
    $("loading").hidden = false;
    $("loading-message").textContent = message;
    document.querySelector("#loading progress").hidden = true;
    $("retry").hidden = false;
    setBusy(true);
  } else setBusy(false);
}
function log(text, command) {
  if (!text) return;
  const entry = el("article", undefined, "log-entry");
  if (command) entry.append(el("div", command, "log-command"));
  entry.append(el("pre", text));
  $("log").append(entry);
  while ($("log").children.length > 40) $("log").firstElementChild.remove();
  $("log").scrollTop = $("log").scrollHeight;
}
function renderCharacters(characters) {
  $("characters").replaceChildren();
  characters.forEach((character, index) => {
    const [code, name, description] = descriptions[index] || ["TRAVELER", character.name, ""];
    const card = button("", "/card new " + character.index, "character character-" + index);
    card.append(el("span", "0" + (index + 1), "character-number"), el("span", code, "eyebrow"),
      el("h2", name), el("p", description), el("span", "以此角色出发 →", "character-action"));
    $("characters").append(card);
  });
}
function renderHints(text) {
  $("command-hints").replaceChildren();
  // Only copy command prefixes from engine-authored usage text; numbers are entered by the player.
  const commands = [...text.matchAll(/\/card\s+([a-z_]+)/g)].map((match) => match[1]);
  for (const command of [...new Set(commands)].filter((c) => !["multi", "mp", "pvp", "new", "ctrl"].includes(c)).slice(0, 14)) {
    const item = el("button", command, "hint-button");
    item.type = "button";
    item.onclick = () => { $("command").value = "/card " + command + " "; $("command").focus(); };
    $("command-hints").append(item);
  }
}
function render(data) {
  state = data;
  $("confirmation").hidden = !data.confirmation;
  renderCharacters(data.characters);
  const run = data.run;
  $("start").hidden = Boolean(run);
  $("game").hidden = !run;
  if (!run) return;
  $("player-name").textContent = run.name;
  $("location").textContent = "旅途 / " + run.node;
  $("stats").replaceChildren();
  for (const [label, value] of [["生命", run.hp + " / " + run.maxHp], ["能量", run.energy + " / " + run.maxEnergy], ["格挡", run.block], ["金币", run.gold], ["牌库", run.deckCount]]) {
    const stat = el("div", undefined, "stat");
    stat.append(el("span", label), el("strong", String(value)));
    $("stats").append(stat);
  }
  $("arena-title").textContent = run.battle ? "选择你的目标" : run.node;
  $("turn-label").textContent = run.battle ? "第 " + run.turn + " 回合" : "继续攀登";
  $("player-status").textContent = run.status;
  $("hand-panel").hidden = !run.battle;
  $("node-view").hidden = run.battle;
  $("node-view").textContent = run.view;
  $("enemies").replaceChildren();
  if (!run.enemies.some((enemy) => enemy.index === target)) target = run.enemies[0]?.index ?? null;
  for (const enemy of run.enemies) {
    const card = el("button", undefined, "enemy");
    card.type = "button";
    card.setAttribute("aria-pressed", String(target === enemy.index));
    card.append(el("span", "目标 " + enemy.index, "eyebrow"), el("h3", enemy.name),
      el("p", enemy.intent, "intent"), el("p", "生命 " + enemy.hp + " / " + enemy.maxHp + " · 格挡 " + enemy.block));
    const hp = el("progress"); hp.value = enemy.hp; hp.max = enemy.maxHp;
    hp.setAttribute("aria-label", enemy.name + "生命");
    card.append(hp);
    if (enemy.status) card.append(el("p", enemy.status, "status-text"));
    card.onclick = () => { target = enemy.index; render(state); };
    $("enemies").append(card);
  }
  $("choices").replaceChildren();
  for (const choice of [...run.choices, ...run.routes]) $("choices").append(button(choice.name, choice.command, "choice"));
  $("hand-count").textContent = String(run.hand.length);
  $("hand").replaceChildren();
  for (const card of run.hand) {
    const command = "/card play " + card.index + (target !== null ? " " + target : "");
    const node = button("", command, "playing-card type-" + card.type);
    node.title = card.summary;
    node.append(el("span", String(card.cost), "card-cost"), el("span", ({attack:"攻击",skill:"技能",power:"能力",status:"状态",curse:"诅咒"})[card.type] || card.type, "card-type"),
      el("h3", card.name), el("p", card.description, "card-description"));
    if (card.preview) node.append(el("p", card.preview, "card-preview"));
    node.append(el("span", "#" + card.index + " · 点击出牌", "card-index"));
    $("hand").append(node);
  }
  $("piles").replaceChildren();
  for (const [key, label] of [["draw", "抽牌堆"], ["discard", "弃牌堆"], ["exhaust", "消耗堆"]]) {
    $("piles").append(button(label + " " + (run.piles?.[key] ?? 0), "/card " + key));
  }
  $("relics").replaceChildren();
  if (!run.relics.length) $("relics").append(el("span", "暂无遗物"));
  for (const value of (run.relicDetails || run.relics)) {
    // Accept both cached legacy names and structured relic details.
    const relic = typeof value === "string"
      ? { name: value, info: "此遗物暂无效果说明，请重新加载以获取最新数据。", story: "暂无故事。" }
      : { name: value?.name || "遗物", info: value?.info || value?.description || "暂无效果说明。",
          story: value?.story || "暂无故事。" };
    const item = el("button", relic.name, "relic-button");
    item.type = "button";
    item.title = relic.info;
    item.setAttribute("aria-description", relic.info);
    item.setAttribute("aria-haspopup", "dialog");
    item.onclick = () => showRelicDetails(relic);
    $("relics").append(item);
  }
  $("potions").replaceChildren();
  if (!run.potions.length) $("potions").append(el("span", "暂无药水"));
  run.potions.forEach((name, index) => {
    const item = el("button", "[" + index + "] " + name);
    item.type = "button";
    item.onclick = () => {
      $("command").value = "/card potion " + index + (target !== null ? " " + target : "");
      $("command").focus();
      log("已填入药水指令，请核对目标后执行。");
    };
    $("potions").append(item);
  });
  $("boss").textContent = run.boss ? "本层 Boss · " + run.boss : "";
}
let activeCommand = "";
function send(command) {
  if (!ready || busy) return;
  command = command.trim();
  if (!command) return;
  if (!/^[/.。]/.test(command)) command = "/card " + command;
  $("error").hidden = true;
  activeCommand = command;
  setBusy(true);
  worker.postMessage({ type: "command", id: ++requestId, command });
}
function start() {
  try {
    worker = new Worker("./worker.js", { type: "module" });
    worker.onerror = (event) => showError("游戏线程启动失败：" + (event.message || "请检查 worker.js 是否存在，以及浏览器是否允许加载游戏资源。"), true);
    worker.onmessageerror = () => showError("游戏线程通信失败，请重新加载页面。", true);
    worker.onmessage = ({ data }) => {
      if (data.type === "progress") {
        currentStage = data.message;
        $("loading-message").textContent = currentStage;
        return;
      }
      if (data.type === "error") {
        showError((ready ? "本次操作失败：" : "游戏加载失败：") + data.message, !ready);
        return;
      }
      clearInterval(watchdog);
      ready = true;
      $("loading").hidden = true;
      $("console").hidden = false;
      setBusy(false);
      render(data.result);
      log(data.result.reply, activeCommand);
      renderHints(data.result.reply || data.result.run?.view || "");
      activeCommand = "";
    };
    loadingStarted = Date.now();
    watchdog = setInterval(() => {
      const seconds = Math.floor((Date.now() - loadingStarted) / 1000);
      if (seconds >= 150) {
        showError("加载超过 150 秒。可能无法连接运行环境下载地址 cdn.jsdelivr.net，或资源未完整上传。请检查网络后重新加载。", true);
      } else {
        $("loading-message").textContent = currentStage + "（已等待 " + seconds + " 秒）";
      }
    }, 1000);
    worker.postMessage({ type: "init", id: ++requestId });
  } catch (error) { showError("无法启动游戏：" + error.message, true); }
}
document.addEventListener("click", (event) => {
  const node = event.target.closest("[data-command]");
  if (node && !node.disabled) send(node.dataset.command);
});
$("command-form").addEventListener("submit", (event) => {
  event.preventDefault();
  if (ready && !busy) { send($("command").value); $("command").value = ""; }
});
$("new-run").onclick = () => {
  $("start").hidden = !$("start").hidden;
  if (!$("start").hidden) $("start").scrollIntoView({ behavior: "smooth" });
};
window.addEventListener("beforeunload", (event) => {
  if (state?.run) { event.preventDefault(); event.returnValue = ""; }
});
start();
