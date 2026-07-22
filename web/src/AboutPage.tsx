import { useEffect, useMemo, useRef, useState } from 'react'
import { gameStateAtTime, POSSESSION_SECONDS } from './gameSimulation'
import { getPlayerProfile, gravityRatings, headshotUrl, PROFILE_SEASON } from './playerProfiles'

const STEPS = [
  {
    label: 'Inputs',
    title: 'Stats become gravity',
    summary: 'Season production establishes every player’s baseline influence.',
  },
  {
    label: 'Kernel',
    title: 'Each player bends space',
    summary: 'A Gaussian turns player location, strength, and reach into a smooth field.',
  },
  {
    label: 'Net field',
    title: 'Pressure cancels opportunity',
    summary: 'Blue and red are compared locally so contested areas resolve toward neutral.',
  },
  {
    label: 'Spacing',
    title: 'Open looks must be real',
    summary: 'Defender distance helps only when teammates preserve usable floor balance.',
  },
  {
    label: 'Lifecycle',
    title: 'The field follows game state',
    summary: 'Inbound, transition, action, shot, and dead-ball envelopes prevent visual jumps.',
  },
  {
    label: 'Example',
    title: 'One possession, end to end',
    summary: 'The same production simulator powers this miniature live example.',
  },
]

export function AboutPage({ onBack }: { onBack: () => void }) {
  const [activeStep, setActiveStep] = useState(0)
  const [playing, setPlaying] = useState(true)
  const [sigma, setSigma] = useState(5)
  const [defenderDistance, setDefenderDistance] = useState(3.5)
  const [teammateDistance, setTeammateDistance] = useState(9)
  const [demoTime, setDemoTime] = useState(0)
  const [clock, setClock] = useState(0)
  const sectionRefs = useRef<(HTMLElement | null)[]>([])

  useEffect(() => {
    if (!playing) return
    let frame = 0
    let previous = performance.now()
    const animate = (now: number) => {
      const dt = Math.min(0.05, (now - previous) / 1000)
      previous = now
      setClock(now)
      setDemoTime((time) => (time + dt * 0.72) % POSSESSION_SECONDS)
      frame = requestAnimationFrame(animate)
    }
    frame = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frame)
  }, [playing])

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const mostVisible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0]
        if (mostVisible) setActiveStep(Number((mostVisible.target as HTMLElement).dataset.chapter ?? 0))
      },
      { root: document.querySelector('.about-shell'), threshold: [0.25, 0.45, 0.65] },
    )
    sectionRefs.current.forEach((section) => section && observer.observe(section))
    return () => observer.disconnect()
  }, [])

  const game = useMemo(() => gameStateAtTime(demoTime, 5), [demoTime])
  const pulse = 0.5 + Math.sin(clock / 620) * 0.5
  const coverageQuality = smoothstep(3.5, 7.5, defenderDistance)
  const floorBalance = smoothstep(5, 10, teammateDistance)
  const opportunity = coverageQuality * floorBalance

  return (
    <main className="about-shell">
      <header className="about-header">
        <button className="about-back" onClick={onBack}>
          <span>←</span> Back to court
        </button>
        <div className="about-brand">
          <span>COURT</span> GRAVITY
        </div>
        <div className="about-header-actions">
          <span className="about-season">{PROFILE_SEASON} MODEL</span>
          <button onClick={() => setPlaying((value) => !value)}>{playing ? 'Pause motion' : 'Play motion'}</button>
        </div>
      </header>

      <div className="about-scroll-layout">
        <aside className="about-scroll-rail" aria-label="Story progress">
          <div className="about-nav-caption">SCROLL TO EXPLORE</div>
          <div className="rail-progress">
            <span style={{ height: `${((activeStep + 1) / STEPS.length) * 100}%` }} />
          </div>
          {STEPS.map((item, index) => (
            <div key={item.label} className={index === activeStep ? 'active' : ''}>
              <i>{String(index + 1).padStart(2, '0')}</i>
              <span>
                <small>{item.label}</small>
                <strong>{item.title}</strong>
              </span>
            </div>
          ))}
        </aside>

        <div className="about-story">
          <div className="about-scroll-intro">
            <div className="about-kicker">AN INTERACTIVE MODEL EXPLAINER</div>
            <h1>From box score<br />to spatial advantage.</h1>
            <p>Scroll through the model one layer at a time. Adjust the inputs to see how the field responds.</p>
            <div className="scroll-cue"><i /> SCROLL</div>
          </div>

          {STEPS.map((item, index) => (
            <section
              key={item.label}
              ref={(node) => {
                sectionRefs.current[index] = node
              }}
              data-chapter={index}
              className={`about-chapter ${index === activeStep ? 'active' : ''}`}
            >
              <div className="chapter-heading">
                <div className="chapter-number">{String(index + 1).padStart(2, '0')}</div>
                <div className="about-copy">
                  <div className="about-kicker">
                    CHAPTER {index + 1} / {STEPS.length} · {item.label.toUpperCase()}
                  </div>
                  <h2>{item.title}</h2>
                  <p>{item.summary}</p>
                </div>
              </div>

              <div className="about-visual">
                {index === 0 && <StatsVisual />}
                {index === 1 && <KernelVisual sigma={sigma} pulse={pulse} />}
                {index === 2 && (
                  <CancellationVisual distance={defenderDistance} pulse={pulse} advantage={coverageQuality} />
                )}
                {index === 3 && (
                  <SpacingVisual
                    defenderDistance={defenderDistance}
                    teammateDistance={teammateDistance}
                    opportunity={opportunity}
                    pulse={pulse}
                  />
                )}
                {index === 4 && <LifecycleVisual game={game} />}
                {index === 5 && <PossessionVisual time={demoTime} />}
              </div>

              <div className="about-interaction">
                {index === 1 && (
                  <Control
                    label="Influence radius (σ)"
                    value={sigma}
                    min={2.5}
                    max={8}
                    step={0.1}
                    suffix=" ft"
                    onChange={setSigma}
                  />
                )}
                {index === 2 && (
                  <Control
                    label="Defender separation"
                    value={defenderDistance}
                    min={1}
                    max={10}
                    step={0.1}
                    suffix=" ft"
                    onChange={setDefenderDistance}
                  />
                )}
                {index === 3 && (
                  <>
                    <Control
                      label="Defender separation"
                      value={defenderDistance}
                      min={1}
                      max={10}
                      step={0.1}
                      suffix=" ft"
                      onChange={setDefenderDistance}
                    />
                    <Control
                      label="Nearest teammate"
                      value={teammateDistance}
                      min={2}
                      max={14}
                      step={0.1}
                      suffix=" ft"
                      onChange={setTeammateDistance}
                    />
                  </>
                )}
                {(index === 4 || index === 5) && (
                  <Control
                    label="Possession time"
                    value={demoTime}
                    min={0}
                    max={POSSESSION_SECONDS}
                    step={0.05}
                    suffix=" s"
                    onChange={setDemoTime}
                  />
                )}
              </div>

              <div className="about-insight">
                <span>EXECUTIVE READOUT</span>
                <p>{insightFor(index, sigma, defenderDistance, teammateDistance, opportunity, game.phase)}</p>
              </div>
            </section>
          ))}

          <section className="about-scroll-outro">
            <div className="about-kicker">MODEL TO MOMENT</div>
            <h2>Now watch the full system.</h2>
            <p>Return to the live court to explore every possession, angle, player, and field layer.</p>
            <button onClick={onBack}>Open live court <span>→</span></button>
          </section>
        </div>
      </div>
    </main>
  )
}

