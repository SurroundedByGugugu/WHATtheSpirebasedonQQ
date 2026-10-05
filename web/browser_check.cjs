// Usage: node web/browser_check.cjs <absolute path to installed playwright module>
const { chromium } = require(process.argv[2] || "playwright");
const path = require("node:path");
const fs = require("node:fs");
const { pathToFileURL } = require("node:url");
(async () => {
  const browser = await chromium.launch({ channel: "msedge", headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await context.newPage();
    const output = path.join(__dirname, ".test-runtime");
    fs.mkdirSync(output, { recursive: true });
    // Expose only the test worker, and inject fixture setup in the test response.
    // Production assets retain their normal command-only protocol.
    await page.addInitScript(() => {
      const OriginalWorker = window.Worker;
      window.Worker = class extends OriginalWorker {
        constructor(...args) { super(...args); window.testWorker = this; }
      };
    });
    await page.route("**/worker*.js", async (route) => {
      const response = await route.fetch();
      const source = (await response.text()).replace(
        'const result = data.type === "init"',
        'if (data.type === "setup") runtime.runPython(data.python); const result = data.type === "init"');
      await route.fulfill({ response, body: source });
    });
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("requestfailed", (request) => console.log("Request failed:", request.url(), request.failure()?.errorText));
    await page.goto(pathToFileURL(path.join(__dirname, "dist/index.html")).href);
    await page.getByText("不能直接双击 HTML", { exact: false }).waitFor();
    console.log("PASS: file:// displays HTTP launch instructions.");
    await page.goto("http://127.0.0.1:8765/");
    await page.locator("#characters button").first().waitFor({ timeout: 145000 });
    console.log("PASS: Pyodide and engine loaded; characters:", await page.locator("#characters button").count());
    await page.locator("#characters button").first().click();
    await page.locator("#game:not([hidden])").waitFor();
    await page.locator("#choices button").first().waitFor();
    console.log("PASS: new run and opening choices.");
    async function command(text) {
      await page.locator("#advanced-commands").evaluate((node) => node.open = true);
      await page.locator("#command").fill(text);
      await page.locator("#command-form button").click();
      await page.waitForFunction(() => !document.getElementById("command").disabled);
      if (await page.locator("#error").isVisible()) throw new Error(await page.locator("#error").innerText());
    }
    async function settled() {
      await page.waitForFunction(() => !document.getElementById("command").disabled);
      if (await page.locator("#error").isVisible()) throw new Error(await page.locator("#error").innerText());
    }
    async function setup(python) {
      await page.evaluate((python) => {
        document.getElementById("command").disabled = true;
        window.testWorker.postMessage({ type: "setup", python, command: "" });
      }, python);
      await settled();
    }
    await setup(`from web_bridge import service, SESSION
from data.card.AAAregistry import create_card
from data.card.upgrade_rules import upgrade_card
from game.reward import RewardState, RewardOption
from game.node.node_rest import create_rest_state
from game.node.node_shop import ShopState, ShopItem
run = service.get_run(SESSION)
run.clear_pending_nodes()
run.pending_reward = RewardState(options=[RewardOption("gold", "25 金币", {"amount": 25}), RewardOption("card", "选择奖励卡牌", {"cards": [create_card("card.strike"), create_card("card.defend")]})])`);
    if (await page.locator("#advanced-commands").getAttribute("open") !== null) throw new Error("Manual commands should start collapsed.");
    await page.locator('#choices [data-command="/card take 0"]').click();
    await settled();
    await page.locator('#choices [data-command="/card take 1"]').click();
    await settled();
    await page.locator('#choices [data-command="/card pick 1"]').click();
    await settled();
    if (await page.locator('#choices [data-command^="/card pick"]').count()) throw new Error("Reward card buttons did not clear.");
    await setup(`run.clear_pending_nodes()
run.pending_shop = ShopState(items=[ShopItem("card", "打击", 20, {"card": create_card("card.strike")}), ShopItem("card", "昂贵商品", 9999, {"card": create_card("card.defend")})])`);
    await page.screenshot({ path: path.join(output, "shop-desktop.png"), fullPage: true });
    await page.locator('#choices [data-command="/card buy 0"]').click();
    await settled();
    if (!(await page.locator('#choices [data-command="/card buy 0"]').isDisabled())) throw new Error("Sold item remained enabled.");
    if (!(await page.locator('#choices [data-command="/card buy 1"]').isDisabled())) throw new Error("Unaffordable item enabled.");
    await page.locator('#choices [data-command="/card item 1"]').click();
    await settled();
    if (!(await page.locator('#choices [data-command="/card buy 1"]').isDisabled())) throw new Error("Busy reset reenabled unavailable item.");
    await page.locator("#choices button").filter({ hasText: "定向删牌" }).click();
    await page.locator('#action-dialog [data-command="/card remove 0"]').click();
    await settled();
    if (await page.locator("#action-dialog").isVisible()) throw new Error("Action dialog stayed open after submission.");
    await setup(`run.clear_pending_nodes()
run.pending_rest = create_rest_state()
run.master_deck = [upgrade_card(create_card("card.strike")), create_card("card.defend")]`);
    await page.locator("#choices button").filter({ hasText: "锻造" }).click();
    await page.setViewportSize({ width: 390, height: 844 });
    if (await page.locator("#action-dialog").evaluate((node) => node.scrollWidth > node.clientWidth)) throw new Error("Mobile selection dialog overflows.");
    await page.screenshot({ path: path.join(output, "smith-mobile.png") });
    await page.locator('#action-dialog [data-command="/card smith 0"]').click();
    await page.setViewportSize({ width: 1440, height: 1000 });
    await settled();
    if (!(await page.locator("#log").innerText()).includes("锻造完成")) throw new Error("Smith action failed.");
    console.log("PASS: reward, shop, removal and smith flows use buttons only.");
    await command("/card testroom battle");
    await page.locator("#hand button").first().waitFor();
    await command("/ctrl addcard 打击 手牌");
    const before = await page.locator("#hand button").count();
    await page.locator("#hand button").last().click();
    await page.waitForFunction(() => !document.getElementById("command").disabled);
    if (await page.locator("#hand button").count() !== before - 1) throw new Error("Card click did not play the card.");
    await page.locator('[data-command="/card end"]').click();
    await page.waitForFunction(() => document.getElementById("turn-label").textContent.includes("2"));
    console.log("PASS: card click, target selection and end turn.");
    const potionCount = await page.locator("#potions button").count();
    await page.locator("#potions button").nth(1).click();
    await page.locator('#action-dialog [data-command="/card potion 1 1"]').click();
    await settled();
    if (await page.locator("#potions button").count() !== potionCount - 1) throw new Error("Potion was not consumed.");
    await setup(`battle = run.current_battle
battle.pending_discard_selection = True
battle.pending_discard_min_count = 1
battle.pending_discard_max_count = 2`);
    if (!(await page.locator('#selection-submit button').isDisabled())) throw new Error("Required selection can submit empty.");
    if (!(await page.locator('[data-command="/card end"]').isDisabled())) throw new Error("End turn enabled during selection.");
    await page.locator('#selection-options button').nth(0).click();
    await page.locator('#selection-options button').nth(1).click();
    await page.locator('#enemies button').first().click();
    if (await page.locator('#selection-options [aria-pressed="true"]').count() !== 2) throw new Error("Target change lost selected cards.");
    await page.screenshot({ path: path.join(output, "selection-desktop.png"), fullPage: true });
    await page.locator('#selection-submit button').click();
    await settled();
    if (await page.locator('#selection-panel').isVisible()) throw new Error("Discard selection did not complete.");
    console.log("PASS: targeted potion and multi-card discard without typing.");
    await setup(`from game.stances import change_stance
from game.orbs import channel, set_slots
from data.zones.element_zones import ElementZone
battle = run.current_battle
battle.player.character_id = "character.watcher"
change_stance(battle, "calm")
battle.active_zone = ElementZone("water")
channel(battle, battle.player, "frost")`);
    if (await page.locator('#player-panel .orb-slot').count() !== 1) throw new Error("First orb did not receive one slot.");
    if (await page.locator('.arena #player-status').count()) throw new Error("Player statuses still in enemy panel.");
    const positions = await page.evaluate(() => ['.arena', '#player-panel', '#hand-panel'].map(s => document.querySelector(s).getBoundingClientRect().top));
    if (!(positions[0] < positions[1] && positions[1] < positions[2])) throw new Error("Combat strip is in the wrong position.");
    const backgrounds = [];
    for (const stance of ["calm", "wrath", "divinity"]) {
      await setup(`change_stance(battle, "${stance}")`);
      if (await page.locator('#player-panel').getAttribute('data-stance') !== stance) throw new Error("Stance not refreshed.");
      backgrounds.push(await page.locator('#player-panel').evaluate(node => getComputedStyle(node).backgroundColor));
    }
    if (new Set(backgrounds).size !== 3) throw new Error("Stances must have distinct background colors.");
    const normalBorder = await page.locator('#player-panel').evaluate(node => getComputedStyle(node).getPropertyValue('--zone-saturation'));
    await setup(`battle.active_zone = ElementZone("water", True, 3)
set_slots(battle.player, 3)`);
    const extremeBorder = await page.locator('#player-panel').evaluate(node => getComputedStyle(node).getPropertyValue('--zone-saturation'));
    if (parseFloat(extremeBorder) <= parseFloat(normalBorder)) throw new Error("Extreme Zone saturation did not increase.");
    if (await page.locator('#orb-slots .orb-empty').count() !== 2) throw new Error("Missing empty slots.");
    await page.locator('#orb-slots button').first().click();
    if (!(await page.locator('#action-dialog').innerText()).includes('再生')) throw new Error("Orb details missing Zone synergy.");
    await page.locator('#action-dialog button').filter({ hasText: '关闭' }).click();
    await page.locator('#zone-badge').click();
    await page.locator('#action-dialog button').filter({ hasText: '关闭' }).click();
    await page.screenshot({ path: path.join(output, "combat-strip-desktop.png"), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.locator('#player-panel').scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(output, "combat-strip-mobile.png") });
    await setup(`set_slots(battle.player, 100)`);
    if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) throw new Error("Many orb slots overflow the page.");
    await setup(`set_slots(battle.player, 3)
battle.active_zone = None
change_stance(battle, "none")`);
    if (await page.locator('#zone-badge').isVisible()) throw new Error("Expired Zone badge stayed visible.");
    if (await page.locator('#player-panel').getAttribute('data-extreme') !== 'false') throw new Error("Extreme color not cleared.");
    await page.setViewportSize({ width: 1440, height: 1000 });
    console.log("PASS: player strip position, stances, orb slots, Zone colors, details and mobile overflow.");
    await page.locator("#advanced-commands").evaluate((node) => node.open = false);
    await page.screenshot({ path: path.join(output, "desktop.png"), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) throw new Error("Mobile page overflows horizontally.");
    await page.screenshot({ path: path.join(output, "mobile.png"), fullPage: true });
    console.log("PASS: mobile width has no horizontal overflow.");
    async function playFollowup(cardId, extra = "") {
      await setup(`battle.pending_choice = None
battle.pending_choice_queue = []
battle.active_zone = None
battle.player.relics = []
battle.player.statuses.values.clear()
battle.player.cost = 10
battle.player.hand = [create_card("${cardId}"), create_card("card.defend"), create_card("card.strike")]
battle.player.draw_pile = [create_card("card.strike"), create_card("card.strike")]
battle.player.discard_pile = [create_card("card.strike")]
${extra}`);
      await page.locator('#hand button').first().click();
      await settled();
      if (!(await page.locator('#selection-panel').isVisible())) throw new Error("Missing follow-up selection panel.");
      if (!(await page.locator('[data-command="/card end"]').isDisabled())) throw new Error("End turn enabled during follow-up.");
    }
    await playFollowup("card.crystal_plating", 'battle.player.hand[1].attack_element = "fire"');
    if (await page.locator('#selection-options button').count() !== 1) throw new Error("Plating included ineligible cards.");
    if (await page.locator('#selection-title').evaluate(node => document.activeElement !== node)) throw new Error("Selection panel was not focused after play.");
    await page.screenshot({ path: path.join(output, "plating-mobile.png") });
    await page.locator('#selection-options [data-command="/card plate 0"]').click();
    await settled();
    if (!(await page.locator('#hand').innerText()).includes('打击·晶')) throw new Error("Plating button did not modify its target.");
    if (await page.locator('#selection-panel').isVisible()) throw new Error("Completed selection still displayed.");
    await playFollowup("card.synchronization");
    await page.locator('#selection-options button').filter({ hasText: '弃牌堆' }).click();
    await settled();
    if (await page.locator('#selection-panel').isVisible()) throw new Error("Sync selection failed.");
    await playFollowup("card.abyss_index");
    await page.locator('#selection-options button').nth(1).click();
    await settled();
    if (await page.locator('#selection-panel').isVisible()) throw new Error("Abyss index selection failed.");
    await playFollowup("card.radiant_crystal_reflection", 'battle.player.hand[0].replay_extra = 1');
    if (!(await page.locator('#selection-submit button').isDisabled())) throw new Error("Reflection allowed empty selection.");
    await page.locator('#selection-options button').filter({ hasText: '手牌' }).first().click();
    await page.locator('#selection-options button').filter({ hasText: '弃牌堆' }).click();
    if (!(await page.locator('#selection-options button').filter({ hasText: '抽牌堆' }).first().isDisabled())) throw new Error("Reflection exceeded max selections.");
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.locator('#selection-panel').scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(output, "reflection-desktop.png") });
    await page.locator('#selection-submit button').click();
    await settled();
    if (await page.locator('#selection-panel').isVisible()) throw new Error("Reflection selection failed.");
    await playFollowup("card.fossil");
    await page.locator('#selection-submit button').click();
    await settled();
    if (await page.locator('#selection-panel').isVisible()) throw new Error("Fossil skip failed.");
    await playFollowup("card.fossil");
    await page.locator('#selection-options button').first().click();
    await page.locator('#selection-options button').nth(1).click();
    await page.locator('#selection-submit button').click();
    await settled();
    if (await page.locator('#hand button').count() !== 0) throw new Error("Fossil did not consume selected cards.");
    if (!(await page.locator('#player-status').innerText()).includes('岩层')) throw new Error("Fossil rock layers missing.");
    if (await page.locator('#advanced-commands').getAttribute('open') !== null) throw new Error("Follow-up actions required manual commands.");
    console.log("PASS: plating, sync, abyss index, reflection and fossil follow-up buttons.");
    const broken = await context.newPage();
    await broken.route("**/app*.js", (route) => route.abort());
    await broken.goto("http://127.0.0.1:8765/");
    await broken.getByText("网页启动脚本加载失败", { exact: false }).waitFor();
    console.log("PASS: missing script displays actionable error.");
    if (errors.length) throw new Error(errors.join("\n"));
    console.log("All browser checks passed.");
  } finally { await browser.close(); }
})().catch((error) => { console.error(error); process.exitCode = 1; });
