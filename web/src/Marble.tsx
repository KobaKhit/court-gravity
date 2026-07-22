import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { FieldMode, SimPlayer, stepMarble } from './fieldMath'

type Props = {
  players: SimPlayer[]
  mode: FieldMode
  enabled: boolean
  resetKey: number
}

export function Marble({ players, mode, enabled, resetKey }: Props) {
  const mesh = useRef<THREE.Mesh>(null)
  const state = useRef({
    pos: [15, 30] as [number, number],
    vel: [0, 0] as [number, number],
    lastKey: -1,
  })

  useFrame((_, dt) => {
    if (!mesh.current) return
    if (state.current.lastKey !== resetKey) {
      state.current.pos = [15, 30]
      state.current.vel = [0, 0]
      state.current.lastKey = resetKey
    }
    if (!enabled) {
      mesh.current.position.set(state.current.pos[0], state.current.pos[1], 0.8)
      return
    }
    const clamped = Math.min(dt, 0.05)
    const next = stepMarble(state.current.pos, state.current.vel, players, mode, clamped, 1.6)
    state.current.pos = next.pos
    state.current.vel = next.vel
    const z = 0.8
    mesh.current.position.set(next.pos[0], next.pos[1], z)
  })

  return (
    <mesh ref={mesh} visible={enabled}>
      <sphereGeometry args={[0.7, 20, 20]} />
      <meshStandardMaterial color="#49A88F" emissive="#1a4a40" metalness={0.3} roughness={0.4} />
    </mesh>
  )
}
