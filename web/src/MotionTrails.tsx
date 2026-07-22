import { useMemo } from 'react'
import { Line } from '@react-three/drei'
import { gameStateAtTime } from './gameSimulation'

type Trail = {
  id: string
  color: string
  points: [number, number, number][]
}

export function MotionTrails({
  time,
  sigma,
  possession,
  phase,
  phaseProgress,
}: {
  time: number
  sigma: number
  possession: number
  phase: string
  phaseProgress: number
}) {
  const { playerTrails, ballTrail } = useMemo(() => {
    const samples = Array.from({ length: 20 }, (_, i) => {
      const sampleTime = Math.max(0, time - (19 - i) * 0.12)
      const state = gameStateAtTime(sampleTime, sigma)
      const isLiveInbound = state.phase !== 'Inbound' || state.phaseProgress >= 0.52
      return state.possession === possession && state.phase !== 'DeadBall' && isLiveInbound ? state : null
    }).filter(Boolean) as ReturnType<typeof gameStateAtTime>[]

    const current = gameStateAtTime(time, sigma)
    const trails: Trail[] = current.players.map((player) => ({
      id: player.id,
      color: player.squad === 'blue' ? '#20bfff' : '#ff4d32',
      points: samples
        .map((state) => state.players.find((candidate) => candidate.id === player.id))
        .filter(Boolean)
        .map((point) => [point!.x, point!.y, 0.42] as [number, number, number]),
    }))

    return {
      playerTrails: trails,
      ballTrail: samples.map((state) => state.ball),
    }
  }, [time, sigma, possession])

  if (phase === 'DeadBall' || (phase === 'Inbound' && phaseProgress < 0.52)) return null
  const inboundOpacity = phase === 'Inbound' ? 0.14 : 0.34

  return (
    <group>
      {playerTrails.map((trail) =>
        trail.points.length > 1 ? (
          <Line
            key={trail.id}
            points={trail.points}
            color={trail.color}
            lineWidth={1.25}
            transparent
            opacity={inboundOpacity}
            depthWrite={false}
          />
        ) : null,
      )}
      {ballTrail.length > 1 && (
        <Line
          points={ballTrail}
          color={phase === 'Shot' ? '#ffd166' : '#ff9a3d'}
          lineWidth={phase === 'Shot' ? 3.2 : 1.8}
          transparent
          opacity={phase === 'Shot' ? 0.95 : phase === 'Inbound' ? 0.35 : 0.55}
          depthWrite={false}
        />
      )}
    </group>
  )
}