function StatsVisual() {
  const profiles = [getPlayerProfile('BPG'), getPlayerProfile('RC')].filter(Boolean)
  return (
    <div className="stats-visual">
      {profiles.map((profile) => {
        if (!profile) return null
        const ratings = gravityRatings(profile)
        return (
          <article key={profile.simulationId} className={`about-player-card ${profile.team.toLowerCase()}`}>
            <img src={headshotUrl(profile)} alt="" />
            <div>
              <small>{profile.team} · {profile.position}</small>
              <h3>{profile.name}</h3>
              <p>
                {profile.stats.points.toFixed(1)} PTS · {profile.stats.rebounds.toFixed(1)} REB ·{' '}
                {profile.stats.assists.toFixed(1)} AST
              </p>
              <div className="rating-row">
                <span>OFFENSE</span>
                <i>
                  <b style={{ width: `${(ratings.offense / 1.55) * 100}%` }} />
                </i>
                <strong>{ratings.offense.toFixed(2)}×</strong>
              </div>
              <div className="rating-row defense-rating">
                <span>DEFENSE</span>
                <i>
                  <b style={{ width: `${(ratings.defense / 1.55) * 100}%` }} />
                </i>
                <strong>{ratings.defense.toFixed(2)}×</strong>
              </div>
            </div>
          </article>
        )
      })}
      <div className="formula-card">
        <span>BASELINE RATINGS</span>
        <code>O = f(PTS, AST, REB, 3P%)</code>
        <code>D = f(STL, BLK, REB)</code>
        <p>Ratings establish mass and influence radius before game context is applied.</p>
      </div>
    </div>
  )
}

