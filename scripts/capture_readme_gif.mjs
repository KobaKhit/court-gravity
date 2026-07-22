import { createRequire } from 'module'
import { copyFileSync, mkdirSync, readdirSync, unlinkSync, writeFileSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { spawnSync } from 'child_process'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = join(__dirname, '..')
const require = createRequire(join(root, 'web', 'package.json'))
const { chromium } = require('playwright')

const framesDir = join(root, 'docs', 'gif-frames')
const outGif = join(root, 'docs', 'court-gravity-preview.gif')
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
writeFileSync(join(framesDir, 'meta.json'), JSON.stringify({ frameCount, intervalMs, url, outGif }, null, 2))
console.log(`Captured ${frameCount} frames → ${framesDir}`)

const stitch = `
from pathlib import Path
from PIL import Image
frames_dir = Path(r'''${framesDir}''')
paths = sorted(frames_dir.glob('frame_*.png'))[::2]
frames = []
for p in paths:
    im = Image.open(p).convert('RGB')
    w = 880
    h = max(1, round(im.height * (w / im.width)))
    im = im.resize((w, h), Image.Resampling.LANCZOS)
    frames.append(im.convert('P', palette=Image.ADAPTIVE, colors=160))
out = Path(r'''${outGif}''')
frames[0].save(out, save_all=True, append_images=frames[1:], duration=160, loop=0, optimize=True)
print(f'Wrote {out} ({out.stat().st_size} bytes, {len(frames)} frames)')
`

const pyCandidates = [
  join(root, '.venv', 'Scripts', 'python.exe'),
  join(root, '.venv', 'bin', 'python'),
  'python',
]
let stitched = false
for (const py of pyCandidates) {
  const result = spawnSync(py, ['-c', stitch], { encoding: 'utf8' })
  if (result.status === 0) {
    process.stdout.write(result.stdout || '')
    stitched = true
    break
  }
}
if (!stitched) {
  console.error('Captured frames, but could not stitch GIF (Pillow/python missing).')
  process.exitCode = 2
} else {
  // Keep the social/OG asset on the static site in sync with docs/.
  const publicGif = join(root, 'web', 'public', 'court-gravity-preview.gif')
  copyFileSync(outGif, publicGif)
  console.log(`Synced OG preview → ${publicGif}`)
}
