import { Suspense, useEffect, useMemo, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { ContactShadows } from '@react-three/drei'
import { Leva, useControls, button } from 'leva'
import { Arena, CourtMesh, GameBall, PlayerMarkers } from './CourtSurface'
import { Heatmap2D } from './Heatmap2D'
import { Marble } from './Marble'
import { CameraPreset, CameraRig } from './CameraRig'
import { MotionTrails } from './MotionTrails'
import { FieldMode, KernelType } from './fieldMath'
import { GAME_DURATION, POSSESSION_COUNT, POSSESSION_SECONDS, gameStateAtTime } from './gameSimulation'
import { getPlayerProfile, gravityRatings } from './playerProfiles'
import { AboutPage } from './AboutPage'
import { useMobileProfile } from './useMobileProfile'

export default function App() {
  const mobile = useMobileProfile()
  const [t, setT] = useState(0)
  const [marbleKey, setMarbleKey] = useState(0)
  const [isPlaying, setIsPlaying] = useState(true)
  const [playbackRate, setPlaybackRate] = useState<0.5 | 1>(1)
  const [cameraPreset, setCameraPreset] = useState<CameraPreset>('top')
  const [page, setPage] = useState<'court' | 'about'>(() =>
    typeof window !== 'undefined' && window.location.hash === '#about' ? 'about' : 'court',
  )
  const [showExplainer, setShowExplainer] = useState(false)
  const [mobileViewDefaulted, setMobileViewDefaulted] = useState(false)
  const [viewOverride, setViewOverride] = useState<'3d' | '2d' | 'both' | null>(null)

  const controls = useControls('Field', {
    defense: { value: 0.55, min: 0, max: 1, step: 0.01 },
    sigma: { value: 5, min: 2, max: 10, step: 0.1 },
    massScale: { value: 1.0, min: 0.3, max: 2.5, step: 0.05 },
    mode: { options: ['net', 'offense', 'defense'] as FieldMode[] },
    kernel: { options: ['gaussian', 'softened'] as KernelType[] },
    zScale: { value: 1.55, min: 0.15, max: 4.0, step: 0.05 },
    view: { options: ['3d', '2d', 'both'] as const },
    marble: false,
    resetMarble: button(() => setMarbleKey((k) => k + 1)),
  })
  const profileControls = useControls('Players · 2025–26', {
    showPlayerImages: true,
    showNamesAndStats: false,
    showLakers: true,
    showSpurs: true,
    lukaDoncic: true,
    austinReaves: true,
    lebronJames: true,
    deandreAyton: true,
    ruiHachimura: true,
    deaaronFox: true,
    stephonCastle: true,
    devinVassell: true,
    victorWembanyama: true,
    harrisonBarnes: true,
  })

  useEffect(() => {
    if (!mobile.isNarrow || mobileViewDefaulted) return
    setViewOverride('3d')
    setCameraPreset('portrait')
    setMobileViewDefaulted(true)
  }, [mobile.isNarrow, mobileViewDefaulted])

  useEffect(() => {
    if (!showExplainer) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setShowExplainer(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [showExplainer])

  useEffect(() => {
    const syncPage = () => setPage(window.location.hash === '#about' ? 'about' : 'court')
    window.addEventListener('hashchange', syncPage)
    window.addEventListener('popstate', syncPage)
    return () => {
      window.removeEventListener('hashchange', syncPage)
      window.removeEventListener('popstate', syncPage)
    }
  }, [])

  useEffect(() => {
    if (!isPlaying || page === 'about' || showExplainer) return
    let raf = 0
    let last = performance.now()
    const loop = (now: number) => {
      const dt = ((now - last) / 1000) * playbackRate
      last = now
      setT((prev) => {
        const next = prev + dt
        return next > GAME_DURATION ? 0 : next
      })
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(raf)
  }, [isPlaying, playbackRate, page, showExplainer])

  const game = useMemo(() => gameStateAtTime(t, controls.sigma), [t, controls.sigma])
  const players = useMemo(
    () =>
      game.players.map((p) => {
      let mass = p.mass * controls.massScale
      let sigma = controls.sigma
      const profile = getPlayerProfile(p.id)
      const ratings = profile ? gravityRatings(profile) : null
      if (p.team === 'offense') {
        mass *= 0.92 * game.offenseIntensity
        if (ratings) {
          mass *= ratings.offense
          sigma *= ratings.offenseRadius / 5
        }
        const spacingQuality = Math.max(0, Math.min(1, ((p.teammateSpacing ?? 8) - 3) / 5))
        // Two teammates occupying the same pocket do not create twice the
        // opportunity. Their combined field is smoothly de-emphasized until
        // they restore playable NBA spacing.
        mass *= 0.5 + spacingQuality * 0.5
      }
      if (p.team === 'offense' && (p.opportunity ?? 0) > 0) {
        // Open looks read as brighter, broader blue pressure systems.
        mass *= 1 + (p.opportunity ?? 0) * 0.48
        sigma += (p.opportunity ?? 0) * 0.65
      }
      if (p.team === 'defense') {
        mass *= (0.56 + controls.defense * 0.8) * game.defenseIntensity
        if (ratings) {
          mass *= ratings.defense
          sigma *= ratings.defenseRadius / 5
        }
      }
      return { ...p, mass, sigma }
    }),
    [
      game.players,
      game.offenseIntensity,
      game.defenseIntensity,
      controls.massScale,
      controls.sigma,
      controls.defense,
    ],
  )
  const visibleProfileIds = useMemo(() => {
    const enabled = new Set<string>()
    if (profileControls.showLakers) {
      if (profileControls.lukaDoncic) enabled.add('BPG')
      if (profileControls.austinReaves) enabled.add('BSG')
      if (profileControls.lebronJames) enabled.add('BSF')
      if (profileControls.deandreAyton) enabled.add('BC')
      if (profileControls.ruiHachimura) enabled.add('BPF')
    }
    if (profileControls.showSpurs) {
      if (profileControls.deaaronFox) enabled.add('RPG')
      if (profileControls.stephonCastle) enabled.add('RSG')
      if (profileControls.devinVassell) enabled.add('RSF')
      if (profileControls.victorWembanyama) enabled.add('RC')
      if (profileControls.harrisonBarnes) enabled.add('RPF')
    }
    return enabled
  }, [profileControls])

  if (page === 'about') {
    return (
      <AboutPage
        onBack={() => {
          window.location.hash = ''
          setPage('court')
        }}
      />
    )
  }

  // On mobile, avoid rendering both 3D + inset heatmap by default.
  const selectedView = (viewOverride ?? controls.view) as '3d' | '2d' | 'both'
  const effectiveView = mobile.isNarrow && selectedView === 'both' ? '3d' : selectedView
  const show3d = effectiveView === '3d' || effectiveView === 'both'
  const show2d = effectiveView === '2d' || effectiveView === 'both'
  const gameClock = game.shotClock == null ? '—' : Math.max(0, game.shotClock).toFixed(1)
  const phaseLabel = game.phase === 'DeadBall' ? 'Made · Dead Ball' : game.phase
  const meshSegments = mobile.isMobile ? 96 : 200
  const enableShadows = !mobile.isMobile && !mobile.reduceMotion
  const canvasDpr: [number, number] = mobile.isMobile ? [1, 1.15] : [1, 1.75]

  return (
    <main className={`app-shell ${mobile.isNarrow ? 'is-mobile' : ''}`}>
      {!mobile.isNarrow && <Leva collapsed oneLineLabels />}
      <div className="overlay-title">
        <h1>COURT <span>GRAVITY</span></h1>
        <p>See how every player bends space, pulls defenders, and creates the next open shot.</p>
      </div>
      <div className="scorebug">
        <div><span className="team-dot offense" />LAL <strong>{game.blueScore}</strong></div>
        <div><span className="team-dot defense" />SAS <strong>{game.redScore}</strong></div>
        <div className={`clock ${game.shotClock == null ? 'dead' : ''}`}><small>SHOT</small>{gameClock}</div>
      </div>
      <div className="possession-label">
        <span>POSSESSION {game.possession + 1}/6</span>
        <strong>{game.playName}</strong>
        <em className={game.phase === 'DeadBall' ? 'dead' : game.phase === 'Inbound' ? 'inbound' : ''}>
          {phaseLabel}
        </em>
        {game.openPlayerId && game.opportunitySeparation >= 5 && (
          <b className="opportunity">
            {game.shotValue === 3 ? 'OPEN 3PT' : 'OPEN ROLL'} · {game.openPlayerId} ·{' '}
            {game.opportunitySeparation.toFixed(1)} FT
          </b>
        )}
      </div>
      <div className="mobile-scorechip" aria-label="Score and possession">
        <strong>LAL {game.blueScore}</strong>
        <span>·</span>
        <strong>SAS {game.redScore}</strong>
        <em>{gameClock}</em>
        <small>
          P{game.possession + 1}/6 · {phaseLabel}
        </small>
      </div>
      <div className="camera-presets" aria-label="Camera angle">
        <button
          className={cameraPreset === 'top' || cameraPreset === 'portrait' ? 'active' : ''}
          onClick={() => setCameraPreset(mobile.isNarrow ? 'portrait' : 'top')}
        >
          Top
        </button>
        <button
          className={cameraPreset === 'sideline' ? 'active' : ''}
          onClick={() => setCameraPreset('sideline')}
        >
          Side
        </button>
      </div>
      <div className="overlay-actions">
        <button className="about-link explainer-link" onClick={() => setShowExplainer(true)}>
          Watch explainer <span>▶</span>
        </button>
        <button
          className="about-link"
          onClick={() => {
            window.location.hash = 'about'
            setPage('about')
          }}
        >
          How it works <span>→</span>
        </button>
      </div>
      {showExplainer && (
        <div
          className="explainer-modal"
          role="dialog"
          aria-modal="true"
          aria-label="Court Gravity explainer video"
          onClick={() => setShowExplainer(false)}
        >
          <div className="explainer-panel" onClick={(event) => event.stopPropagation()}>
            <div className="explainer-panel-header">
              <div>
                <div className="eyebrow">FOUR-MINUTE EXPLAINER</div>
                <strong>Court Gravity</strong>
              </div>
              <button type="button" onClick={() => setShowExplainer(false)} aria-label="Close explainer">
                Close
              </button>
            </div>
            <video
              className="explainer-video"
              src={`${import.meta.env.BASE_URL}videos/court_gravity_explainer.mp4`}
              controls
              autoPlay
              playsInline
            />
          </div>
        </div>
      )}
      <div className="playback-controls">
        <button onClick={() => setIsPlaying((playing) => !playing)}>{isPlaying ? 'Pause' : 'Play'}</button>
        <button onClick={() => setPlaybackRate((rate) => (rate === 1 ? 0.5 : 1))}>{playbackRate}×</button>
        <div className="possession-progress">
          <i style={{ width: `${game.localProgress * 100}%` }} />
        </div>
        <button
          onClick={() => {
            const next = (game.possession + 1) % POSSESSION_COUNT
            setT(next * POSSESSION_SECONDS)
          }}
        >
          Next
        </button>
      </div>
      <div className="legend">
        <span><i className="swatch offense" /> Offensive advantage</span>
        <span><i className="swatch neutral" /> Contested / canceled</span>
        <span><i className="swatch defense" /> Defensive advantage</span>
      </div>
      <div className="disclaimer">
        Gravity ratings derived from 2025–26 regular-season production.
        <a className="site-credit" href="https://kobakhit.com/" target="_blank" rel="noreferrer">
          made by kobakhit
        </a>
      </div>

      {show2d && (
        <Heatmap2D
          players={players}
          mode={controls.mode as FieldMode}
          kernel={controls.kernel as KernelType}
          expanded={!show3d}
          mobile={mobile.isMobile}
        />
      )}

      {show3d && (
        <Canvas
          shadows={enableShadows}
          dpr={canvasDpr}
          gl={{ antialias: !mobile.isMobile, toneMappingExposure: 1.15 }}
          camera={{
            position: mobile.isNarrow ? [0, 47, 78] : [0, 47, 108],
            up: [-1, 0, 0],
            fov: mobile.isNarrow ? 48 : 42,
            near: 0.1,
            far: 500,
          }}
          style={{ position: 'absolute', inset: 0, touchAction: 'none' }}
        >
          <color attach="background" args={['#030509']} />
          <fog attach="fog" args={['#030509', 105, 190]} />
          <ambientLight intensity={mobile.isMobile ? 0.34 : 0.26} />
          <directionalLight
            position={[-18, -8, 35]}
            intensity={mobile.isMobile ? 1.7 : 2.2}
            color="#d9edff"
            castShadow={enableShadows}
          />
          <Suspense fallback={null}>
            <Arena />
            <CourtMesh
              players={players}
              mode={controls.mode as FieldMode}
              kernel={controls.kernel as KernelType}
              zScale={controls.zScale}
              segments={meshSegments}
            />
            <MotionTrails
              time={t}
              sigma={controls.sigma}
              possession={game.possession}
              phase={game.phase}
              phaseProgress={game.phaseProgress}
            />
            <PlayerMarkers
              players={players}
              mode={controls.mode as FieldMode}
              kernel={controls.kernel as KernelType}
              zScale={controls.zScale}
              visibleProfileIds={visibleProfileIds}
              showImages={profileControls.showPlayerImages}
              showStats={profileControls.showNamesAndStats && !mobile.isNarrow}
            />
            <GameBall position={game.ball} />
            <Marble
              players={players}
              mode={controls.mode as FieldMode}
              enabled={controls.marble}
              resetKey={marbleKey}
            />
            {enableShadows && (
              <ContactShadows
                position={[0, 47, -6.1]}
                opacity={0.28}
                scale={108}
                blur={2.4}
                far={14}
                color="#000000"
              />
            )}
          </Suspense>
          <CameraRig preset={cameraPreset} mobile={mobile.isMobile} />
        </Canvas>
      )}

    </main>
  )
}