function KernelVisual({ sigma, pulse }: { sigma: number; pulse: number }) {
  const diameter = 86 + sigma * 34
  return (
    <div className="field-lab">
      <div
        className="kernel-field"
        style={{
          width: diameter,
          height: diameter,
          opacity: 0.76 + pulse * 0.12,
        }}
      />
      {[0.36, 0.58, 0.8].map((scale) => (
        <i
          key={scale}
          className="kernel-ring"
          style={{ width: diameter * scale, height: diameter * scale }}
        />
      ))}
      <div className="diagram-player offense-player">LD</div>
      <div className="formula-float">
        <code>
          I(x) = m · exp(−d² / 2σ²)
        </code>
        <span>σ = {sigma.toFixed(1)} ft</span>
      </div>
    </div>
  )
}

function CancellationVisual({
  distance,
  pulse,
  advantage,
}: {
  distance: number
  pulse: number
  advantage: number
}) {
  const separation = distance * 22
  return (
    <div className="field-lab cancellation-lab">
      <div
        className="weather-orb blue-orb"
        style={{ transform: `translateX(${-separation / 2}px) scale(${0.96 + pulse * 0.04})`, opacity: 0.2 + advantage * 0.72 }}
      />
      <div
        className="weather-orb red-orb"
        style={{ transform: `translateX(${separation / 2}px)`, opacity: 0.78 - advantage * 0.36 }}
      />
      <div className="diagram-player offense-player" style={{ transform: `translateX(${-separation / 2}px)` }}>
        O
      </div>
      <div className="diagram-player defense-player" style={{ transform: `translateX(${separation / 2}px)` }}>
        D
      </div>
      <div className={`advantage-status ${advantage > 0.56 ? 'open' : advantage < 0.18 ? 'contested' : ''}`}>
        {advantage > 0.56 ? 'OFFENSIVE ADVANTAGE' : advantage < 0.18 ? 'CANCELED / CONTESTED' : 'DEVELOPING'}
      </div>
      <div className="formula-float">
        <code>Z(x) = Σ Defense − Σ Offense</code>
        <span>{distance.toFixed(1)} ft separation</span>
      </div>
    </div>
  )
}

function SpacingVisual({
  defenderDistance,
  teammateDistance,
  opportunity,
  pulse,
}: {
  defenderDistance: number
  teammateDistance: number
  opportunity: number
  pulse: number
}) {
  return (
    <div className="field-lab spacing-lab">
      <div
        className="weather-orb blue-orb"
        style={{ opacity: 0.12 + opportunity * 0.82, transform: `scale(${0.92 + pulse * opportunity * 0.08})` }}
      />
      <div className="diagram-player offense-player">O</div>
      <div className="diagram-player defense-player" style={{ transform: `translateX(${defenderDistance * 19}px)` }}>
        D
      </div>
      <div className="diagram-player teammate-player" style={{ transform: `translateX(${-teammateDistance * 16}px)` }}>
        T
      </div>
      <div className="spacing-measure defender-measure" style={{ width: defenderDistance * 19 }}>
        {defenderDistance.toFixed(1)} ft
      </div>
      <div className="opportunity-meter">
        <span>OPPORTUNITY QUALITY</span>
        <strong>{Math.round(opportunity * 100)}</strong>
        <i>
          <b style={{ width: `${opportunity * 100}%` }} />
        </i>
      </div>
    </div>
  )
}

function LifecycleVisual({ game }: { game: ReturnType<typeof gameStateAtTime> }) {
  const phases = ['Inbound', 'Transition', 'Set', 'Action', 'Shot', 'DeadBall']
  return (
    <div className="lifecycle-visual">
      <div className="phase-track">
        {phases.map((phase) => (
          <div key={phase} className={game.phase === phase ? 'active' : ''}>
            <i />
            <span>{phase}</span>
          </div>
        ))}
      </div>
      <div className="envelope-chart">
        <div>
          <span>OFFENSIVE FIELD</span>
          <i>
            <b className="offense-bar" style={{ width: `${game.offenseIntensity * 100}%` }} />
          </i>
          <strong>{Math.round(game.offenseIntensity * 100)}%</strong>
        </div>
        <div>
          <span>DEFENSIVE FIELD</span>
          <i>
            <b className="defense-bar" style={{ width: `${game.defenseIntensity * 100}%` }} />
          </i>
          <strong>{Math.round(game.defenseIntensity * 100)}%</strong>
        </div>
      </div>
      <p className="lifecycle-note">
        During dead balls and the inbound hold, both envelopes return to zero. They rebuild only after the ball becomes
        live.
      </p>
    </div>
  )
}

