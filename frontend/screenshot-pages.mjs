import puppeteer from 'puppeteer-core';

const browser = await puppeteer.launch({
  executablePath: '/Users/shayuen/Library/Caches/ms-playwright/chromium-1223/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing',
  headless: 'new',
  args: ['--no-sandbox', '--disable-gpu']
});

const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });

const errors = [];
page.on('console', msg => {
  if (msg.type() === 'error') errors.push('[CONSOLE] ' + msg.text());
});
page.on('pageerror', err => errors.push('[PAGE ERROR] ' + err.message));

try {
  console.log('=== 登录 ===');
  await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle2' });
  await page.waitForSelector('input[placeholder*="用户名"]', { timeout: 5000 });
  await page.type('input[placeholder*="用户名"]', 'admin', { delay: 30 });
  await page.type('input[type="password"]', 'admin123', { delay: 30 });
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 10000 }),
    page.evaluate(() => {
      const btns = [...document.querySelectorAll('button')];
      const loginBtn = btns.find(b => b.textContent.includes('登'));
      if (loginBtn) loginBtn.click();
    })
  ]);
  console.log('登录后 URL:', page.url());

  console.log('\n=== 中医管理页面 ===');
  await page.goto('http://localhost:3000/tcm', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: '/tmp/tcm-page.png', fullPage: true });
  
  const tcmBody = await page.evaluate(() => document.querySelector('.el-table__body')?.innerHTML?.length || 0);
  const tcmText = await page.evaluate(() => document.body.innerText.substring(0, 800));
  console.log('TCM table body size:', tcmBody);
  console.log('TCM 页面文本:\n', tcmText.substring(0, 500));

  console.log('\n=== 急救中心页面 ===');
  await page.goto('http://localhost:3000/emergency', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: '/tmp/emergency-page.png', fullPage: true });
  
  const emText = await page.evaluate(() => document.body.innerText.substring(0, 800));
  console.log('Emergency 页面文本:\n', emText.substring(0, 500));

  if (errors.length) {
    console.log('\n=== 错误汇总 ===');
    errors.forEach(e => console.log(e));
  } else {
    console.log('\n无 JS 错误');
  }
} catch(e) {
  console.error('FATAL:', e.message);
  await page.screenshot({ path: '/tmp/error-state.png' });
} finally {
  await browser.close();
}
