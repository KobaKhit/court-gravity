export type PlayerProfile = {
  simulationId: string
  nbaId: string
  name: string
  shortName: string
  team: 'Lakers' | 'Spurs'
  position: string
  stats: {
    points: number
    rebounds: number
    assists: number
    steals: number
    blocks: number
    threePct: number
  }
}

export type GravityRatings = {
  offense: number
  defense: number
  offenseRadius: number
  defenseRadius: number
}

export const PROFILE_SEASON = '2025–26'

export const PLAYER_PROFILES: PlayerProfile[] = [
  {
    simulationId: 'BPG',
    nbaId: '1629029',
    name: 'Luka Dončić',
    shortName: 'Dončić',
    team: 'Lakers',
    position: 'PG',
    stats: { points: 33.5, rebounds: 7.7, assists: 8.3, steals: 1.6, blocks: 0.5, threePct: 37.0 },
  },
  {
    simulationId: 'BSG',
    nbaId: '1630559',
    name: 'Austin Reaves',
    shortName: 'Reaves',
    team: 'Lakers',
    position: 'SG',
    stats: { points: 23.3, rebounds: 4.7, assists: 5.5, steals: 1.1, blocks: 0.4, threePct: 35.9 },
  },
  {
    simulationId: 'BSF',
    nbaId: '2544',
    name: 'LeBron James',
    shortName: 'James',
    team: 'Lakers',
    position: 'SF',
    stats: { points: 20.9, rebounds: 6.1, assists: 7.2, steals: 1.2, blocks: 0.6, threePct: 31.7 },
  },
  {
    simulationId: 'BC',
    nbaId: '1629028',
    name: 'Deandre Ayton',
    shortName: 'Ayton',
    team: 'Lakers',
    position: 'C',
    stats: { points: 12.5, rebounds: 8.0, assists: 0.8, steals: 0.6, blocks: 1.0, threePct: 0 },
  },
  {
    simulationId: 'BPF',
    nbaId: '1629060',
    name: 'Rui Hachimura',
    shortName: 'Hachimura',
    team: 'Lakers',
    position: 'PF',
    stats: { points: 11.5, rebounds: 3.3, assists: 0.8, steals: 0.6, blocks: 0.3, threePct: 43.6 },
  },
  {
    simulationId: 'RPG',
    nbaId: '1628368',
    name: "De'Aaron Fox",
    shortName: 'Fox',
    team: 'Spurs',
    position: 'PG',
    stats: { points: 18.6, rebounds: 3.8, assists: 6.2, steals: 1.2, blocks: 0.3, threePct: 33.2 },
  },
  {
    simulationId: 'RSG',
    nbaId: '1642264',
    name: 'Stephon Castle',
    shortName: 'Castle',
    team: 'Spurs',
    position: 'SG',
    stats: { points: 16.7, rebounds: 5.3, assists: 7.4, steals: 1.1, blocks: 0.3, threePct: 33.2 },
  },
  {
    simulationId: 'RSF',
    nbaId: '1630170',
    name: 'Devin Vassell',
    shortName: 'Vassell',
    team: 'Spurs',
    position: 'SF',
    stats: { points: 13.9, rebounds: 4.0, assists: 2.5, steals: 0.9, blocks: 0.4, threePct: 38.4 },
  },
  {
    simulationId: 'RC',
    nbaId: '1641705',
    name: 'Victor Wembanyama',
    shortName: 'Wembanyama',
    team: 'Spurs',
    position: 'C',
    stats: { points: 25.0, rebounds: 11.5, assists: 3.1, steals: 1.0, blocks: 3.1, threePct: 34.9 },
  },
  {
    simulationId: 'RPF',
    nbaId: '203084',
    name: 'Harrison Barnes',
    shortName: 'Barnes',
    team: 'Spurs',
    position: 'PF',
    stats: { points: 9.9, rebounds: 2.8, assists: 1.9, steals: 0.6, blocks: 0.2, threePct: 38.8 },
  },
]

const profileMap = new Map(PLAYER_PROFILES.map((profile) => [profile.simulationId, profile]))

export function getPlayerProfile(simulationId: string) {
  return profileMap.get(simulationId)
}

export function headshotUrl(profile: PlayerProfile) {
  return `https://cdn.nba.com/headshots/nba/latest/1040x760/${profile.nbaId}.png`
}

export function gravityRatings(profile: PlayerProfile): GravityRatings {
  const { points, rebounds, assists, steals, blocks, threePct } = profile.stats
  const offense = clamp(0.68 + points / 80 + assists / 55 + rebounds / 250 + (threePct / 100) * 0.35, 0.82, 1.48)
  const defense = clamp(0.65 + steals * 0.18 + blocks * 0.16 + rebounds * 0.015, 0.78, 1.55)
  const offenseRadius = clamp(4.25 + assists * 0.12 + points * 0.014, 4.5, 6.0)
  const defenseRadius = clamp(4.1 + steals * 0.16 + blocks * 0.28 + rebounds * 0.018, 4.35, 5.9)
  return { offense, defense, offenseRadius, defenseRadius }
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value))
}