function PossessionVisual({ time }: { time: number }) {
  const game = gameStateAtTime(time, 5)
  return (
    <div className="example-visual">
      <div className="example-score">
        <strong>{game.playName}</strong>
        <span>{game.phase}</span>
        <em>{game.shotClock == null ? '—' : game.shotClock.toFixed(1)} SHOT</em>
      </div>
      <svg viewBox="0 0 940 500" role="img" aria-label="Animated example possession">
        <rect x="1" y="1" width="938" height="498" rx="8" className="mini-floor" />
        <path d="M470 0V500 M0 170H190V330H0 M940 170H750V330H940" className="mini-lines" />
        <circle cx="470" cy="250" r="60" className="mini-lines" />
        <circle cx="40" cy="250" r="40" className="mini-lines" />
        <circle cx="900" cy="250" r="40" className="mini-lines" />
        {game.players.map((player) => {
          const x = player.y * 10
          const y = (25 - player.x) * 10
          const field = player.team === 'offense' ? game.offenseIntensity : game.defenseIntensity
          return (
            <g key={`field-${player.id}`}>
              <circle
                cx={x}
                cy={y}
                r={46 + (player.opportunity ?? 0) * 20}
                fill={player.team === 'offense' ? '#19d9ff' : '#ff3e27'}
                opacity={field * (0.08 + (player.opportunity ?? 0) * 0.2)}
              />
            </g>
          )
        })}
        {game.players.map((player) => {
          const x = player.y * 10
          const y = (25 - player.x) * 10
          const profile = getPlayerProfile(player.id)
          return (
            <g key={player.id} transform={`translate(${x} ${y})`}>
              <circle r="11" fill={player.squad === 'blue' ? '#fdb927' : '#c4ced4'} />
              <circle r="8" fill="#081019" stroke={player.team === 'offense' ? '#35dcff' : '#ff4933'} strokeWidth="3" />
              <text y="3.5">{profile?.shortName.slice(0, 2).toUpperCase() ?? player.id}</text>
            </g>
          )
        })}
        <circle cx={game.ball[1] * 10} cy={(25 - game.ball[0]) * 10} r="6" className="mini-ball" />
      </svg>
      <div className="example-readout">
        <span>OFFENSE {Math.round(game.offenseIntensity * 100)}%</span>
        <span>DEFENSE {Math.round(game.defenseIntensity * 100)}%</span>
        <span>{game.openPlayerId ? `${game.openPlayerId} OPEN · ${game.opportunitySeparation.toFixed(1)} FT` : 'NO OPEN LOOK'}</span>
      </div>
    </div>
  )
}

function Control({
  label,
  value,
  min,
  max,
  step,
  suffix,
  onChange,
}: {
  label: string
  value: number
  min: number
  max: number
  step: number
  suffix: string
  onChange: (value: number) => void
}) {
  return (
    <label className="about-control">
      <span>{label}</span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      <strong>
        {value.toFixed(1)}
        {suffix}
      </strong>
    </label>
  )
}

function insightFor(
  step: number,
  sigma: number,
  defenderDistance: number,
  teammateDistance: number,
  opportunity: number,
  phase: string,
) {
  if (step === 0) return 'The model explains why Dončić pulls the defense farther while Wembanyama changes more space defensively.'
  if (step === 1)
    return `At σ ${sigma.toFixed(1)}, influence is ${sigma > 6 ? 'broad and scheme-level' : sigma < 4 ? 'tight and matchup-specific' : 'balanced between matchup and help responsibilities'}.`
  if (step === 2)
    return defenderDistance < 3.5
      ? 'Close coverage nearly cancels the offensive field, leaving a neutral contested zone.'
      : 'As separation grows, local defensive influence falls and blue advantage becomes visible.'
  if (step === 3)
    return `Defender space and teammate spacing combine to a ${Math.round(opportunity * 100)}% opportunity signal; crowding at ${teammateDistance.toFixed(1)} ft can suppress an otherwise open look.`
  if (step === 4) return `${phase} is active. Field envelopes interpolate continuously so phase changes never pop or teleport.`
  return 'This example uses the production state machine, player ratings, spacing checks, and lifecycle envelopes—not a separate animation.'
}

function smoothstep(edge0: number, edge1: number, value: number) {
  const x = Math.max(0, Math.min(1, (value - edge0) / (edge1 - edge0)))
  return x * x * (3 - 2 * x)
}

