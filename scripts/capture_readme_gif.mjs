import { createRequire } from 'module'
import { mkdirSync, readdirSync, unlinkSync, writeFileSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = join(__dirname, '..')
const require = createRequire(join(root, 'web', 'package.json'))
const { chromium } = require('playwright')

const framesDir = join(root, 'docs', 'gif-frames')
const url = process.env.CAPTURE_URL || 'https://court-gravity.onrender.com/'

mkdirSync(framesDir, { recursive: true })
for (const f of readdirSync(framesDir)) {
  if (f.endsWith('.png')) unlinkSync(join(framesDir, f))
}

const browser = await chromium.launch({ channel: 'chrome', headless: true })
const page = await browser.newPage({
  viewport: { width: 1280, height: 720 },
  deviceScaleFactor: 1,
})

await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 120_000 })
await page.waitForSelector('canvas', { timeout: 60_000 })
await page.waitForTimeout(3000)
await page.addStyleTag({
  content: `[class*="leva"] { opacity: 0 !important; pointer-events: none !important; }`,
})
await page.waitForTimeout(300)

const frameCount = 20
const intervalMs = 250
for (let i = 0; i < frameCount; i++) {
  await page.screenshot({
    path: join(framesDir, `frame_${String(i).padStart(3, '0')}.png`),
    type: 'png',
  })
  await page.waitForTimeout(intervalMs)
}

await browser.close()
writeFileSync(join(framesDir, 'meta.json'), JSON.stringify({ frameCount, intervalMs, url }, null, 2))
console.log(`Captured ${frameCount} frames → ${framesDir}`)
