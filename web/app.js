window.spireStarted = true;
const $ = (id) => document.getElementById(id);
let worker, ready = false, busy = true, state = null, target = null, requestId = 0;
let watchdog, loadingStarted, currentStage = "准备游戏";
const originalCharacterIds = [
  "character.armored_warrior", "character.silent_huntress", "character.defect", "character.watcher"
];
const characterCodes = {
  "character.armored_warrior": "IRONCLAD", "character.silent_huntress": "THE SILENT",
  "character.defect": "DEFECT", "character.watcher": "WATCHER",
  "character.lumine": "LUMINE", "character.yoirine": "YOIRINE", "character.suzuri": "SUZURI"
};
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
function localButton(label, handler, className = "") {
  const node = el("button", label, className);
  node.type = "button";
  node.dataset.uiAction = "true";
  node.disabled = busy || !ready;
  node.onclick = () => { if (!busy && ready) handler(); };
  return node;
}
function blockButton(node, blocked) {
  node.dataset.blocked = String(Boolean(blocked));
  node.disabled = busy || !ready || Boolean(blocked);
}
function actionDialog(title, description = "", closeLabel = "取消") {
  let dialog = $("action-dialog");
  if (!dialog) {
    dialog = el("dialog", undefined, "relic-dialog action-dialog");
    dialog.id = "action-dialog";
    dialog.setAttribute("aria-labelledby", "action-dialog-title");
    document.body.append(dialog);
  }
  const heading = el("div", undefined, "panel-heading");
  const name = el("h2", title); name.id = "action-dialog-title";
  const close = el("button", closeLabel); close.type = "button";
  close.onclick = () => dialog.close();
  heading.append(name, close);
  dialog.replaceChildren(heading);
  if (description) dialog.append(el("p", description, "action-description"));
  if (!dialog.open) dialog.showModal();
  return dialog;
}
function actionNode(choice) {
  const row = el("div", undefined, "action-row");
  const node = choice.options
    ? localButton("", () => {
        const dialog = actionDialog(choice.name, choice.description);
        const list = el("div", undefined, "choices");
        for (const item of choice.options) list.append(actionNode(item));
        if (!choice.options.length) list.append(el("p", "当前没有可选择的卡牌。", "hint"));
        dialog.append(list);
      }, "choice")
    : button("", choice.command, "choice");
  node.append(el("strong", choice.name));
  if (choice.description) node.append(el("span", choice.description, "action-description"));
  if (choice.reason) node.append(el("span", choice.reason, "action-reason"));
  blockButton(node, choice.disabled);
  row.append(node);
  if (choice.detailCommand) row.append(button("详情", choice.detailCommand, "action-detail"));
  return row;
}
function renderSelection(selection) {
  $("selection-panel").hidden = !selection;
  $("selection-options").replaceChildren();
  $("selection-submit").replaceChildren();
  if (!selection) return;
  $("selection-title").textContent = selection.title;
  $("selection-hint").textContent = selection.hint || "点击卡牌完成选择。";
  if (!selection.options.length && !selection.multiple) {
    $("selection-submit").append(localButton("打开指令操作", () => {
      $("advanced-commands").open = true;
      $("command").focus();
    }));
    return;
  }
  if (!selection.multiple) {
    for (const option of selection.options) $("selection-options").append(actionNode(option));
    return;
  }
  const selected = new Set();
  const minimum = selection.minimum || 0;
  const maximum = Math.min(selection.maximum ?? selection.options.length, selection.options.length);
  const quantity = minimum === maximum ? String(minimum) : `${minimum}–${maximum}`;
  $("selection-hint").textContent = [selection.hint, `选择 ${quantity} 张牌，再点击确认。`].filter(Boolean).join(" ");
  const submit = localButton("", () => {
    const indices = [...selected].map((i) => selection.options[i].command.split(" ").at(-1));
    send(selection.command + " " + (indices.join(",") || selection.emptyValue || "none"));
  }, "primary");
  const update = () => {
    submit.textContent = selected.size ? `确认选择（${selected.size} 张）` : minimum > 0 ? "请先选择卡牌" : "不选择，继续";
    blockButton(submit, selected.size < minimum || selected.size > maximum);
    [...$("selection-options").children].forEach((node, index) => {
      node.setAttribute("aria-pressed", String(selected.has(index)));
      blockButton(node, !selected.has(index) && selected.size >= maximum);
    });
  };
  selection.options.forEach((option, index) => {
    const node = localButton("", () => {
      if (selected.has(index)) selected.delete(index); else selected.add(index);
      update();
    }, "choice");
    node.append(el("strong", option.name), el("span", option.description, "action-description"));
    $("selection-options").append(node);
  });
  $("selection-submit").append(submit);
  update();
}
function showPotion(potion, index) {
  const dialog = actionDialog(potion.name, potion.description);
  const list = el("div", undefined, "choices");
  if (potion.target === "enemy") {
    dialog.append(el("p", "选择使用目标", "hint"));
    for (const enemy of state.run.enemies) {
      list.append(button("对 " + enemy.name + " 使用 · 生命 " + enemy.hp,
        `/card potion ${index} ${enemy.index}`, "choice"));
    }
  } else {
    list.append(button("使用药水", "/card potion " + index, "primary"));
  }
  dialog.append(list);
}
function setBusy(value) {
  busy = value;
  document.querySelectorAll("[data-command], [data-ui-action], #command-form button, #command, #new-run").forEach((node) => {
    node.disabled = value || !ready || node.dataset.blocked === "true";
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
  const original = originalCharacterIds.map((id) => characters.find((character) => character.character_id === id)).filter(Boolean);
  const custom = characters.filter((character) => !originalCharacterIds.includes(character.character_id));
  let position = 0;
  for (const [title, group, className] of [["原作角色", original, "original-characters"], ["私货角色", custom, "custom-characters"]]) {
    if (!group.length) continue;
    const section = el("section", undefined, "character-group " + className);
    const heading = el("h2", title, "character-group-title");
    heading.id = className + "-title";
    section.setAttribute("aria-labelledby", heading.id);
    const grid = el("div", undefined, "characters");
    for (const character of group) {
      const code = characterCodes[character.character_id] || "TRAVELER";
      const card = button("", "/card new " + character.index, "character character-" + character.index);
      const description = `最大生命 ${character.maxHp} · 初始金币 ${character.startingGold}`;
      card.append(el("span", String(++position).padStart(2, "0"), "character-number"), el("span", code, "eyebrow"),
        el("h2", character.name), el("p", description), el("span", "以此角色出发 →", "character-action"));
      grid.append(card);
    }
    section.append(heading, grid);
    $("characters").append(section);
  }
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
function renderCombatStatus(run) {
  const combat = run.combatStatus || { stance: "none", showStance: false, zone: null, orbCapacity: 0, orbs: [], focus: 0 };
  const panel = $("player-panel");
  panel.hidden = false;
  const vitals = [["hp", "生命", `${run.hp} / ${run.maxHp}`]];
  if (run.battle) vitals.push(["energy", "能量", `${run.energy} / ${run.maxEnergy}`], ["block", "格挡", run.block]);
  $("player-vitals").replaceChildren();
  for (const [key, label, value] of vitals) {
    const stat = el("div", undefined, "player-vital vital-" + key);
    stat.append(el("span", label), el("strong", String(value)));
    $("player-vitals").append(stat);
  }
  $("player-status").hidden = !run.battle;
  panel.dataset.stance = combat.stance;
  panel.dataset.zone = combat.zone?.element || "none";
  panel.dataset.extreme = String(Boolean(combat.zone?.extreme));
  $("player-status").textContent = run.status || "无状态";
  $("stance-badge").hidden = !combat.showStance;
  $("stance-badge").textContent = combat.stance === "none" ? "无姿态" : combat.stanceName;
  const zone = $("zone-badge");
  zone.hidden = !combat.zone;
  zone.textContent = combat.zone ? combat.zone.name + (combat.zone.extreme ? ` · 剩余 ${combat.zone.duration} 回合` : "") : "";
  zone.title = combat.zone?.description || "";
  zone.setAttribute("aria-haspopup", "dialog");
  zone.onclick = () => { if (combat.zone) actionDialog(combat.zone.name, combat.zone.description, "关闭"); };
  $("orb-panel").hidden = !combat.orbCapacity && !combat.focus;
  $("orb-label").textContent = `充能球 ${combat.orbs.length}/${combat.orbCapacity} · 集中 ${combat.focus >= 0 ? "+" : ""}${combat.focus} · 左侧优先激发`;
  const slots = $("orb-slots");
  slots.replaceChildren();
  const symbols = { lightning: "雷", frost: "霜", dark: "暗", glass: "璃", plasma: "离" };
  for (let index = 0; index < combat.orbCapacity; index++) {
    const orb = combat.orbs[index];
    const slot = orb
      ? localButton("", () => actionDialog(orb.name, orb.summary, "关闭"), "orb-slot")
      : el("div", undefined, "orb-slot orb-empty");
    slot.dataset.kind = orb?.kind || "empty";
    slot.setAttribute("aria-label", `球槽 ${index + 1}：` + (orb?.summary || "空槽"));
    if (orb) { slot.title = orb.summary; slot.setAttribute("aria-haspopup", "dialog"); }
    slot.append(el("span", orb ? symbols[orb.kind] || "球" : "+", "orb-sphere"));
    const text = el("span", undefined, "orb-text");
    text.append(el("strong", orb ? orb.name : "空球槽"));
    text.append(el("span", orb ? (orb.kind === "dark" ? `增长 ${orb.passive} · 积蓄 ${orb.value}` : `被动 ${orb.passive} · 激发 ${orb.evoke}`) : "等待生成", "orb-values"));
    slot.append(text);
    slots.append(slot);
  }
}
function render(data) {
  state = data;
  $("confirmation").hidden = !data.confirmation;
  renderCharacters(data.characters);
  const run = data.run;
  $("start").hidden = Boolean(run);
  $("game").hidden = !run;
  if (!run) { $("selection-panel").hidden = true; $("player-panel").hidden = true; return; }
  $("player-name").textContent = run.name;
  $("location").textContent = "旅途 / " + run.node;
  $("stats").replaceChildren();
  for (const [label, value] of [["金币", run.gold], ["牌库", run.deckCount]]) {
    const stat = el("div", undefined, "stat");
    stat.append(el("span", label), el("strong", String(value)));
    $("stats").append(stat);
  }
  $("arena-title").textContent = run.battle ? "选择你的目标" : run.node;
  $("turn-label").textContent = run.battle ? "第 " + run.turn + " 回合" : "继续攀登";
  renderCombatStatus(run);
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
    card.dataset.uiAction = "true";
    card.disabled = busy || !ready;
    card.onclick = () => {
      if (busy || !ready) return;
      target = enemy.index;
      document.querySelectorAll("#enemies .enemy").forEach((node, index) =>
        node.setAttribute("aria-pressed", String(run.enemies[index].index === target)));
      document.querySelectorAll("#hand [data-command]").forEach((node, index) => {
        node.dataset.command = "/card play " + run.hand[index].index + " " + target;
      });
    };
    $("enemies").append(card);
  }
  $("choices").replaceChildren();
  $("action-title").textContent = run.battle ? "" : (run.selection ? "请先完成下方选择" : (run.actionTitle || "可用操作"));
  for (const choice of [...run.choices, ...run.routes]) $("choices").append(actionNode(choice));
  renderSelection(run.selection);
  blockButton(document.querySelector('[data-command="/card end"]'), Boolean(run.selection));
  $("hand-count").textContent = String(run.hand.length);
  $("hand").replaceChildren();
  for (const card of run.hand) {
    const command = "/card play " + card.index + (target !== null ? " " + target : "");
    const node = button("", command, "playing-card type-" + card.type);
    node.title = card.summary;
    blockButton(node, Boolean(run.selection));
    node.append(el("span", String(card.cost), "card-cost"), el("span", ({attack:"攻击",skill:"技能",power:"能力",status:"状态",curse:"诅咒"})[card.type] || card.type, "card-type"),
      el("h3", card.name), el("p", card.description, "card-description"));
    if (card.preview) node.append(el("p", card.preview, "card-preview"));
    node.append(el("span", "#" + card.index + (run.selection ? " · 请先完成上方选择" : " · 点击出牌"), "card-index"));
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
  (run.potionDetails || []).forEach((potion, index) => {
    const item = localButton(potion.name, () => showPotion(potion, index));
    item.title = potion.description + (potion.usable ? "" : "（仅战斗中可用）");
    item.setAttribute("aria-haspopup", "dialog");
    blockButton(item, !potion.usable || Boolean(run.selection));
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
  $("action-dialog")?.close();
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
      if (data.result.run?.selection && /^\/card\s+play\b/.test(activeCommand)) {
        $("selection-title").focus({ preventScroll: true });
        $("selection-panel").scrollIntoView({ block: "nearest" });
      }
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
