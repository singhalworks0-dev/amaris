const assert = require('node:assert/strict');
const {chromium} = require('C:/Users/Lenovo/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright');

(async () => {
  const base = process.argv[2] || 'https://amaris-gold.vercel.app';
  const host = new URL(base).hostname;
  const browser = await chromium.launch({headless:true, executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const navigations = [];
    page.on('request', request => {if (request.isNavigationRequest() && request.frame() === page.mainFrame()) navigations.push(request.url());});
    let response = await page.goto(base, {waitUntil:'domcontentloaded', timeout:120000});
    assert.equal(response.status(), 200);
    await page.waitForTimeout(5000);
    await page.getByRole('link', {name:'CATEGORIES', exact:true}).first().hover();
    const earrings = page.getByRole('link', {name:'EARRINGS', exact:true}).filter({visible:true}).first();
    await Promise.all([page.waitForURL('**/collections/earrings', {timeout:120000}), earrings.click()]);
    assert.equal(new URL(page.url()).hostname, host);
    await page.waitForTimeout(3000);
    const product = page.locator('a[href*="/products/"]').filter({visible:true}).first();
    const productUrl = await product.getAttribute('href');
    await Promise.all([page.waitForURL(url => url.pathname.includes('/products/'), {timeout:120000}), product.click()]);
    assert.equal(new URL(page.url()).hostname, host);
    await page.waitForTimeout(3000);
    const escaped = await page.locator('a[href]').evaluateAll(xs => xs.filter(x => /(^|\.)amarisjewels\.com$/.test(x.hostname)).map(x => x.href));
    assert.deepEqual(escaped, []);
    assert(navigations.every(url => new URL(url).hostname === host));
    await page.screenshot({path:'preview-vercel-product.png'});
    console.log(JSON.stringify({homepage:200,collection:new URL('/collections/earrings',base).href,product:page.url(),productLink:productUrl,originalStoreLinks:escaped.length,navigations}, null, 2));
  } finally {await browser.close();}
})().catch(error => {console.error(error);process.exit(1);});
