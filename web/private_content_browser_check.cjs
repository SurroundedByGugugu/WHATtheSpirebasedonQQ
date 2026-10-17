// Uses real Python responses with an offline Worker to exercise the setup UI.
const { chromium } = require(process.argv[2] || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const assert = require('node:assert/strict');
(async () => {
  const responses = JSON.parse(execFileSync('python', ['-B', '-c', `
import json
from web.bridge import dispatch
commands = ['', '/card private off', '/card private on', '/card new 0']
print(json.dumps({cmd: json.loads(dispatch(cmd)) for cmd in commands}))
`], { cwd: path.join(__dirname, '..'), encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }));
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('http://spire.test/**', route => {
      const name = new URL(route.request().url()).pathname.slice(1) || 'index.html';
      return route.fulfill({ body: fs.readFileSync(path.join(__dirname, name)),
        contentType: { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css' }[path.extname(name)] });
    });
    await page.addInitScript(data => {
      window.Worker = class {
        postMessage(message) {
          setTimeout(() => this.onmessage({ data: { type: 'result', result: data[message.command || ''] } }), 0);
        }
      };
    }, responses);
    await page.goto('http://spire.test/');
    await page.locator('#characters button').first().waitFor();
    assert.equal(await page.locator('#characters button').count(), 8);
    assert.match(await page.locator('#characters').innerText(), /昼·里辛塔法【已停工】/);
    assert.match(await page.locator('#characters').innerText(), /Suzuri【施工中】/i);
    await page.locator('#private-content').selectOption('off');
    await page.waitForFunction(() => document.querySelectorAll('#characters button').length === 4);
    assert.equal(await page.locator('.custom-characters').count(), 0);
    assert.equal(await page.locator('#private-content').inputValue(), 'off');
    await page.locator('#private-content').selectOption('on');
    await page.waitForFunction(() => document.querySelectorAll('#characters button').length === 8);
    await page.locator('.original-characters button').first().click();
    await page.locator('#game:not([hidden])').waitFor();
    await page.locator('#new-run').click();
    assert.equal(await page.locator('#private-content').isDisabled(), true);
    assert.match(await page.locator('#private-content-hint').innerText(), /已固定/);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    assert.deepEqual(errors, []);
    console.log('PASS: private toggle, original-only selection, status labels, run lock and mobile layout.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
