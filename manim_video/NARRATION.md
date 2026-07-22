# Court Gravity — four-minute narration

Target length: approximately four minutes at 140–150 words per minute. Read
calmly and leave the marked visual transformations room to finish. Section
names match `full_explainer.py`.

## Timed VO (use this for production)

The essay below is the long-form script. It is denser than the ~245s Manim
draft, so production voiceover uses the condensed `spoken` lines in
[`narration_cues.json`](narration_cues.json) (section start/end times derived
from `full_explainer.py`, coda padded to the rendered draft).

```bash
pip install -e ".[narration]"
python scripts/build_narration.py analyze      # word budgets vs windows
# Prefer reusing expensive source mp3 clips:
python scripts/build_narration.py synthesize --reuse-clips
python scripts/build_narration.py mux        # stitch + mux onto draft mp4
# or: python scripts/build_narration.py all --reuse-clips
```

Optional OpenAI voices: `python scripts/build_narration.py synthesize --engine openai --voice verse`

Output lands in `data/storyboard/narration/` (gitignored).

## Cold open

Most basketball analysis treats the court as flat.

But to a defense, it is not.

Every offensive player pulls attention toward a different part of the floor.
Some stretch the defense beyond the three-point line. Some compress it toward
the rim. Some make help arrive half a second earlier simply because the cost
of being late is so high.

Defenders reshape the same space in the opposite direction. They remove angles,
discourage passes, and close opportunities before the box score ever records
them.

What if we could see that invisible geometry?

## 01 — The kernel

Begin with one offensive player.

We represent his influence with a smooth Gaussian field. His location sets the
center of the field. His strength determines its depth. Sigma controls how far
that influence reaches.

Close to the player, the value is strongest. Move away, and it falls smoothly
rather than ending at an arbitrary boundary.

The blue well is not shot probability by itself, and it is not claiming that
the player physically bends the floor. It represents offensive pressure:
space the defense must account for.

That distinction matters. Gravity is valuable because of the decisions it
forces, including the decisions that never appear in a traditional stat line.

## 02 — Strength and reach

Two players can stand in the same location and bend the court differently.

Increase mass and the well becomes deeper. In basketball language, ignoring
that player becomes more expensive.

Increase sigma and the field becomes wider. The player now affects help
defenders who are farther away.

Production, efficiency, shooting, and playmaking establish the strength of the
field. Role and range help establish its radius.

A high-gravity creator does not only occupy his own defender. He changes the
shape of the entire help scheme.

## 03 — Two views

This surface and the top-down heatmap are not different measurements.

They are two views of the same function.

In the angled view, height makes the topology intuitive: valleys represent
offensive pull, ridges represent defensive pressure.

Rotate overhead and equal-height contours become the familiar weather-map
bands. The two-dimensional view is better for locating space. The
three-dimensional view is better for explaining why that space exists.

Moving between them lets an audience preserve the same mental model.

## 04 — Player ratings

The shape begins with a player profile.

For Luka Dončić, scoring volume, efficiency, playmaking, and rebounding create
a high offensive baseline with a broad area of influence.

For Victor Wembanyama, rim protection, blocks, mobility, and defensive impact
produce an unusually strong defensive field.

These ratings do not decide the possession by themselves. They establish the
baseline.

The live field then combines that baseline with role, location, movement,
teammate spacing, defender distance, and the current phase of play.

In other words: who the player is matters, but where everyone is right now
matters just as much.

## 05 — Defensive cancellation

Defense contributes an opposing field.

Blue offensive wells and red defensive ridges are compared at every point on
the floor.

When a defender is close, balanced, and positioned between the attacker and
the scoring area, the two influences cancel. The surface returns toward
neutral. A viewer should immediately read that area as contested.

Now move the defender away.

The red contribution weakens locally, and the offensive basin gradually
reappears.

There is no arbitrary open-or-closed switch. Opportunity changes continuously
with separation, angle, and defensive quality.

## 06 — Superposition

One matchup is useful for understanding the idea, but basketball is never one
matchup.

First, add the five offensive fields. Each player contributes a different well
based on his role and position.

Then isolate the five defensive fields. Help responsibilities create a
connected system of ridges rather than five independent circles.

Finally, superpose both layers.

The result is one net surface describing which side owns each region of the
court at this instant.

That surface can reveal a valuable pocket even when no single defender has
made an obvious mistake.

## 07 — Spacing

Defender separation alone is not enough.

If two offensive players occupy the same pocket, they do not create twice the
value. Their fields overlap, the defense can guard two threats with one
position, and the usable floor shrinks.

Move the teammate to the opposite side. The defense must now cover more width,
the floor regains balance, and the original player’s gravity becomes useful.

The opportunity signal becomes strongest when the defender is late and the
other four players preserve playable spacing.

That is the bright blue basin we are looking for: not merely an unguarded
player, but a sustainable offensive advantage.

## 08 — Game state

The field must also follow the state of the game.

After a made basket, the topology disappears because there is no live
offensive pressure yet.

During the inbound, the field begins at zero. It then rebuilds through
transition, the set, and the action.

The interpolation is continuous, so the visualization never pops from one
shape to another.

This keeps the model faithful to when pressure actually exists and prevents a
dead-ball alignment from being mistaken for a live opportunity.

## 09 — Live possession

Now watch the geometry instead of only the ball.

The ball handler turns the corner and drives. Defenders compress toward the
paint. The strong-side ridge becomes crowded while the weak-side defender
inherits two responsibilities.

The shooter stays spaced. His defender takes one more step toward the drive.
The blue basin begins to form before the pass is thrown.

The kickout does not create the opening at the last moment.

It reveals space that the possession had already shaped.

That is the key analytical idea: opportunity is often the accumulated result
of several movements, not a single final action.

## 10 — Counterfactual

Because the model is continuous, we can ask a more useful question.

What if the defender had rotated sooner?

Keep the other nine players fixed and move only that defender. The red ridge
now reaches the shooter in time. The blue basin flattens, and the open look
disappears.

Restore the observed rotation and the opportunity returns.

This counterfactual view turns the visualization from a replay graphic into a
teaching tool. Coaches can compare responsibilities. Analysts can explain
which movement created the advantage. Executives can see the result without
decoding a spreadsheet.

## Coda

The box score records what happened.

Court Gravity helps explain why space opened, which player created it, and what
the defense could have changed.

This is a pedagogical influence model, not the proprietary NBA Gravity metric.
