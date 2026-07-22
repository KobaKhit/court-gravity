/** Court geometry + Gaussian field (mirrors core/field.py for the web). */

export type Team = 'offense' | 'defense'
export type FieldMode = 'net' | 'offense' | 'defense'
export type KernelType = 'gaussian' | 'softened'

export interface CourtConfig {
  length: number
  width: number
  origin: string
  default_sigma: number
}

export interface SimPlayer {
  id: string
  x: number
  y: number
  mass: number
  sigma: number
  team: Team
  squad?: 'blue' | 'red'
  role?: string
  /** 0–1 live indicator for an intentionally created open look. */
  opportunity?: number
  /** Nearest offensive teammate distance, used to suppress false stacked value. */
  teammateSpacing?: number
}

export const DEFAULT_COURT: CourtConfig = {
  length: 94,
  width: 50,
  origin: 'hoop',
  default_sigma: 5,
}

export function courtExtents(c: CourtConfig = DEFAULT_COURT) {
  const halfW = c.width / 2
  return { x0: -halfW, x1: halfW, y0: 0, y1: c.length }
}

export function influence(
  x: number,
  y: number,
  p: SimPlayer,
  kernel: KernelType = 'gaussian',
  softening = 2,
  G = 1,
): number {
  const dx = x - p.x
  const dy = y - p.y
  if (kernel === 'softened') {
    return (G * p.mass) / Math.sqrt(dx * dx + dy * dy + softening * softening)
  }
  const s = p.sigma
  return p.mass * Math.exp(-(dx * dx + dy * dy) / (2 * s * s))
}

export function courtSurface(
  x: number,
  y: number,
  players: SimPlayer[],
  mode: FieldMode = 'net',
  kernel: KernelType = 'gaussian',
): number {
  let z = 0
  for (const p of players) {
    if (mode === 'offense' && p.team !== 'offense') continue
    if (mode === 'defense' && p.team !== 'defense') continue
    const I = influence(x, y, p, kernel)
    if (mode === 'offense') z -= I
    else if (mode === 'defense') z += I
    else z += p.team === 'offense' ? -I : I
  }
  return z
}

export function evaluateGrid(
  players: SimPlayer[],
  nx = 80,
  ny = 75,
  mode: FieldMode = 'net',
  kernel: KernelType = 'gaussian',
  court: CourtConfig = DEFAULT_COURT,
): { xs: Float32Array; ys: Float32Array; Z: Float32Array; nx: number; ny: number } {
  const { x0, x1, y0, y1 } = courtExtents(court)
  const xs = new Float32Array(nx)
  const ys = new Float32Array(ny)
  const Z = new Float32Array(nx * ny)
  for (let i = 0; i < nx; i++) xs[i] = x0 + (i / (nx - 1)) * (x1 - x0)
  for (let j = 0; j < ny; j++) ys[j] = y0 + (j / (ny - 1)) * (y1 - y0)
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      Z[j * nx + i] = courtSurface(xs[i], ys[j], players, mode, kernel)
    }
  }
  return { xs, ys, Z, nx, ny }
}

export function packUniforms(players: SimPlayer[], maxPlayers = 16) {
  const uPlayers: number[] = []
  const uSigma: number[] = []
  const list = players.slice(0, maxPlayers)
  for (const p of list) {
    const signed = p.team === 'offense' ? -p.mass : p.mass
    uPlayers.push(p.x, p.y, signed)
    uSigma.push(p.sigma)
  }
  while (uPlayers.length < maxPlayers * 3) {
    uPlayers.push(0, 0, 0)
    uSigma.push(5)
  }
  return { uPlayers, uSigma, uCount: list.length }
}

/** ∇z analytic for isotropic Gaussians; used by marble integrator. */
export function gradientAt(
  x: number,
  y: number,
  players: SimPlayer[],
  mode: FieldMode = 'net',
): [number, number] {
  let gx = 0
  let gy = 0
  for (const p of players) {
    if (mode === 'offense' && p.team !== 'offense') continue
    if (mode === 'defense' && p.team !== 'defense') continue
    const dx = x - p.x
    const dy = y - p.y
    const I = influence(x, y, p, 'gaussian')
    const s2 = p.sigma * p.sigma
    let sx = 1
    if (mode === 'offense') sx = -1
    else if (mode === 'defense') sx = 1
    else sx = p.team === 'offense' ? -1 : 1
    // ∂I/∂x = -I * dx / σ² ; contribution to z is sx * I
    gx += sx * (-I * dx / s2)
    gy += sx * (-I * dy / s2)
  }
  return [gx, gy]
}

