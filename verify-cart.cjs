const {chromium}=require('C:/Users/Lenovo/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs=require('node:fs');
(async()=>{
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});const page=await browser.newPage({viewport:{width:1440,height:1000}});
await page.goto('http://localhost:4173/products/imperial-taj-earcuffs',{waitUntil:'domcontentloaded',timeout:90000});await page.waitForTimeout(3000);
await page.locator('[data-add-to-cart]').first().click();await page.waitForTimeout(1500);
const added=await page.evaluate(()=>JSON.parse(localStorage.getItem('amaris-preview-cart')||'[]'));
if(added.length!==1)throw new Error('Add to cart failed');
await page.screenshot({path:'preview-cart.png'});
const quantity=page.getByRole('spinbutton',{name:'Quantity for Imperial Taj Earcuffs'});await quantity.fill('2');await quantity.dispatchEvent('change');
const updated=await page.evaluate(()=>JSON.parse(localStorage.getItem('amaris-preview-cart'))[0].quantity);if(updated!==2)throw new Error('Quantity update failed');
await page.reload({waitUntil:'domcontentloaded'});await page.waitForTimeout(2000);
await page.locator('[data-cart-drawer-toggle]').filter({visible:true}).first().click();
await page.getByRole('button',{name:'Remove',exact:true}).click();
const removed=await page.evaluate(()=>JSON.parse(localStorage.getItem('amaris-preview-cart')).length);if(removed!==0)throw new Error('Removal failed');
const result={add:true,quantity:true,persistence:true,remove:true};fs.writeFileSync('cart-verification.json',JSON.stringify(result,null,2));console.log(result);await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
