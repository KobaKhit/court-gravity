# Court Gravity

3Blue1Brown-style visualization of basketball players as gravity wells on the court plane.

Shared **NumPy field core** feeds:

- **Manim Community** explainer scenes (`manim_video/`)
- **Three.js + R3F + leva** interactive web toy (`web/`)
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
pip install manim   # optional, for video

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

Open the local Vite URL. Use leva controls for `threePct`, `defense`, `sigma`, `mode` (`net`/`offense`/`defense`), kernel toggle, animation, and marble.

### Manim

Use a dedicated Python 3.12 environment for Manim on Windows:

```bash
py -3.12 -m venv .venv-manim
.venv-manim\Scripts\python.exe -m pip install -e ".[video,dev,preview]"
.venv-manim\Scripts\manim.exe -ql \
  manim_video/full_explainer.py CourtGravityExplainer
```

Manim Community requires `moderngl` wheels (or MSVC build tools). On Python
versions without compatible wheels, use the matplotlib storyboard renderer:

```bash
python manim_video/render_matplotlib.py
# frames land in data/storyboard/
```

When Manim is available (Python 3.11/3.12 recommended):

```bash
manim -ql manim_video/scenes.py GravityCourtStatic
manim -ql manim_video/storyboard.py MassModulation
# Continuous educational first cut:
manim -ql manim_video/full_explainer.py CourtGravityExplainer
```

Use `-qk --renderer=opengl` for higher quality.

Without Manim or FFmpeg, render the animated GIF preview with the existing
NumPy/Matplotlib/Pillow environment:

```bash
python manim_video/render_explainer_preview.py
# data/storyboard/court_gravity_explainer_preview.gif

# Optional H.264 review file:
pip install -e ".[preview]"
python manim_video/render_explainer_preview.py \
  --mp4 data/storyboard/court_gravity_explainer_preview.mp4
```

## Ship

```bash
python scripts/ship.py
# or manually: generate_data → sync_web_assets → render_matplotlib → npm run build
```

Deploy `web/dist/` to any static host. Optional Blender bake: `blender --background --python blender/bake_heightmaps.py`.

## Layout

```
court-gravity/
  core/            # field, kde, trajectories, archetypes, court, export
  manim_video/     # storyboard scenes
  blender/         # bpy displacement bake
  web/             # vite + r3f + leva
  data/            # generated synthetic runs
  configs/         # court_config.json, palette.json
  scripts/         # sanity, parity, generate_data
  tests/
```

## Math (summary)

\[
I_i(x,y) = m_i \exp\bigl(-\tfrac12 r^\top \Sigma_i^{-1} r\bigr)
\]

\[
z(x,y) = -\sum_{i\in\mathrm{off}} I_i + \sum_{j\in\mathrm{def}} I_j
\]

Optional softened Newtonian kernel: \(\Phi = -Gm/\sqrt{r^2+\varepsilon^2}\).