export function stepMarble(
  pos: [number, number],
  vel: [number, number],
  players: SimPlayer[],
  mode: FieldMode,
  dt = 0.02,
  damping = 1.5,
  court: CourtConfig = DEFAULT_COURT,
): { pos: [number, number]; vel: [number, number] } {
  const [gx, gy] = gradientAt(pos[0], pos[1], players, mode)
  const ax = -gx - damping * vel[0]
  const ay = -gy - damping * vel[1]
  const nv: [number, number] = [vel[0] + ax * dt, vel[1] + ay * dt]
  const { x0, x1, y0, y1 } = courtExtents(court)
  const np: [number, number] = [
    Math.min(x1, Math.max(x0, pos[0] + nv[0] * dt)),
    Math.min(y1, Math.max(y0, pos[1] + nv[1] * dt)),
  ]
  return { pos: np, vel: nv }
}

export interface TrajFile {
  players: Array<{
    id: string
    role: string
    team: Team
    stats: { base_mass: number; sigma: number; respect?: number }
    traj: Array<[number, number, number]>
  }>
  ball: Array<[number, number, number]>
  dt: number
  duration: number
}

export function isValidTrajFile(data: unknown): data is TrajFile {
  if (!data || typeof data !== 'object') return false
  const d = data as TrajFile
  return (
    Array.isArray(d.players) &&
    d.players.length > 0 &&
    typeof d.dt === 'number' &&
    d.dt > 0 &&
    typeof d.duration === 'number' &&
    d.players.every(
      (p) =>
        p &&
        Array.isArray(p.traj) &&
        p.traj.length > 0 &&
        p.stats &&
        typeof p.stats.base_mass === 'number',
    )
  )
}

export function playersAtTime(data: TrajFile, t: number): SimPlayer[] {
  const dt = data.dt > 0 ? data.dt : 1 / 30
  return data.players.map((p) => {
    const traj = p.traj
    const last = Math.max(0, traj.length - 1)
    const raw = Number.isFinite(t) ? Math.floor(t / dt) : 0
    const idx = Math.max(0, Math.min(raw, last))
    const frame = traj[idx] ?? traj[0]
    const x = frame?.[1] ?? 0
    const y = frame?.[2] ?? 0
    return {
      id: p.id,
      x,
      y,
      mass: p.stats?.base_mass ?? 1,
      sigma: p.stats?.sigma ?? 5,
      team: p.team,
      role: p.role,
    }
  })
}

export function defaultStaticLineup(massScale = 1, sigma = 5): SimPlayer[] {
  return [
    { id: 'pg', x: 0, y: 26, mass: 1.2 * massScale, sigma, team: 'offense', role: 'playmaker' },
    { id: 'sg', x: -18, y: 22, mass: 1.4 * massScale, sigma: sigma + 1, team: 'offense', role: 'sharpshooter' },
    { id: 'sf', x: 18, y: 20, mass: 0.9 * massScale, sigma, team: 'offense', role: 'wing' },
    { id: 'c', x: 0, y: 6, mass: 1.1 * massScale, sigma: sigma - 0.5, team: 'offense', role: 'rim_runner' },
    { id: 'pf', x: -16, y: 12, mass: 0.9 * massScale, sigma, team: 'offense', role: 'wing' },
    { id: 'd0', x: 0, y: 24, mass: 1.0 * massScale, sigma, team: 'defense', role: 'lockdown' },
    { id: 'd1', x: -14, y: 20, mass: 1.0 * massScale, sigma, team: 'defense', role: 'lockdown' },
    { id: 'd2', x: 14, y: 18, mass: 0.95 * massScale, sigma, team: 'defense', role: 'lockdown' },
    { id: 'd3', x: 2, y: 8, mass: 1.05 * massScale, sigma, team: 'defense', role: 'lockdown' },
    { id: 'd4', x: -10, y: 12, mass: 0.9 * massScale, sigma, team: 'defense', role: 'lockdown' },
  ]
}
