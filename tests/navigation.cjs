const assert = require('node:assert/strict');
const fs = require('node:fs');
const {chromium} = require('C:/Users/Lenovo/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright');

(async () => {
  const browser = await chromium.launch({headless:true, executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
  try {
    const page = await browser.newPage();
    const navigations = [];
    await page.route('**/*', async route => {
      const request = route.request();
      if (request.isNavigationRequest()) navigations.push(request.url());
      await route.fulfill({contentType:request.isNavigationRequest() ? 'text/html' : 'application/json', body:request.isNavigationRequest() ? '<!doctype html><html><head></head><body>Demo page</body></html>' : '{}'});
    });
    await page.goto('https://demo.test/');
    await page.addScriptTag({content:fs.readFileSync('replica.js', 'utf8')});
    await page.evaluate(() => {
      const link = document.createElement('a');
      link.textContent = 'Dynamically loaded product';
      link.href = 'https://www.amarisjewels.com/products/imperial-taj-earcuffs?variant=123';
      document.body.append(link);
      const form = document.createElement('form');
      form.action = 'https://www.amarisjewels.com/search';
      document.body.append(form);
    });
    assert.equal(await page.locator('a').getAttribute('href'), 'https://demo.test/products/imperial-taj-earcuffs?variant=123');
    assert.equal(await page.locator('form').getAttribute('action'), 'https://demo.test/search');
    await page.evaluate(async () => {
      await fetch('https://www.amarisjewels.com/search/suggest?q=ring');
      await fetch(new Request('https://amarisjewels.com/collections/earrings?section_id=grid'));
    });
    await Promise.all([page.waitForURL('https://demo.test/products/imperial-taj-earcuffs?variant=123'), page.getByRole('link').click()]);
    assert(navigations.every(url => new URL(url).hostname === 'demo.test'));
    console.log('PASS: dynamic product links, search form, fetch URLs and page navigation stay on the demo host.');
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exit(1);});
