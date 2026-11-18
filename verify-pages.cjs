const { chromium } = require('C:/Users/Lenovo/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright');
const fs = require('node:fs');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const results=[];
 for(const [slug,path] of [['home','/'],['collection','/collections/earrings'],['product','/products/imperial-taj-earcuffs'],['story','/pages/our-story'],['boutiques','/pages/our-boutiques']]){
  try {
   const response=await page.goto('http://localhost:4173'+path,{waitUntil:'domcontentloaded',timeout:90000});
   await page.waitForTimeout(7000);
   await page.screenshot({path:`preview-${slug}.png`});
   results.push({page:slug,status:response.status(),title:await page.title(),horizontalOverflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),heading:await page.locator('h1').allTextContents()});
   if(slug==='home'){
    for(const name of ['CATEGORIES','COLLECTIONS','READY TO SHIP','CAMPAIGNS']){
     const link=page.getByRole('link',{name,exact:true}).first();
     await link.hover(); await page.waitForTimeout(400);
     await page.screenshot({path:`preview-menu-${name.toLowerCase().replaceAll(' ','-')}.png`});
    }
    await page.setViewportSize({width:390,height:844});
    await page.mouse.move(380,800); await page.waitForTimeout(1500);
    await page.screenshot({path:'preview-mobile.png'});
    results.push({page:'mobile-home',horizontalOverflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),buttons:await page.locator('button').evaluateAll(xs=>xs.filter(x=>x.getBoundingClientRect().width>0).slice(0,8).map(x=>({label:x.getAttribute('aria-label'),text:x.textContent.trim().slice(0,50)})))});
    await page.setViewportSize({width:1440,height:1000});
   }
  }catch(e){results.push({page:slug,error:e.message})}
 }
 fs.writeFileSync('verification.json',JSON.stringify(results,null,2)); console.log(JSON.stringify(results,null,2));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
