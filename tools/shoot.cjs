// Headless screenshots + checks: node tools/shoot.cjs <url> <outprefix>
const { chromium } = require("E:/tutorial/founderdada/node_modules/playwright");
(async () => {
  const [url, out] = process.argv.slice(2);
  const browser = await chromium.launch();
  for (const [name, vp] of [["desktop", { width: 1440, height: 900 }], ["mobile", { width: 390, height: 844, isMobile: true, deviceScaleFactor: 2 }]]) {
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: vp.deviceScaleFactor || 1, isMobile: !!vp.isMobile, colorScheme: "dark" });
    const page = await ctx.newPage();
    const errors = [];
    page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
    page.on("pageerror", (e) => errors.push(String(e)));
    await page.goto(url, { waitUntil: "networkidle" });
    await page.waitForTimeout(2800);
    const info = await page.evaluate(() => ({
      scrollW: document.documentElement.scrollWidth, innerW: innerWidth,
      fonts: [...document.fonts].map((f) => f.family + ":" + f.style + ":" + f.status).join(","),
      overflow: [...document.querySelectorAll("body *")].filter((e) => e.getBoundingClientRect().right > innerWidth + 1 && !e.closest(".ba,.tablist,.panel,.d-reflow")).slice(0, 8).map((e) => e.tagName + "." + e.className),
      height: document.documentElement.scrollHeight,
    }));
    console.log(name, JSON.stringify(info), "errors:", errors.slice(0, 5));
    await page.screenshot({ path: `${out}-${name}-top.png` });
    await page.screenshot({ path: `${out}-${name}-full.png`, fullPage: true });
    await ctx.close();
  }
  await browser.close();
})();
