import { SimPlayer } from './fieldMath'

export const POSSESSION_SECONDS = 15
export const POSSESSION_COUNT = 6
export const GAME_DURATION = POSSESSION_SECONDS * POSSESSION_COUNT

export type Squad = 'blue' | 'red'
export type GamePhase = 'Inbound' | 'Transition' | 'Set' | 'Action' | 'Shot' | 'DeadBall'

export type GameState = {
  players: SimPlayer[]
  ball: [number, number, number]
  possession: number
  offense: Squad
  playName: string
  phase: GamePhase
  phaseProgress: number
  localProgress: number
  offenseIntensity: number
  defenseIntensity: number
  shotClock: number | null
  blueScore: number
  redScore: number
  openPlayerId: string | null
  opportunityScore: number
  opportunitySeparation: number
  shotValue: 2 | 3
}

type Point = [number, number]
type Role = 'PG' | 'SG' | 'SF' | 'C' | 'PF'
type PositionMap = Record<string, Point>

const ROLES: Role[] = ['PG', 'SG', 'SF', 'C', 'PF']
const OPEN_ROLES: Role[] = ['SG', 'C', 'SG', 'C', 'SF', 'SG']
const SHOT_VALUES: (2 | 3)[] = [3, 2, 3, 2, 3, 3]
const INBOUND_END = 0.11
const TRANSITION_END = 0.35
const SET_END = 0.44
const ACTION_END = 0.77
const SHOT_END = 0.89

const clamp01 = (v: number) => Math.max(0, Math.min(1, v))
const smooth = (v: number) => {
  const x = clamp01(v)
  return x * x * (3 - 2 * x)
}
const phaseT = (value: number, start: number, end: number) => smooth((value - start) / (end - start))
const mix = (a: number, b: number, t: number) => a + (b - a) * smooth(t)
const mixPoint = (a: Point, b: Point, t: number): Point => [mix(a[0], b[0], t), mix(a[1], b[1], t)]
const playerId = (squad: Squad, role: Role) => `${squad === 'blue' ? 'B' : 'R'}${role}`
const openRoleForPossession = (possession: number) => OPEN_ROLES[possession % OPEN_ROLES.length]

const playNames = [
  'Lakers · Horns Kickout',
  'Spurs · Early Drag Roll',
  'Lakers · Spain Flare',
  'Spurs · Corner Split Slip',
  'Lakers · Flare Motion',
  'Spurs · High PnR Kickout',
]

function possessionContext(possession: number) {
  const offense: Squad = possession % 2 === 0 ? 'blue' : 'red'
  const defense: Squad = offense === 'blue' ? 'red' : 'blue'
  const direction = offense === 'blue' ? 1 : -1
  const attackHoopY = offense === 'blue' ? 90 : 4
  const inboundBaselineY = offense === 'blue' ? 4 : 90
  return { offense, defense, direction, attackHoopY, inboundBaselineY }
}

/**
 * Exact alignment used at both the end of the prior dead ball and the start
 * of the next inbound. Keeping this shared is what removes boundary teleports.
 */
function inboundPositions(possession: number): PositionMap {
  const { offense, defense, direction, inboundBaselineY } = possessionContext(possession)
  const map: PositionMap = {}
  const offenseSpots: Point[] = [
    [0, inboundBaselineY + direction * 7],
    [-12, inboundBaselineY + direction * 12],
    [12, inboundBaselineY + direction * 15],
    [0, inboundBaselineY + direction * 20],
    [0, inboundBaselineY - direction * 1.4],
  ]
  const defenseSpots: Point[] = [
    [1, inboundBaselineY + direction * 10],
    [-11, inboundBaselineY + direction * 15],
    [11, inboundBaselineY + direction * 18],
    [1, inboundBaselineY + direction * 23],
    [-6, inboundBaselineY + direction * 27],
  ]
  ROLES.forEach((role, i) => {
    map[playerId(offense, role)] = offenseSpots[i]
    map[playerId(defense, role)] = defenseSpots[i]
  })
  return map
}

