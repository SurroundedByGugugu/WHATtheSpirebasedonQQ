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
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("requestfailed", (request) => console.log("Request failed:", request.url(), request.failure()?.errorText));
    await page.goto(pathToFileURL(path.join(__dirname, "dist/index.html")).href);
    await page.getByText("不能直接双击 HTML", { exact: false }).waitFor();
    console.log("PASS: file:// displays HTTP launch instructions.");
    await page.goto("http://127.0.0.1:8765/");
    await page.locator("#characters button").first().waitFor({ timeout: 145000 });
    console.log("PASS: Pyodide and engine loaded; five characters:", await page.locator("#characters button").count());
    await page.locator("#characters button").first().click();
    await page.locator("#game:not([hidden])").waitFor();
    await page.locator("#choices button").first().waitFor();
    console.log("PASS: new run and opening choices.");
    async function command(text) {
      await page.locator("#command").fill(text);
      await page.locator("#command-form button").click();
      await page.waitForFunction(() => !document.getElementById("command").disabled);
      if (await page.locator("#error").isVisible()) throw new Error(await page.locator("#error").innerText());
    }
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
    const output = path.join(__dirname, ".test-runtime");
    fs.mkdirSync(output, { recursive: true });
    await page.screenshot({ path: path.join(output, "desktop.png"), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) throw new Error("Mobile page overflows horizontally.");
    await page.screenshot({ path: path.join(output, "mobile.png"), fullPage: true });
    console.log("PASS: mobile width has no horizontal overflow.");
    const broken = await context.newPage();
    await broken.route("**/app.js", (route) => route.abort());
    await broken.goto("http://127.0.0.1:8765/");
    await broken.getByText("网页启动脚本加载失败", { exact: false }).waitFor();
    console.log("PASS: missing script displays actionable error.");
    if (errors.length) throw new Error(errors.join("\n"));
    console.log("All browser checks passed.");
  } finally { await browser.close(); }
})().catch((error) => { console.error(error); process.exitCode = 1; });
