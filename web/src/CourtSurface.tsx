import { useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { Html, Line, Text } from '@react-three/drei'
import * as THREE from 'three'
import { courtFragmentShader, courtVertexShader } from './shaders'
import { FieldMode, KernelType, SimPlayer, courtExtents, courtSurface, packUniforms } from './fieldMath'
import { getPlayerProfile, gravityRatings, headshotUrl } from './playerProfiles'

type Props = {
  players: SimPlayer[]
  mode: FieldMode
  kernel: KernelType
  zScale?: number
  colorScale?: number
  segments?: number
}

/** Court in XY plane, Z = height (matches shader + Python core). */
export function CourtMesh({
  players,
  mode,
  kernel,
  zScale = 0.35,
  colorScale = 1.2,
  segments = 200,
}: Props) {
  const mat = useRef<THREE.ShaderMaterial>(null)
  const { x0, x1, y0, y1 } = courtExtents()
  const width = x1 - x0
  const height = y1 - y0

  const uniforms = useMemo(
    () => ({
      uPlayers: { value: Array.from({ length: 16 }, () => new THREE.Vector3()) },
      uSigma: { value: new Float32Array(16).fill(5) },
      uCount: { value: 0 },
      uZScale: { value: zScale },
      uMode: { value: 0 },
      uKernel: { value: 0 },
      uSoftening: { value: 2.0 },
      uColorScale: { value: colorScale },
    }),
    [],
  )

  useFrame(() => {
    if (!mat.current) return
    const packed = packUniforms(players)
    for (let i = 0; i < 16; i++) {
      const o = i * 3
      uniforms.uPlayers.value[i].set(packed.uPlayers[o], packed.uPlayers[o + 1], packed.uPlayers[o + 2])
      uniforms.uSigma.value[i] = packed.uSigma[i]
    }
    uniforms.uCount.value = packed.uCount
    uniforms.uMode.value = mode === 'offense' ? 1 : mode === 'defense' ? 2 : 0
    uniforms.uKernel.value = kernel === 'softened' ? 1 : 0
    uniforms.uZScale.value = zScale
    uniforms.uColorScale.value = colorScale
  })

  return (
    <mesh position={[(x0 + x1) / 2, (y0 + y1) / 2, 0]}>
      <planeGeometry args={[width, height, segments, segments]} />
      <shaderMaterial
        ref={mat}
        vertexShader={courtVertexShader}
        fragmentShader={courtFragmentShader}
        uniforms={uniforms}
        side={THREE.DoubleSide}
      />
    </mesh>
  )
}

export function PlayerMarkers({
  players,
  mode,
  kernel,
  zScale,
  visibleProfileIds,
  showImages,
  showStats,
}: {
  players: SimPlayer[]
  mode: FieldMode
  kernel: KernelType
  zScale: number
  visibleProfileIds: Set<string>
  showImages: boolean
  showStats: boolean
}) {
  return (
    <group>
      {players.map((p) => {
        const opportunity = p.opportunity ?? 0
        const profile = visibleProfileIds.has(p.id) ? getPlayerProfile(p.id) : undefined
        const ratings = profile ? gravityRatings(profile) : null
        const color =
          opportunity > 0.08
            ? '#77edff'
            : p.squad === 'blue'
              ? '#20bfff'
              : p.squad === 'red'
                ? '#ff4d32'
                : p.team === 'offense'
                  ? '#20bfff'
                  : '#ff4d32'
        const height = Math.max(-5.5, Math.min(5.5, courtSurface(p.x, p.y, players, mode, kernel) * zScale))
        return (
          <group key={p.id} position={[p.x, p.y, height + 0.15]}>
            <mesh position={[0, 0, 1.25]} rotation={[Math.PI / 2, 0, 0]} castShadow>
              <capsuleGeometry args={[0.48, 1.25, 5, 12]} />
              <meshStandardMaterial
                color={color}
                emissive={opportunity > 0.08 ? '#20cfff' : '#000000'}
                emissiveIntensity={opportunity * 1.4}
                roughness={0.28}
                metalness={0.16}
              />
            </mesh>
            <mesh position={[0, 0, 2.48]} castShadow>
              <sphereGeometry args={[0.4, 16, 12]} />
              <meshStandardMaterial color="#c68d68" roughness={0.8} />
            </mesh>
            <mesh position={[0, 0, 0.04]}>
              <ringGeometry args={[0.72, 0.94, 36]} />
              <meshBasicMaterial color={color} transparent opacity={0.85} side={THREE.DoubleSide} />
            </mesh>
            {(p.opportunity ?? 0) > 0.08 && (
              <>
                <mesh position={[0, 0, 0.07]}>
                  <ringGeometry args={[1.04, 1.27, 48]} />
                  <meshBasicMaterial
                    color="#7beeff"
                    transparent
                    opacity={0.28 + opportunity * 0.68}
                    side={THREE.DoubleSide}
                  />
                </mesh>
                <pointLight
                  color="#53dfff"
                  intensity={1.2 + opportunity * 2.2}
                  distance={7}
                  decay={2}
                  position={[0, 0, 0.45]}
                />
              </>
            )}
            <pointLight color={color} intensity={1.8} distance={5} decay={2} position={[0, 0, 0.6]} />
            {profile && ratings && (showImages || showStats) ? (
              <Html center position={[0, 0, 4.05]} zIndexRange={[8, 0]} style={{ pointerEvents: 'none' }}>
                <div
                  className={`player-profile-marker ${profile.team.toLowerCase()} ${
                    opportunity > 0.08 ? 'open' : ''
                  }`}
                >
                  {showImages && (
                    <div className="player-portrait">
                      <span>{profile.shortName.slice(0, 2).toUpperCase()}</span>
                      <img
                        src={headshotUrl(profile)}
                        alt=""
                        onError={(event) => {
                          event.currentTarget.style.display = 'none'
                        }}
                      />
                    </div>
                  )}
                  {showStats && (
                    <div className="player-profile-copy">
                      <strong>{profile.shortName}</strong>
                      <small>
                        {profile.team === 'Lakers' ? 'LAL' : 'SAS'} · {profile.position}
                      </small>
                      <>
                        <span>
                          {profile.stats.points.toFixed(1)} PTS · {profile.stats.assists.toFixed(1)} AST
                        </span>
                        <span>
                          {profile.stats.rebounds.toFixed(1)} REB · {profile.stats.steals.toFixed(1)} STL ·{' '}
                          {profile.stats.blocks.toFixed(1)} BLK
                        </span>
                        <em>
                          O {ratings.offense.toFixed(2)}× · D {ratings.defense.toFixed(2)}×
                        </em>
                      </>
                    </div>
                  )}
                </div>
              </Html>
            ) : (
              <Text
                position={[0, 0, 3.25]}
                fontSize={0.62}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
                outlineWidth={0.05}
                outlineColor="#05070a"
              >
                {p.id.toUpperCase()}
              </Text>
            )}
          </group>
        )
      })}
    </group>
  )
}

export function CourtLines() {
  const { x0, x1, y0, y1 } = courtExtents()
  const border = useMemo(
    () =>
      [
        [x0, y0, 0.05],
        [x1, y0, 0.05],
        [x1, y1, 0.05],
        [x0, y1, 0.05],
        [x0, y0, 0.05],
      ] as [number, number, number][],
    [x0, x1, y0, y1],
  )
  const paint = useMemo(() => {
    const hw = 8
    const len = 19
    return [
      [-hw, y0, 0.06],
      [-hw, y0 + len, 0.06],
      [hw, y0 + len, 0.06],
      [hw, y0, 0.06],
    ] as [number, number, number][]
  }, [y0])

  return (
    <group>
      <Line points={border} color="#888888" lineWidth={1} />
      <Line points={paint} color="#555555" lineWidth={1} />
    </group>
  )
}

function Hoop({ far = false }: { far?: boolean }) {
  const y = far ? 90 : 4
  const facing = far ? Math.PI : 0
  return (
    <group position={[0, y, 0]} rotation={[0, 0, facing]}>
      <mesh position={[0, -1.2, 6]} castShadow>
        <boxGeometry args={[6, 0.18, 3.5]} />
        <meshPhysicalMaterial
          color="#dce8ef"
          transparent
          opacity={0.38}
          transmission={0.4}
          roughness={0.15}
        />
      </mesh>
      <Line
        points={[
          [-1.25, -1.05, 5.2],
          [1.25, -1.05, 5.2],
          [1.25, -1.05, 6.9],
          [-1.25, -1.05, 6.9],
          [-1.25, -1.05, 5.2],
        ]}
        color="#ffffff"
        lineWidth={2}
      />
      <mesh position={[0, 0, 5.1]} castShadow>
        <torusGeometry args={[0.75, 0.09, 10, 32]} />
        <meshStandardMaterial color="#ff5a1f" emissive="#8a1800" emissiveIntensity={0.7} />
      </mesh>
      <mesh position={[0, -2.0, 3.0]} rotation={[Math.PI / 2, 0, 0]} castShadow>
        <cylinderGeometry args={[0.14, 0.22, 6, 12]} />
        <meshStandardMaterial color="#343944" metalness={0.8} roughness={0.3} />
      </mesh>
      <mesh position={[0, -1.25, 0.2]} castShadow>
        <boxGeometry args={[3.5, 3.0, 0.4]} />
        <meshStandardMaterial color="#141820" metalness={0.5} roughness={0.5} />
      </mesh>
    </group>
  )
}

export function Arena() {
  const lightPods = [-22, -11, 0, 11, 22]
  return (
    <group>
      <mesh position={[0, 47, -7.2]} receiveShadow>
        <boxGeometry args={[54, 98, 2.0]} />
        <meshStandardMaterial color="#080b10" roughness={0.75} metalness={0.15} />
      </mesh>
      <mesh position={[0, 47, -8.35]} receiveShadow>
        <boxGeometry args={[76, 116, 0.5]} />
        <meshStandardMaterial color="#020305" roughness={1} />
      </mesh>
      <Hoop />
      <Hoop far />
      {lightPods.map((x) => (
        <pointLight
          key={x}
          position={[x, 47, 35]}
          color={Math.abs(x) < 1 ? '#a9d8ff' : '#ffe8c0'}
          intensity={55}
          distance={70}
          decay={2}
        />
      ))}
    </group>
  )
}

export function GameBall({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh castShadow>
        <sphereGeometry args={[0.48, 24, 18]} />
        <meshStandardMaterial color="#e86f18" roughness={0.72} />
      </mesh>
      <mesh rotation={[0, 0, Math.PI / 2]}>
        <torusGeometry args={[0.485, 0.018, 6, 32]} />
        <meshBasicMaterial color="#26150d" />
      </mesh>
      <pointLight color="#ff8a32" intensity={1.4} distance={4} />
    </group>
  )
}
