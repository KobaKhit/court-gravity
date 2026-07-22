# Court Gravity

3Blue1Brown-style visualization of basketball players as gravity wells on the court plane.

[![Court Gravity preview](docs/court-gravity-preview.gif)](https://court-gravity.onrender.com)

**Live web toy:** [court-gravity.onrender.com](https://court-gravity.onrender.com)  
**Repo:** [github.com/KobaKhit/court-gravity](https://github.com/KobaKhit/court-gravity)

Shared **NumPy field core** feeds:

- **Manim Community** explainer (`manim_video/`)
- **Three.js + R3F + leva** interactive web toy (`web/`)
- Timed **Edge TTS narration** aligned to Manim section windows
- Optional **Blender** displacement bake (`blender/`)

Offense digs attractive wells (negative \(z\)); defense raises repulsive ridges (positive \(z\)).

> Pedagogical model inspired by Fernández & Bornn pitch control and NBA “Gravity” framing — **not** a reproduction of the proprietary NBA Gravity metric.

## Quick start

### Python core

```bash
cd court-gravity
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -e ".[dev]"

python scripts/sanity_plot.py
python scripts/parity_check.py
python scripts/generate_data.py
pytest
```

### Web

```bash
cd web
npm install
npm run dev
```

Open the local Vite URL. Use leva controls for `threePct`, `defense`, `sigma`, `mode` (`net` / `offense` / `defense`), kernel toggle, animation, and marble.

### Manim explainer

Manim Community needs compatible `moderngl` wheels (Python 3.11/3.12 recommended on Windows):

```bash
py -3.12 -m venv .venv-manim
.venv-manim\Scripts\python.exe -m pip install -e ".[video,dev,preview]"
.venv-manim\Scripts\manim.exe -ql manim_video/full_explainer.py CourtGravityExplainer
```

Other scenes:

```bash
manim -ql manim_video/scenes.py GravityCourtStatic
manim -ql manim_video/storyboard.py MassModulation
```

Use `-qk --renderer=opengl` for higher quality.

Without Manim, use the matplotlib / Pillow preview path:

```bash
python manim_video/render_matplotlib.py
# frames → data/storyboard/

pip install -e ".[preview]"
python manim_video/render_explainer_preview.py
# GIF → data/storyboard/court_gravity_explainer_preview.gif

python manim_video/render_explainer_preview.py \
  --mp4 data/storyboard/court_gravity_explainer_preview.mp4
```

### Narration (timed VO)

The long-form essay in `manim_video/NARRATION.md` is denser than the ~4-minute draft. Production voiceover uses condensed `spoken` lines in `manim_video/narration_cues.json`, timed to Manim section windows from `full_explainer.py`.

```bash
pip install -e ".[narration]"
python scripts/build_narration.py analyze      # word budgets vs section windows
python scripts/build_narration.py synthesize # Edge TTS (Andrew, -5%) → wavs
python scripts/build_narration.py mux        # stitch + mux onto manim draft
# or:
python scripts/build_narration.py all
```

Default Edge voice is `en-US-AndrewNeural` at `-5%`. Alternatives: `--voice en-US-BrianNeural` or `--voice en-US-ChristopherNeural`.

**ElevenLabs (best quality)** — requires CLI + API key:

```bash
# one-time: elevenlabs config init --api-key sk_...
python scripts/build_narration.py all --engine elevenlabs --voice Daniel
# calmer US options: --voice Adam   or   --voice George
```

Outputs (gitignored):

- `data/storyboard/narration/court_gravity_narration.wav`
- `data/storyboard/narration/court_gravity_with_narration.mp4`

Optional OpenAI voices:

```bash
set OPENAI_API_KEY=...
python scripts/build_narration.py synthesize --engine openai --voice verse
```

## Ship / deploy

```bash
python scripts/ship.py
# or: generate_data → sync_web_assets → render_matplotlib → npm run build
```

Static web deploy is configured for Render (`render.yaml`):

- Root directory: `web`
- Build: `npm install && npm run build`
- Publish: `dist`
- Auto-deploys on push to `master`

Optional Blender bake: `blender --background --python blender/bake_heightmaps.py`.

## Layout

```
court-gravity/
  core/                 # field, kde, trajectories, archetypes, court, export
  manim_video/          # explainer scenes + NARRATION.md + narration_cues.json
  blender/              # bpy displacement bake
  web/                  # vite + r3f + leva
  data/                 # storyboard frames, drafts, generated assets
  configs/              # court_config.json, palette.json
  scripts/              # sanity, parity, generate_data, build_narration, ship
  tests/
  render.yaml           # Render static-site blueprint
```

## Math (summary)

\[
I_i(x,y) = m_i \exp\bigl(-\tfrac12 r^\top \Sigma_i^{-1} r\bigr)
\]

\[
z(x,y) = -\sum_{i\in\mathrm{off}} I_i + \sum_{j\in\mathrm{def}} I_j
\]

Optional softened Newtonian kernel: \(\Phi = -Gm/\sqrt{r^2+\varepsilon^2}\).