function halfCourtPositions(possession: number, action: number): PositionMap {
  const { offense, defense, direction, attackHoopY } = possessionContext(possession)
  const topY = attackHoopY - direction * 25
  const wingY = attackHoopY - direction * 19
  const rimY = attackHoopY - direction * 6
  const playVariant = possession % 3
  const openRole = openRoleForPossession(possession)
  let offenseSpots: Point[]

  if (playVariant === 0) {
    offenseSpots = [
      [mix(0, 8 * direction, action), mix(topY, attackHoopY - direction * 10, action)],
      [-18, wingY],
      [18, wingY + direction * 2],
      [mix(-6, 0, action), mix(topY + direction * 4, rimY, action)],
      [mix(6, -6, action), mix(topY + direction * 4, topY + direction, action)],
    ]
  } else if (playVariant === 1) {
    offenseSpots = [
      [mix(-5, 3, action), mix(topY, attackHoopY - direction * 15, action)],
      [-21, attackHoopY - direction * 7],
      [mix(18, 10, action), mix(wingY, topY, action)],
      [mix(0, 2, action), mix(topY + direction * 5, rimY, action)],
      [mix(8, -8, action), mix(topY + direction * 3, topY - direction * 2, action)],
    ]
  } else {
    offenseSpots = [
      [0, topY],
      [mix(-18, -21.8, action), mix(wingY, attackHoopY - direction * 9, action)],
      [mix(19, 5, action), mix(attackHoopY - direction * 7, rimY, action)],
      [-7, topY + direction * 5],
      [18, topY + direction * 3],
    ]
  }

  const map: PositionMap = {}
  ROLES.forEach((role, i) => {
    const [x, y] = offenseSpots[i]
    const gap = i === 3 ? 1.8 : 2.7
    const shade = i % 2 === 0 ? 0.7 : -0.7
    // Late help creates a genuine weak-side opening. The assigned defender
    // pinches toward the paint as the action develops, exposing the shooter.
    const help = role === openRole ? smooth(action) : 0
    const helpTowardCenter = x === 0 ? 8 : -Math.sign(x) * 10
    map[playerId(offense, role)] = [x, y]
    map[playerId(defense, role)] = [
      x + shade + helpTowardCenter * help,
      y + direction * (gap + 3.2 * help),
    ]
  })
  return map
}

function blendPositionMaps(from: PositionMap, to: PositionMap, t: number): PositionMap {
  const result: PositionMap = {}
  for (const id of Object.keys(from)) result[id] = mixPoint(from[id], to[id] ?? from[id], t)
  return result
}

function phaseFor(local: number): { phase: GamePhase; progress: number } {
  if (local < INBOUND_END) return { phase: 'Inbound', progress: phaseT(local, 0, INBOUND_END) }
  if (local < TRANSITION_END) return { phase: 'Transition', progress: phaseT(local, INBOUND_END, TRANSITION_END) }
  if (local < SET_END) return { phase: 'Set', progress: phaseT(local, TRANSITION_END, SET_END) }
  if (local < ACTION_END) return { phase: 'Action', progress: phaseT(local, SET_END, ACTION_END) }
  if (local < SHOT_END) return { phase: 'Shot', progress: phaseT(local, ACTION_END, SHOT_END) }
  return { phase: 'DeadBall', progress: phaseT(local, SHOT_END, 1) }
}

function fieldIntensities(phase: GamePhase, progress: number) {
  if (phase === 'DeadBall') return { offenseIntensity: 0, defenseIntensity: 0 }
  if (phase === 'Inbound') {
    // The ball is dead for the first half of the inbound. Gravity only begins
    // once the pass leaves the inbounder's hands.
    const live = phaseT(progress, 0.52, 1)
    return { offenseIntensity: live * 0.24, defenseIntensity: live * 0.07 }
  }
  if (phase === 'Transition') {
    return {
      offenseIntensity: mix(0.24, 1, progress),
      defenseIntensity: mix(0.07, 0.92, phaseT(progress, 0.18, 1)),
    }
  }
  if (phase === 'Set') {
    return {
      offenseIntensity: 1,
      defenseIntensity: mix(0.92, 1, progress),
    }
  }
  if (phase === 'Shot') {
    const fade = 1 - phaseT(progress, 0.62, 1)
    return { offenseIntensity: fade, defenseIntensity: fade }
  }
  return { offenseIntensity: 1, defenseIntensity: 1 }
}

