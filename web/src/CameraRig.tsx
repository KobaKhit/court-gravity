import { useEffect, useMemo, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'

export type CameraPreset = 'top' | 'sideline' | 'portrait'

const PRESETS: Record<CameraPreset, { position: THREE.Vector3; target: THREE.Vector3; up: THREE.Vector3 }> = {
  top: {
    position: new THREE.Vector3(0, 47, 108),
    target: new THREE.Vector3(0, 47, 0),
    // Screen-up points toward the near sideline, putting the 94-foot axis
    // left-to-right like a landscape weather/radar map.
    up: new THREE.Vector3(-1, 0, 0),
  },
  sideline: {
    position: new THREE.Vector3(115, 47, 48),
    target: new THREE.Vector3(0, 47, 2),
    up: new THREE.Vector3(0, 0, 1),
  },
  portrait: {
    // Top-down with the court length vertical on a phone screen.
    position: new THREE.Vector3(0, 47, 102),
    target: new THREE.Vector3(0, 47, 0),
    up: new THREE.Vector3(0, 1, 0),
  },
}

export function CameraRig({
  preset,
  mobile = false,
}: {
  preset: CameraPreset
  mobile?: boolean
}) {
  const { camera } = useThree()
  const controls = useRef<OrbitControlsImpl>(null)
  const transitioning = useRef(true)
  const destination = useMemo(() => PRESETS[preset], [preset])

  useEffect(() => {
    transitioning.current = true
  }, [camera, preset])

  useFrame((_, dt) => {
    if (!controls.current) return
    if (mobile) {
      // Keep the locked mobile camera glued to the portrait framing.
      camera.position.copy(destination.position)
      camera.up.copy(destination.up)
      controls.current.target.copy(destination.target)
      camera.lookAt(controls.current.target)
      controls.current.update()
      transitioning.current = false
      return
    }
    if (!transitioning.current) return
    const alpha = 1 - Math.exp(-dt * 4.2)
    camera.position.lerp(destination.position, alpha)
    camera.up.lerp(destination.up, alpha).normalize()
    controls.current.target.lerp(destination.target, alpha)
    camera.lookAt(controls.current.target)
    controls.current.update()

    if (
      camera.position.distanceTo(destination.position) < 0.08 &&
      controls.current.target.distanceTo(destination.target) < 0.04
    ) {
      camera.position.copy(destination.position)
      camera.up.copy(destination.up)
      controls.current.target.copy(destination.target)
      transitioning.current = false
    }
  })

  return (
    <OrbitControls
      ref={controls}
      target={[0, 47, 0]}
      enableDamping={!mobile}
      dampingFactor={0.055}
      enableRotate={!mobile}
      enablePan={!mobile}
      enableZoom={!mobile}
      minDistance={mobile ? 90 : 30}
      maxDistance={mobile ? 120 : 240}
      minPolarAngle={Math.PI * 0.04}
      maxPolarAngle={Math.PI * 0.48}
      screenSpacePanning={false}
      touches={
        mobile
          ? undefined
          : {
              ONE: THREE.TOUCH.ROTATE,
              TWO: THREE.TOUCH.DOLLY_PAN,
            }
      }
      onStart={() => {
        if (!mobile) transitioning.current = false
      }}
    />
  )
}
