import { useEffect, useRef } from 'react'
import { evaluateGrid, FieldMode, KernelType, SimPlayer } from './fieldMath'
import { getPlayerProfile } from './playerProfiles'

type Props = {
  players: SimPlayer[]
  mode: FieldMode
  kernel: KernelType
  width?: number
  height?: number
  expanded?: boolean
}

const mix = (a: number, b: number, t: number) => a + (b - a) * t
const smoothstep = (edge0: number, edge1: number, value: number) => {
  const x = Math.max(0, Math.min(1, (value - edge0) / (edge1 - edge0)))
  return x * x * (3 - 2 * x)
}

export function Heatmap2D({ players, mode, kernel, width = 1128, height = 600, expanded = false }: Props) {
  const ref = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const nx = 72
    const ny = 136
    const offenseGrid = evaluateGrid(players, nx, ny, 'offense', kernel).Z
    const defenseGrid = evaluateGrid(players, nx, ny, 'defense', kernel).Z
    const img = ctx.createImageData(ny, nx)
    const fixedScale = mode === 'net' ? 1.15 : 1.45

    for (let screenY = 0; screenY < nx; screenY++) {
      for (let screenX = 0; screenX < ny; screenX++) {
        const xIndex = nx - 1 - screenY
        const yIndex = screenX
        const index = yIndex * nx + xIndex
        const offense = Math.max(0, -offenseGrid[index])
        const defense = Math.max(0, defenseGrid[index])
        const net = mode === 'offense' ? offense : mode === 'defense' ? -defense : offense - defense
        const offenseStrength = smoothstep(0.02, 0.68, Math.max(0, net) / fixedScale)
        const defenseStrength = smoothstep(0.02, 0.68, Math.max(0, -net) / fixedScale)
        const contested =
          mode === 'net'
            ? Math.min(1, Math.min(offense, defense) / fixedScale) *
              (1 - Math.max(offenseStrength, defenseStrength))
            : 0
        const plank = Math.floor(screenY / 7) % 2
        let r = expanded ? (plank ? 67 : 57) : 2
        let g = expanded ? (plank ? 47 : 39) : 4
        let b = expanded ? (plank ? 27 : 22) : 7
        r = mix(r, 111, contested * 0.18)
        g = mix(g, 117, contested * 0.18)
        b = mix(b, 124, contested * 0.18)
        r = mix(r, 38, offenseStrength * 0.72)
        g = mix(g, 220, offenseStrength * 0.72)
        b = mix(b, 255, offenseStrength * 0.72)
        r = mix(r, 245, defenseStrength * 0.62)
        g = mix(g, 52, defenseStrength * 0.62)
        b = mix(b, 31, defenseStrength * 0.62)
        const o = (screenY * ny + screenX) * 4
        img.data[o] = r
        img.data[o + 1] = g
        img.data[o + 2] = b
        img.data[o + 3] = 255
      }
    }

    const off = document.createElement('canvas')
    off.width = ny
    off.height = nx
    off.getContext('2d')!.putImageData(img, 0, 0)
    ctx.imageSmoothingEnabled = true
    ctx.clearRect(0, 0, width, height)
    ctx.drawImage(off, 0, 0, width, height)
    if (expanded) drawCourt(ctx, width, height)

    for (const p of players) {
      const px = (p.y / 94) * width
      const py = (1 - (p.x + 25) / 50) * height
      const profile = getPlayerProfile(p.id)
      ctx.beginPath()
      ctx.arc(px, py, expanded ? 7 : 5, 0, Math.PI * 2)
      ctx.fillStyle = p.squad === 'blue' ? '#fdb927' : '#c4ced4'
      ctx.fill()
      ctx.lineWidth = expanded ? 3 : 2
      ctx.strokeStyle = p.team === 'offense' ? '#40dfff' : '#ff4d32'
      ctx.stroke()
      ctx.fillStyle = '#071019'
      ctx.font = `800 ${expanded ? 10 : 8}px Inter, sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(profile?.shortName.slice(0, 2).toUpperCase() ?? p.id.slice(-2), px, py + 0.5)
    }
  }, [players, mode, kernel, width, height, expanded])

  return (
    <div className={`heatmap-panel ${expanded ? 'expanded' : 'inset'}`}>
      <div className="heatmap-label">2D NET ADVANTAGE</div>
      <canvas ref={ref} width={width} height={height} />
    </div>
  )
}

function drawCourt(ctx: CanvasRenderingContext2D, width: number, height: number) {
  const sx = width / 94
  const sy = height / 50
  const point = (x: number, y: number): [number, number] => [y * sx, (25 - x) * sy]
  ctx.save()
  ctx.strokeStyle = 'rgba(242, 246, 249, 0.92)'
  ctx.lineWidth = Math.max(1.4, width / 650)
  ctx.beginPath()
  ctx.rect(1, 1, width - 2, height - 2)
  ctx.moveTo(47 * sx, 0)
  ctx.lineTo(47 * sx, height)
  ctx.stroke()

  const drawCircle = (x: number, y: number, radius: number) => {
    const [cx, cy] = point(x, y)
    ctx.beginPath()
    ctx.arc(cx, cy, radius * sx, 0, Math.PI * 2)
    ctx.stroke()
  }
  drawCircle(0, 47, 6)
  drawCircle(0, 19, 6)
  drawCircle(0, 75, 6)
  drawCircle(0, 4, 4)
  drawCircle(0, 90, 4)

  const drawPaint = (near: boolean) => {
    const y0 = near ? 0 : 75
    const y1 = near ? 19 : 94
    const [left, top] = point(8, y0)
    const [right, bottom] = point(-8, y1)
    ctx.strokeRect(Math.min(left, right), Math.min(top, bottom), Math.abs(right - left), Math.abs(bottom - top))
  }
  drawPaint(true)
  drawPaint(false)

  const cornerBreak = Math.sqrt(23.75 * 23.75 - 22 * 22)
  const nearHoop = point(0, 4)
  const farHoop = point(0, 90)
  const angle = Math.atan2(22, cornerBreak)
  ctx.beginPath()
  ctx.arc(nearHoop[0], nearHoop[1], 23.75 * sx, -angle, angle)
  ctx.moveTo(0, point(22, 0)[1])
  ctx.lineTo((4 + cornerBreak) * sx, point(22, 0)[1])
  ctx.moveTo(0, point(-22, 0)[1])
  ctx.lineTo((4 + cornerBreak) * sx, point(-22, 0)[1])
  ctx.stroke()
  ctx.beginPath()
  ctx.arc(farHoop[0], farHoop[1], 23.75 * sx, Math.PI - angle, Math.PI + angle)
  ctx.moveTo(width, point(22, 94)[1])
  ctx.lineTo((90 - cornerBreak) * sx, point(22, 94)[1])
  ctx.moveTo(width, point(-22, 94)[1])
  ctx.lineTo((90 - cornerBreak) * sx, point(-22, 94)[1])
  ctx.stroke()
  ctx.restore()
}