function scoresAt(possession: number, local: number) {
  const completed = possession + (local >= SHOT_END ? 1 : 0)
  let blueScore = 82
  let redScore = 79
  for (let i = 0; i < completed; i++) {
    if (i % 2 === 0) blueScore += SHOT_VALUES[i]
    else redScore += SHOT_VALUES[i]
  }
  return { blueScore, redScore }
}

/**
 * Six alternating, continuous possessions. Each segment starts with the
 * inbound created by the prior segment's dead-ball endpoint.
 */
export function gameStateAtTime(time: number, sigma = 5): GameState {
  const wrapped = ((time % GAME_DURATION) + GAME_DURATION) % GAME_DURATION
  const possession = Math.floor(wrapped / POSSESSION_SECONDS)
  const local = (wrapped % POSSESSION_SECONDS) / POSSESSION_SECONDS
  const { offense, defense, direction, attackHoopY } = possessionContext(possession)
  const { phase, progress } = phaseFor(local)
  const inbound = inboundPositions(possession)
  const setStart = halfCourtPositions(possession, 0)
  // Real possessions flow directly from early offense into the set. A small
  // amount of action develops during Set, then carries continuously into the
  // main action instead of freezing everyone after transition.
  const liveActionProgress =
    phase === 'Set'
      ? mix(0, 0.22, progress)
      : phase === 'Action'
        ? mix(0.22, 1, progress)
        : phase === 'Shot' || phase === 'DeadBall'
          ? 1
          : 0
  const active = halfCourtPositions(possession, liveActionProgress)
  const shotPositions = halfCourtPositions(possession, 1)
  const nextPossession = (possession + 1) % POSSESSION_COUNT
  const nextInbound = inboundPositions(nextPossession)

  let positions: PositionMap
  if (phase === 'Inbound') positions = inbound
  else if (phase === 'Transition') positions = blendPositionMaps(inbound, setStart, progress)
  else if (phase === 'DeadBall') positions = blendPositionMaps(shotPositions, nextInbound, progress)
  else positions = active

  const receiverRole = openRoleForPossession(possession)
  const pg = positions[playerId(offense, 'PG')]
  const receiver = positions[playerId(offense, receiverRole)]
  const inbounder = inbound[playerId(offense, 'PF')]
  let ball: [number, number, number]

  if (phase === 'Inbound') {
    const pass = phaseT(progress, 0.52, 1)
    const xy = mixPoint(inbounder, pg, pass)
    ball = [xy[0], xy[1], 3.1 + Math.sin(pass * Math.PI) * 2.2]
  } else if (phase === 'Transition' || phase === 'Set') {
    const bounce = 0.9 + Math.abs(Math.sin(local * POSSESSION_SECONDS * 5.4)) * 2.15
    const z = phase === 'Transition' ? mix(3.1, bounce, phaseT(progress, 0, 0.14)) : bounce
    ball = [pg[0], pg[1], z]
  } else if (phase === 'Action') {
    const pass = phaseT(progress, 0.24, 0.72)
    const xy = mixPoint(pg, receiver, pass)
    const bounce = 0.9 + Math.abs(Math.sin(local * POSSESSION_SECONDS * 5.4)) * 2.15
    ball = [xy[0], xy[1], mix(bounce, 3.1, pass) + Math.sin(pass * Math.PI) * 3]
  } else if (phase === 'Shot') {
    const shotTarget: Point = [0, attackHoopY]
    const xy = mixPoint(receiver, shotTarget, progress)
    ball = [xy[0], xy[1], mix(3.1, 5.1, progress) + Math.sin(progress * Math.PI) * 8.5]
  } else {
    // The made ball drops through the rim, is collected, and arrives at the
    // exact next-inbound location by the segment boundary.
    const nextOffense = possessionContext(nextPossession).offense
    const nextInbounder = nextInbound[playerId(nextOffense, 'PF')]
    const retrieve = phaseT(progress, 0.18, 1)
    const xy = mixPoint([0, attackHoopY], nextInbounder, retrieve)
    const dropZ = progress < 0.28 ? mix(5.1, 0.65, progress / 0.28) : mix(0.65, 3.1, retrieve)
    ball = [xy[0], xy[1], dropZ]
  }

  const timingOpportunity =
    phase === 'Set'
      ? phaseT(progress, 0.52, 1) * 0.24
      : phase === 'Action'
      ? mix(0.24, 1, phaseT(progress, 0.08, 0.72))
      : phase === 'Shot'
        ? 1 - phaseT(progress, 0.28, 0.78)
        : 0
  const candidateId = playerId(offense, receiverRole)
  const candidate = positions[candidateId]
  const opportunitySeparation = Math.min(
    ...ROLES.map((role) => {
      const defenderPoint = positions[playerId(defense, role)]
      return Math.hypot(candidate[0] - defenderPoint[0], candidate[1] - defenderPoint[1])
    }),
  )
  const opportunityTeammateSpacing = Math.min(
    ...ROLES.filter((role) => role !== receiverRole).map((role) => {
      const teammate = positions[playerId(offense, role)]
      return Math.hypot(candidate[0] - teammate[0], candidate[1] - teammate[1])
    }),
  )
  // Spacing modifies the field continuously instead of switching on at a
  // single coverage threshold. Tight coverage remains nearly neutral; open
  // and wide-open windows progressively amplify offensive advantage.
  const spacingOpportunity = phaseT(opportunitySeparation, 3.5, 7.5)
  const floorBalance = phaseT(opportunityTeammateSpacing, 5, 10)
  const opportunityScore = timingOpportunity * spacingOpportunity * floorBalance
  // NBA tracking commonly treats 4–6 feet as open and 6+ as wide open.
  const openPlayerId = opportunityScore > 0.2 && opportunitySeparation >= 5 ? candidateId : null

  const players: SimPlayer[] = []
  ;(['blue', 'red'] as Squad[]).forEach((squad) => {
    ROLES.forEach((role, i) => {
      const [x, y] = positions[playerId(squad, role)]
      const isOffense = squad === offense
      const teammateSpacing = isOffense
        ? Math.min(
            ...ROLES.filter((otherRole) => otherRole !== role).map((otherRole) => {
              const teammate = positions[playerId(offense, otherRole)]
              return Math.hypot(x - teammate[0], y - teammate[1])
            }),
          )
        : undefined
      players.push({
        id: playerId(squad, role),
        x,
        y,
        mass: isOffense ? (i === 0 ? 1.25 : i === 1 ? 1.15 : 0.95) : i === 0 || i === 3 ? 1.08 : 0.92,
        sigma: isOffense && i === 1 ? sigma + 0.8 : sigma,
        team: isOffense ? 'offense' : 'defense',
        squad,
        role: isOffense ? role.toLowerCase() : 'lockdown',
        opportunity: playerId(squad, role) === candidateId ? opportunityScore : 0,
        teammateSpacing,
      })
    })
  })

  const intensities = fieldIntensities(phase, progress)
  const liveProgress = clamp01((local - INBOUND_END * 0.52) / (SHOT_END - INBOUND_END * 0.52))
  const shotClock = phase === 'DeadBall' ? null : phase === 'Inbound' && progress < 0.52 ? 24 : 24 * (1 - liveProgress)

  return {
    players,
    ball,
    possession,
    offense,
    playName: playNames[possession],
    phase,
    phaseProgress: progress,
    localProgress: local,
    ...intensities,
    shotClock,
    openPlayerId,
    opportunityScore,
    opportunitySeparation,
    shotValue: SHOT_VALUES[possession],
    ...scoresAt(possession, local),
  }
}
