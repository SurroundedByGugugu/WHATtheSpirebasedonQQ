// node web/bugfix_browser_check.cjs <playwright module path>
const { chromium } = require(process.argv[2] || 'playwright');
const path = require('node:path');
const assert = require('node:assert/strict');
const fixtures = process.argv[3] ? require(path.resolve(process.argv[3])) : null;

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(fixtures => {
      if (fixtures) {
        window.Worker = class extends EventTarget {
          constructor() { super(); window.testWorker = this; this.setups = 0; }
          postMessage(message) {
            const key = message.type === 'init' ? 'initial'
              : message.type === 'setup' ? (++this.setups === 1 ? 'reward' : 'combat')
              : message.command.startsWith('/card new') ? 'new'
              : ({'/card reward back': 'back', '/card take 0': 'reward', '/card pick 2': 'picked'})[message.command];
            if (!key) throw new Error('Unexpected fixture command: ' + message.command);
            setTimeout(() => {
              const event = new MessageEvent('message', { data: { type: 'result', id: message.id, result: fixtures[key] } });
              this.onmessage?.(event);
              this.dispatchEvent(event);
            }, 0);
          }
        };
        return;
      }
      const OriginalWorker = window.Worker;
      window.Worker = class extends OriginalWorker {
        constructor(...args) { super(...args); window.testWorker = this; }
      };
    }, fixtures);
    await page.route('**/worker*.js', async route => {
      const response = await route.fetch();
      const body = (await response.text()).replace('const result = data.type === "init"',
        'if (data.type === "setup") runtime.runPython(data.python); const result = data.type === "init"');
      await route.fulfill({ response, body });
    });
    await page.goto('http://127.0.0.1:8766/');
    await page.locator('#characters button').first().waitFor({ timeout: 145000 });
    await page.locator('#characters button').first().click();
    await page.locator('#game:not([hidden])').waitFor();
    async function setup(python) {
      await page.evaluate(python => new Promise(resolve => {
        const listener = event => {
          if (event.data.id === 9000) { window.testWorker.removeEventListener('message', listener); resolve(); }
        };
        window.testWorker.addEventListener('message', listener);
        window.testWorker.postMessage({ type: 'setup', id: 9000, python, command: '/card view' });
      }), python);
    }
    async function clickCommand(command) {
      await page.locator(`[data-command="${command}"]`).click();
      await page.waitForFunction(() => !document.getElementById('command').disabled);
    }
    await setup(`
from web_bridge import service, SESSION
from data.card.AAAregistry import create_card
from game.reward import RewardState, RewardOption
run = service.get_run(SESSION)
run.pending_ancient = None
cards = [create_card('card.strike_yoirine') for _ in range(3)]
for card, rarity in zip(cards, ['common', 'uncommon', 'rare']):
    card.quantity = rarity
run.pending_reward = RewardState(options=[RewardOption('card', '选择一张卡牌', {'cards': cards})], active_card_option_index=0)
`);
    for (const rarity of ['common', 'uncommon', 'rare']) {
      assert.equal(await page.locator(`#choices .rarity-${rarity}`).count(), 1);
    }
    await clickCommand('/card reward back');
    assert.equal(await page.locator('[data-command="/card take 0"]').count(), 1);
    await clickCommand('/card take 0');
    await clickCommand('/card pick 2');
    await page.getByRole('heading', { name: '获得奖励', exact: true }).waitFor();
    assert.equal(await page.locator('#action-dialog .rarity-rare').count(), 1);
    await page.getByRole('button', { name: '继续', exact: true }).click();
    await setup(`
from data.relic.AAAregistry import create_relic
from game.engine import start_battle_with_player
from game.player_state import PlayerState
create_relic('relic.whirlwall_sparrow_down').on_obtained(run)
special = run.master_deck[-1]
player = PlayerState(run.character_id, run.character_name, 100, 100, 3, 3)
player.draw_pile = [create_card('card.strike_yoirine') for _ in range(8)]
battle, _ = start_battle_with_player(SESSION, run.character_id, player, ['enemy.bronze_orb'])
battle.player.hand = [special]
battle.enemies[0]._captured_card = special
run.current_battle = battle
`);
    assert.ok((await page.locator('#hand .keyword-tag').allTextContents()).includes('保留'));
    assert.match(await page.locator('#enemies .captured-card').textContent(), /磐愿/);
    await page.screenshot({ path: path.join(__dirname, '.test-runtime/bugfix-desktop.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    assert.equal(overflow, false);
    await page.screenshot({ path: path.join(__dirname, '.test-runtime/bugfix-mobile.png'), fullPage: true });
    assert.deepEqual(errors, []);
    console.log('PASS (' + (fixtures ? 'engine snapshot fixtures' : 'live Pyodide') + '): rarity, reward back/reopen, acquired dialog, retain badge, stolen card, desktop/mobile layout.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
