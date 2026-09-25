// Interface check for Eknaam: queue, a case page, upload page, audit and method at phone and desktop widths.
//   ./run.sh ui-check [base-url]   (needs: npm install && npx playwright install chromium)
// Fails on a console error, a missing heading, horizontal overflow, or a case page without its sheet entry and evidence table.
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path')
const BASE = process.argv[2] || 'http://127.0.0.1:8015'; const SHOTS = path.join(__dirname, 'shots'); fs.mkdirSync(SHOTS, { recursive: true })
const WIDTHS = { phone: { width: 390, height: 844 }, desktop: { width: 1366, height: 900 } }
const failures = []; const fail = (m) => { failures.push(m); console.log('FAIL', m) }
;(async () => {
  const browser = await chromium.launch(); const res = await fetch(BASE + '/api/cases').then((r) => r.json()); const first = res[0]
  for (const [wname, vp] of Object.entries(WIDTHS)) {
    const page = await browser.newPage({ viewport: vp }); const errors = []
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) }); page.on('pageerror', (e) => errors.push(String(e)))
    const pages = { '': 'Pick a name to review', add: 'Add recordings of one place name', audit: 'Audit trail', method: 'How a recommendation is made' }
    if (first) pages[String(first.id)] = null
    for (const [hash, heading] of Object.entries(pages)) {
      await page.goto(BASE + '/#/' + hash, { waitUntil: 'networkidle' }); await page.waitForTimeout(600)
      const body = await page.textContent('body')
      if (heading && !body.includes(heading)) fail(`${wname} #/${hash}: heading "${heading}" missing`)
      if (!heading) {
        if (!(await page.$('.sheet-roman'))) fail(`${wname} case ${hash}: sheet entry missing`)
        if (!(await page.$('table.evidence'))) fail(`${wname} case ${hash}: evidence table missing`)
        if (!body.includes('Officer decision')) fail(`${wname} case ${hash}: decision panel missing`)
      }
      const over = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1)
      if (over) fail(`${wname} #/${hash}: horizontal overflow`)
      await page.screenshot({ path: path.join(SHOTS, `${wname}-${hash || 'queue'}.png`), fullPage: true })
    }
    if (errors.length) fail(`${wname}: console errors: ${errors.slice(0, 3).join(' | ')}`)
    await page.close()
  }
  await browser.close(); console.log(failures.length ? `${failures.length} failure(s)` : 'UI check passed'); process.exit(failures.length ? 1 : 0)
})()
