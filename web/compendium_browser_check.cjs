// UI smoke test using real Python catalog data and a fixture Worker (no CDN required).
// node web/compendium_browser_check.cjs <path to playwright>
const { chromium } = require(process.argv[2] || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const assert = require('node:assert/strict');
(async () => {
  const fixture = JSON.parse(execFileSync('python', ['-B', '-c',
    'from web.bridge import dispatch; print(dispatch())'], { cwd: path.join(__dirname, '..'), encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }));
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('http://spire.test/**', route => {
      const name = new URL(route.request().url()).pathname.slice(1) || 'index.html';
      const extension = path.extname(name);
      return route.fulfill({ body: fs.readFileSync(path.join(__dirname, name)), contentType: { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css' }[extension] });
    });
    await page.addInitScript(data => {
      window.Worker = class {
        postMessage() { setTimeout(() => this.onmessage({ data: { type: 'result', result: data } }), 0); }
        terminate() {}
      };
    }, fixture);
    await page.goto('http://spire.test/');
    await page.locator('#characters button').first().waitFor();
    const columns = await page.locator('.custom-characters .characters').evaluate(node => getComputedStyle(node).gridTemplateColumns.split(' ').length);
    assert.equal(columns, 4);
    await page.locator('#open-compendium').click();
    assert.equal(await page.locator('.catalog-entry').count(), 24);
    await page.locator('#catalog-next').click();
    assert.match(await page.locator('#catalog-page').innerText(), /^2 /);
    await page.locator('#catalog-search').fill('card.strike');
    assert.match(await page.locator('#catalog-page').innerText(), /^1 /);
    await page.locator('.catalog-entry').first().click();
    assert.match(await page.locator('#action-dialog').innerText(), /小故事/);
    assert.match(await page.locator('#action-dialog').innerText(), /升级后/);
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#compendium-dialog').evaluate(node => node.open), true);
    await page.locator('#catalog-search').fill('no-such-card-xyz');
    assert.equal(await page.locator('.catalog-entry').count(), 0);
    await page.locator('#catalog-search').fill('');
    await page.locator('#catalog-owner').selectOption('character.yoirine');
    assert.ok(await page.locator('.catalog-entry').count() > 0);
    await page.locator('#catalog-rarity').selectOption('rare');
    await page.locator('#catalog-search').fill('残留搜索');
    await page.locator('#catalog-kind').selectOption('relics');
    assert.equal(await page.locator('#catalog-owner').inputValue(), '*');
    assert.equal(await page.locator('#catalog-rarity').inputValue(), '*');
    assert.equal(await page.locator('#catalog-search').inputValue(), '');
    for (const name of ['豆包', '蚂蚁阿福', 'Claude', 'GPT', 'Gemini', 'Deepseek']) {
      await page.locator('#catalog-search').fill(name);
      await page.locator('.catalog-entry').filter({ has: page.getByText(name, { exact: true }) }).click();
      assert.match(await page.locator('#action-dialog').innerText(), /软件商店/);
      await page.keyboard.press('Escape');
    }
    await page.locator('#catalog-search').fill('AI');
    for (const name of ['豆包', '蚂蚁阿福', 'Claude', 'GPT', 'Gemini', 'Deepseek']) {
      assert.equal(await page.locator('.catalog-entry strong').getByText(name, { exact: true }).count(), 1);
    }
    await page.locator('#catalog-owner').selectOption('character.yoirine');
    assert.equal(await page.locator('.catalog-entry').count(), 0);
    await page.locator('#catalog-reset').click();
    assert.equal(await page.locator('#catalog-search').inputValue(), '');
    await page.locator('#catalog-owner').selectOption('*');
    await page.locator('#catalog-rarity').selectOption('rare');
    assert.ok(await page.locator('.catalog-entry').count() > 0);
    await page.locator('#catalog-rarity').selectOption('*');
    await page.locator('#catalog-search').fill('relic.burning_blood');
    await page.locator('.catalog-entry').click();
    assert.match(await page.locator('#action-dialog').innerText(), /遗物|小故事/);
    await page.keyboard.press('Escape');
    await page.locator('#catalog-search').fill('');
    await page.locator('#catalog-kind').selectOption('fields');
    for (const element of ['火', '地', '风', '水', '雷', '阴', '晶']) {
      for (const prefix of ['', '极']) {
        const name = prefix + element + 'Zone';
        await page.locator('#catalog-search').fill(name);
        await page.locator('.catalog-entry').filter({ has: page.getByText(name, { exact: true }) }).click();
        assert.match(await page.locator('#action-dialog').innerText(), /同属性牌|覆盖/);
        await page.keyboard.press('Escape');
      }
    }
    await page.locator('#catalog-reset').click();
    for (const [kind, search] of [['monsters', '第一勇士'], ['effects', '锚定'], ['fields', '极·星']]) {
      await page.locator('#catalog-kind').selectOption(kind);
      await page.locator('#catalog-search').fill(search);
      assert.ok(await page.locator('.catalog-entry').count() > 0);
      await page.locator('.catalog-entry').first().click();
      assert.match(await page.locator('#action-dialog').innerText(), /效果说明/);
      await page.keyboard.press('Escape');
      await page.locator('#catalog-search').fill('');
    }
    fs.mkdirSync(path.join(__dirname, '.test-runtime'), { recursive: true });
    await page.screenshot({ path: path.join(__dirname, '.test-runtime/compendium-desktop.png') });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(__dirname, '.test-runtime/compendium-mobile.png') });
    assert.equal(await page.locator('#compendium-dialog').evaluate(node => node.scrollWidth <= node.clientWidth), true);
    await page.locator('#close-compendium').click();
    assert.equal(await page.locator('.custom-characters .characters').evaluate(node => getComputedStyle(node).gridTemplateColumns.split(' ').length), 2);
    assert.deepEqual(errors, []);
    console.log('PASS: catalog search, filters, pagination, upgrades, nested dialogs, desktop and mobile layouts.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
